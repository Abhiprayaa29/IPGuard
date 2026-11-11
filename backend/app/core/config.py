import base64
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
# Exactly 32 bytes (256 bits) deterministic keys for local development/test environments
DEV_DEFAULT_NOTES_KEY = b"IPGuardDevMasterKey32BytesLong!!"
DEV_DEFAULT_ASSET_VAULT_KEY = b"IPGuardAssetVaultDevKey32Bytes!!"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "IPGuard"
    app_version: str = "1.0.0"
    app_env: Literal["development", "test", "production"] = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = Field(min_length=1)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    trusted_origins: str | None = None
    dev_admin_key: str = "ipguard-dev-admin-secret-key"
    account_recovery_key: str | None = Field(
        default="ipguard-dev-recovery-secret-key",
        description="Out-of-band account recovery authorization key for restoring REVOKED devices.",
    )
    account_recovery_key_sha256: str | None = Field(
        default=None,
        description="Optional SHA-256 hex digest of the account recovery key so plaintext does not need to reside in env.",
    )
    notes_master_key_b64: str | None = Field(
        default=None,
        description="Base64 encoded 32-byte master key for Secure Notes encryption.",
    )
    asset_vault_master_key_b64: str | None = Field(
        default=None,
        description="Base64 encoded 32-byte master key for Asset Vault XChaCha20-Poly1305 encryption.",
    )
    asset_vault_storage_dir: str | None = Field(
        default=None,
        description="Path to directory for encrypted asset binaries. Defaults to backend/storage.",
    )
    asset_vault_max_file_size_bytes: int = Field(
        default=50 * 1024 * 1024,
        description="Maximum allowed asset file upload size in bytes (default 50 MB).",
    )
    stego_signing_private_key_b64: str | None = Field(
        default=None,
        description="Base64 Ed25519 32-byte seed for PNG LSB signing; provide through a secret manager.",
    )
    stego_active_key_id: str | None = Field(default=None, description="Active Ed25519 public key ID (32 lowercase hex chars).")
    stego_public_keys_json: str | None = Field(
        default=None,
        description="JSON object mapping Ed25519 key IDs to Base64 raw public keys.",
    )
    stego_max_image_bytes: int = Field(default=50 * 1024 * 1024, ge=1)
    stego_max_image_pixels: int = Field(default=20_000_000, ge=1)
    stego_max_image_dimension: int = Field(default=10_000, ge=1)
    stego_max_payload_bytes: int = Field(default=4 * 1024 * 1024, ge=0)

    # M5 Hybrid Batch Blockchain Anchoring (optional; never breaks M1-M4 if unset)
    blockchain_network: str = Field(
        default="anvil",
        description="Target blockchain network identifier (e.g., 'anvil', 'sepolia').",
    )
    blockchain_rpc_url: str | None = Field(
        default=None,
        description="JSON-RPC endpoint URL for Anvil local or Ethereum Sepolia.",
    )
    sepolia_rpc_url: str | None = Field(
        default=None,
        description="Optional Ethereum Sepolia JSON-RPC URL used when BLOCKCHAIN_NETWORK=sepolia.",
    )
    blockchain_chain_id: int | None = Field(
        default=None,
        description="Expected EVM chain ID (31337 for Anvil, 11155111 for Sepolia).",
    )
    sepolia_chain_id: int = Field(
        default=11155111,
        description="Chain ID for Ethereum Sepolia public testnet.",
    )
    blockchain_contract_address: str | None = Field(
        default=None,
        description="Deployed BatchAnchorRegistry contract address (0x...).",
    )
    blockchain_signer_private_key: str | None = Field(
        default=None,
        description="Private key (env-only, never logged or exposed) for the authorized anchor signer.",
    )
    blockchain_receipt_timeout_seconds: int = Field(default=45, ge=5, le=300)
    blockchain_default_batch_size: int = Field(default=500, ge=1, le=5000)

    @property
    def effective_blockchain_network(self) -> str:
        return (self.blockchain_network or "anvil").strip().lower()

    @property
    def effective_blockchain_rpc_url(self) -> str | None:
        net = self.effective_blockchain_network
        if net == "sepolia" and self.sepolia_rpc_url:
            return self.sepolia_rpc_url.strip()
        return self.blockchain_rpc_url.strip() if self.blockchain_rpc_url else None

    @property
    def effective_blockchain_chain_id(self) -> int:
        if self.blockchain_chain_id is not None:
            return self.blockchain_chain_id
        if self.effective_blockchain_network == "sepolia":
            return self.sepolia_chain_id
        return 31337

    @property
    def notes_master_key_bytes(self) -> bytes:
        """
        Resolve the 32-byte master key for Secure Notes encryption.
        Fails closed in production if not explicitly set or not valid 32-byte Base64.
        """
        if not self.notes_master_key_b64:
            if self.app_env == "production":
                raise ValueError(
                    "CRITICAL: NOTES_MASTER_KEY_B64 is mandatory in production environments."
                )
            return DEV_DEFAULT_NOTES_KEY

        try:
            raw_key = base64.b64decode(self.notes_master_key_b64, validate=True)
        except Exception as err:
            raise ValueError(
                "NOTES_MASTER_KEY_B64 must be a valid Base64 encoded string."
            ) from err

        if len(raw_key) != 32:
            raise ValueError(
                f"NOTES_MASTER_KEY_B64 must decode to exactly 32 bytes (got {len(raw_key)})."
            )

        return raw_key

    @property
    def asset_vault_master_key_bytes(self) -> bytes:
        """
        Resolve the 32-byte master key for Asset Vault XChaCha20-Poly1305 encryption.
        Fails closed in production if not explicitly set or not valid 32-byte Base64.
        """
        if not self.asset_vault_master_key_b64:
            if self.app_env == "production":
                raise ValueError(
                    "CRITICAL: ASSET_VAULT_MASTER_KEY_B64 is mandatory in production environments."
                )
            return DEV_DEFAULT_ASSET_VAULT_KEY

        try:
            raw_key = base64.b64decode(self.asset_vault_master_key_b64, validate=True)
        except Exception as err:
            raise ValueError(
                "ASSET_VAULT_MASTER_KEY_B64 must be a valid Base64 encoded string."
            ) from err

        if len(raw_key) != 32:
            raise ValueError(
                f"ASSET_VAULT_MASTER_KEY_B64 must decode to exactly 32 bytes (got {len(raw_key)})."
            )

        return raw_key

    @property
    def effective_account_recovery_key(self) -> str:
        """
        Resolve the out-of-band recovery authorization key or digest requirement.
        Fails closed in production if neither a valid SHA-256 digest nor a strong non-default key is configured.
        """
        digest = (self.account_recovery_key_sha256 or "").strip().lower()
        key = (self.account_recovery_key or "").strip()
        if self.app_env == "production":
            if digest:
                if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                    raise ValueError(
                        "CRITICAL: ACCOUNT_RECOVERY_KEY_SHA256 must be a valid 64-character hex digest."
                    )
                return ""
            if not key or key == "ipguard-dev-recovery-secret-key" or len(key) < 32:
                raise ValueError(
                    "CRITICAL: A strong non-default ACCOUNT_RECOVERY_KEY (>=32 chars) or ACCOUNT_RECOVERY_KEY_SHA256 is mandatory in production."
                )
        return key

    @property
    def storage_directory(self) -> Path:
        """Resolve persistent storage directory for encrypted asset binaries."""
        if self.asset_vault_storage_dir:
            path = Path(self.asset_vault_storage_dir).resolve()
        else:
            path = BACKEND_DIR / "storage"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def trusted_origin_list(self) -> list[str]:
        raw = self.trusted_origins if self.trusted_origins else self.cors_origins
        return [
            origin.strip()
            for origin in raw.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
