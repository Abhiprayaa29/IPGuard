"""Backend unit and integration tests for M5 Blockchain Batch Anchoring."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
import uuid

from eth_account import Account
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, event, update
from sqlalchemy.orm import sessionmaker
from web3.exceptions import ContractLogicError, TimeExhausted, TransactionNotFound

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.audit import AuditEvent
from app.models.auth import Account as AccountModel, AuthSession, Device
from app.models.blockchain import AuditBlockchainAnchor
from app.services.audit_chain import append_audit_event
from app.services.blockchain import (
    anchor_audit_batch,
    get_blockchain_overview,
    verify_blockchain_anchor,
)


@pytest.fixture
def m5_env(tmp_path: Path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'm5-anchor-test.sqlite'}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    acct = Account.create("ipguard-m5-test-ephemeral-signer")
    contract_addr = "0x5FbDB2315678afecb367f032d93F642f64180aa3"

    settings = Settings(
        app_env="test",
        database_url=f"sqlite:///{tmp_path / 'm5-anchor-test.sqlite'}",
        blockchain_network="anvil",
        blockchain_rpc_url="http://127.0.0.1:8545",
        blockchain_chain_id=31337,
        blockchain_contract_address=contract_addr,
        blockchain_signer_private_key=acct.key.hex(),
        blockchain_receipt_timeout_seconds=10,
    )

    device_id = "ipguard-dev-m5-test-001"
    session_token = "a" * 64
    with factory() as db:
        with db.begin():
            db.add(AccountModel(account_id="ipguard-primary", display_name="Test Owner"))
            dev = Device(
                device_id=device_id,
                account_id="ipguard-primary",
                device_name="Test Phone",
                model="SM-A546E",
                android_version="16",
                public_key_x509="dGVzdA==",
                public_key_fingerprint="0" * 64,
                status="ACTIVE",
            )
            db.add(dev)
            db.flush()
            db.add(
                AuthSession(
                    session_token=session_token,
                    challenge_nonce="b" * 64,
                    account_id="ipguard-primary",
                    device_id=dev.id,
                    status="APPROVED",
                    client_origin="http://localhost:5173",
                    expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
                )
            )
            for i in range(3):
                append_audit_event(
                    db,
                    chain_id=device_id,
                    actor_type="DEVICE",
                    actor_device_id=device_id,
                    event_type="ASSET_UPLOADED",
                    resource_type="asset",
                    resource_id=f"asset-{i}",
                    result="SUCCESS",
                    payload={"ordinal": i},
                )

    def _override_db():
        with factory() as s:
            yield s

    def _ensure_sqlite_utc(target, _ctx):
        if target.expires_at and target.expires_at.tzinfo is None:
            target.expires_at = target.expires_at.replace(tzinfo=timezone.utc)

    event.listen(AuthSession, "load", _ensure_sqlite_utc)
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        yield factory, settings, device_id, session_token, acct.address, contract_addr
    finally:
        event.remove(AuthSession, "load", _ensure_sqlite_utc)
        app.dependency_overrides.clear()
        engine.dispose()


class _FakeCall:
    def __init__(self, value=None, exc: Exception | None = None):
        self._value = value
        self._exc = exc

    def call(self):
        if self._exc:
            raise self._exc
        return self._value

    def estimate_gas(self, _tx):
        return 120_000

    def build_transaction(self, params):
        return {
            "to": "0x5FbDB2315678afecb367f032d93F642f64180aa3",
            "value": 0,
            "data": "0x",
            "nonce": params["nonce"],
            "gas": params["gas"],
            "gasPrice": 1_000_000_000,
            "chainId": params["chainId"],
        }


class _FakeWeb3:
    def __init__(
        self,
        signer_address: str,
        *,
        connected: bool = True,
        onchain_signer: str | None = None,
        receipt_status: int = 1,
        verify_match: bool = True,
        send_exc: Exception | None = None,
        receipt_exc: Exception | None = None,
        receipt_missing: bool = False,
        block_num: int = 42,
    ):
        self._connected = connected
        self._onchain_signer = onchain_signer or signer_address
        self._receipt_status = receipt_status
        self._verify_match = verify_match
        self._send_exc = send_exc
        self._receipt_exc = receipt_exc
        self._receipt_missing = receipt_missing
        self._block_num = block_num
        self._tx_hash = bytes.fromhex("ab" * 32)
        self.eth = self._Eth(self)

    def is_connected(self):
        return self._connected

    def to_wei(self, val, _unit):
        return val * 1_000_000_000

    class _Eth:
        def __init__(self, outer):
            self._o = outer
            self.chain_id = 31337
            self.gas_price = 1_000_000_000
            self.account = Account

        def get_transaction_count(self, _addr, _block="latest"):
            return 0

        def get_block(self, _ref):
            return {"baseFeePerGas": 1_000_000_000, "timestamp": 1794390000}

        def send_raw_transaction(self, _raw):
            if self._o._send_exc:
                raise self._o._send_exc
            return self._o._tx_hash

        def wait_for_transaction_receipt(self, _tx_hash, timeout=10):
            if self._o._receipt_exc:
                raise self._o._receipt_exc
            return {"status": self._o._receipt_status, "blockNumber": self._o._block_num}

        def get_transaction_receipt(self, _tx_hash):
            if self._o._receipt_missing:
                raise TransactionNotFound("not found")
            return {"status": self._o._receipt_status, "blockNumber": self._o._block_num}

        def contract(self, address, abi):  # noqa: ARG002
            return self._Contract(self._o)

        class _Contract:
            def __init__(self, outer):
                self._o = outer
                self.functions = self

            def authorizedSigner(self):
                return _FakeCall(self._o._onchain_signer)

            def anchorBatch(self, *_args):
                return _FakeCall()

            def verifyBatch(self, *_args):
                return _FakeCall(self._o._verify_match)


def test_anchor_and_verify_happy_path_and_duplicate_prevented(m5_env):
    factory, settings, device_id, _, signer_addr, _ = m5_env
    fake_w3 = _FakeWeb3(signer_addr)

    with factory() as db:
        device = db.scalar(select_dev := Device.__table__.select().where(Device.device_id == device_id))
        dev_obj = db.query(Device).filter_by(device_id=device_id).one()

        anchor = anchor_audit_batch(
            db,
            dev_obj,
            settings=settings,
            web3_factory=lambda _rpc: fake_w3,
        )
        assert anchor.status == "CONFIRMED"
        assert anchor.from_sequence == 1
        assert anchor.to_sequence == 3
        assert anchor.event_count == 3
        assert anchor.block_number == 42
        assert anchor.explorer_url is None  # Anvil local must NEVER emit fake explorer link

        verified = verify_blockchain_anchor(
            db,
            dev_obj,
            uuid.UUID(anchor.id),
            settings=settings,
            web3_factory=lambda _rpc: fake_w3,
        )
        assert verified.verified is True
        assert verified.checks.onchain_contract_match is True
        assert verified.checks.local_merkle_recomputed_match is True

        # Second call with no new events is rejected cleanly
        with pytest.raises(AppError) as no_new:
            anchor_audit_batch(db, dev_obj, settings=settings, web3_factory=lambda _rpc: fake_w3)
        assert no_new.value.code == "no_unanchored_events"


def test_corrupted_audit_chain_rejected_before_blockchain(m5_env):
    factory, settings, device_id, _, signer_addr, _ = m5_env
    fake_w3 = _FakeWeb3(signer_addr)

    with factory() as db:
        db.execute(
            update(AuditEvent)
            .where(AuditEvent.chain_id == device_id, AuditEvent.sequence == 2)
            .values(event_hash="e" * 64)
        )
        db.commit()
        dev_obj = db.query(Device).filter_by(device_id=device_id).one()

        with pytest.raises(AppError) as err:
            anchor_audit_batch(db, dev_obj, settings=settings, web3_factory=lambda _rpc: fake_w3)
        assert err.value.code == "audit_chain_invalid"


def test_rpc_timeout_reconciles_without_duplicate_tx_and_detects_mismatch(m5_env):
    factory, settings, device_id, _, signer_addr, _ = m5_env
    timeout_w3 = _FakeWeb3(signer_addr, receipt_exc=TimeExhausted("timeout"))

    with factory() as db:
        dev_obj = db.query(Device).filter_by(device_id=device_id).one()
        submitted = anchor_audit_batch(
            db,
            dev_obj,
            settings=settings,
            web3_factory=lambda _rpc: timeout_w3,
        )
        assert submitted.status == "SUBMITTED"
        assert submitted.tx_hash is not None

        # Concurrent/second request cannot submit duplicate tx while SUBMITTED is in-flight
        with pytest.raises(AppError) as in_flight:
            anchor_audit_batch(db, dev_obj, settings=settings, web3_factory=lambda _rpc: timeout_w3)
        assert in_flight.value.code == "anchor_batch_in_flight"

        # Mismatch on contract fails verification cleanly
        mismatch_w3 = _FakeWeb3(signer_addr, verify_match=False)
        res_bad = verify_blockchain_anchor(
            db,
            dev_obj,
            uuid.UUID(submitted.id),
            settings=settings,
            web3_factory=lambda _rpc: mismatch_w3,
        )
        assert res_bad.verified is False
        assert res_bad.checks.onchain_contract_match is False

        # Reconcile when mined & verified
        good_w3 = _FakeWeb3(signer_addr, verify_match=True)
        res_ok = verify_blockchain_anchor(
            db,
            dev_obj,
            uuid.UUID(submitted.id),
            settings=settings,
            web3_factory=lambda _rpc: good_w3,
        )
        assert res_ok.verified is True
        assert res_ok.status == "CONFIRMED"


def test_rpc_unavailable_and_tx_reverted_states(m5_env):
    factory, settings, device_id, _, signer_addr, _ = m5_env

    with factory() as db:
        dev_obj = db.query(Device).filter_by(device_id=device_id).one()

        down_w3 = _FakeWeb3(signer_addr, connected=False)
        with pytest.raises(AppError) as down_err:
            anchor_audit_batch(db, dev_obj, settings=settings, web3_factory=lambda _rpc: down_w3)
        assert down_err.value.code == "blockchain_submission_failed"

        # Previous FAILED attempt can be retried cleanly; test reverted receipt
        revert_w3 = _FakeWeb3(signer_addr, receipt_status=0)
        with pytest.raises(AppError) as rev_err:
            anchor_audit_batch(db, dev_obj, settings=settings, web3_factory=lambda _rpc: revert_w3)
        assert rev_err.value.code == "blockchain_tx_reverted"


def test_api_endpoints_require_hardware_auth_and_redact_secrets(m5_env):
    _, settings, device_id, session_token, signer_addr, _ = m5_env
    client = TestClient(app)

    unauth = client.get("/api/v1/blockchain/anchors")
    assert unauth.status_code == 401

    resp = client.get(
        "/api/v1/blockchain/anchors",
        headers={"Authorization": f"Bearer {session_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["network"] == "anvil"
    assert body["network_label"] == "LOCAL DEVELOPMENT NETWORK"
    assert body["signer_address"] == signer_addr
    assert settings.blockchain_signer_private_key not in resp.text
    assert body["audit_chain_id"] == device_id
    assert body["audit_chain_valid"] is True
    assert body["pending_events"] == 3
