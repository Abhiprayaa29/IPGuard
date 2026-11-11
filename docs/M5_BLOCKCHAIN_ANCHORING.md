# IPGuard M5 — Hybrid Batch Audit Anchoring Architecture

**Date:** 2026-11-11  
**Branch:** `feature/product-ui-redesign-device-lifecycle`  
**Status:** Local Anvil MVP Verified (`PASS`); Ethereum Sepolia Deployment Prepared (`BLOCKED` — external RPC/key/faucet ETH not supplied); Mainnet Out of Scope

---

## 1. Why Hybrid Batch Anchoring Is Used
Recording every HTTP login, note save, or file upload directly as an individual EVM transaction would introduce block confirmation latency, gas overhead, nonce serialization bottlenecks, and retry complexity into core application workflows.

Instead, IPGuard keeps low-latency operations in PostgreSQL and anchors verified batches externally:
1. All application security events continue writing synchronously into PostgreSQL `audit_events` via the existing append-only SHA-256 hash chain (`AUDIT_DOMAIN = b"IPGUARD-AUDIT-V1\x00"`).
2. Prior to anchoring, `verify_audit_chain` validates the entire hash chain (`event_hash`, `prev_hash` linkage, canonical UTF-8 payload, and contiguous `sequence`). Invalid or corrupted chains are **rejected immediately** (`audit_chain_invalid`) and never anchored.
3. Valid contiguous unanchored slices are summarized into a single Keccak-256 Merkle root and anchored on-chain via `BatchAnchorRegistry.anchorBatch`.

**Privacy boundary:** Original event payloads (`canonical_payload`), Secure Notes, Asset Vault binaries, Recovery Keys, biometric templates, bearer tokens, and user metadata remain strictly off-chain.

---

## 2. Existing M4 Audit Hash Chain Preservation
No changes were made to:
- `backend/app/models/audit.py` (`AuditChainHead`, `AuditEvent`, append-only SQLAlchemy hooks)
- `backend/app/services/audit_chain.py` (`append_audit_event`, `verify_audit_chain`)
- M2 hardware authentication, M3 Secure Notes super-encryption (`Vigenere + AES-256-GCM`), M3 Asset Vault (`XChaCha20-Poly1305`), or M4 PNG LSB Steganography (`Ed25519`).

Blockchain failures (RPC unreachable, timeout, insufficient funds, revert) are isolated inside `backend/app/services/blockchain.py` and `/api/v1/blockchain/*` so core IPGuard workflows never block on RPC availability.

---

## 3. Deterministic Keccak-256 Merkle Tree Specification
Implemented in `backend/app/services/merkle.py` and mirrored bit-for-bit in `BatchAnchorRegistry.computeMerkleRoot`:

- **Leaf commitment (`0x00` domain prefix):**  
  `leaf_i = keccak256(0x00 || raw_event_hash_bytes_32)`
- **Internal node commitment (`0x01` domain prefix):**  
  `node = keccak256(0x01 || left_32 || right_32)` (ordered strictly by ascending contiguous `sequence`)
- **Odd node-count rule:** If a tree level has an odd number of nodes (`> 1`), the final node at that level is duplicated (`level.append(level[-1])`) before pairing.
- **On-chain audit chain key:**  
  `auditChainId = keccak256(utf8(chain_id))` (`bytes32`).

Python-to-Solidity root parity was verified directly on live Anvil against `BatchAnchorRegistry.computeMerkleRoot` on the 10-event chain `stego-owner-464a6f53fa13` (`0xb5193d3a219ca08b211f0d25c1421d23a071f494bcf4399f759bcae10b784458`).

---

## 4. Solidity Smart Contract (`BatchAnchorRegistry.sol`)
Located at `blockchain/contracts/BatchAnchorRegistry.sol` (compiled with Solc `0.8.24`):

- **Key separation:** Distinct `owner` (rotates signer via `setAuthorizedSigner` / `transferOwnership`) and `authorizedSigner` (`msg.sender == authorizedSigner` required by `anchorBatch`).
- **Stored commitment (`BatchAnchor` struct):**
  `auditChainId`, `fromSequence`, `toSequence`, `merkleRoot`, `headHash`, `blockTimestamp`, `signer`.
- **Invariants enforced on-chain:**
  - Non-zero `auditChainId`, `merkleRoot`, and `headHash`.
  - Valid sequence bounds (`fromSequence > 0`, `toSequence >= fromSequence`).
  - No duplicate or overlapping batches (`DuplicateOrOverlappingBatch`).
  - Strict sequence contiguity (`NonContiguousSequence`) for subsequent batches (`fromSequence == lastAnchoredSequence + 1`), while allowing any valid verified starting sequence on the first batch.
- **View & Verification:** `getBatch`, `getBatchByRange`, `verifyBatch`, `computeMerkleRoot`.

---

## 5. PostgreSQL Anchor Registry (Migration `0011`)
Migration `backend/app/db/migrations/versions/0011_audit_blockchain_anchors.py` creates table `audit_blockchain_anchors` (`backend/app/models/blockchain.py`):

- Tracks `id`, `audit_chain_id`, `from_sequence`, `to_sequence`, `event_count`, `merkle_root`, `head_hash`, `batch_reference`, `network`, `chain_id`, `contract_address`, `signer_address`, `tx_hash`, `block_number`, `block_timestamp`, `status` (`PENDING`, `SUBMITTED`, `CONFIRMED`, `FAILED`, `REORGED`), `created_at`, `confirmed_at`, `error_message`.
- Unique constraint `uq_audit_blockchain_anchor_batch` enforces database-level deduplication per `(audit_chain_id, from_sequence, to_sequence, network, contract_address)`.
- `anchor_audit_batch` acquires a PostgreSQL row-level lock (`SELECT ... FOR UPDATE` on `AuditChainHead`), commits `tx_hash` in `SUBMITTED` status before waiting for confirmation receipt, and reconciles timeouts cleanly via `verify_blockchain_anchor` without blindly submitting duplicate transactions.

---

## 6. Backend API Endpoints (`/api/v1/blockchain`)
All endpoints are protected by `get_current_authenticated_device` (M2 hardware session bearer authentication) and scoped to the caller's active `device_id`:

- `GET /api/v1/blockchain/anchors` — Returns network metadata (`LOCAL DEVELOPMENT NETWORK` or `ETHEREUM SEPOLIA TESTNET`), contract/signer public addresses, audit chain validity, anchored vs pending counts, and recent anchor records.
- `POST /api/v1/blockchain/anchors` — Runs `verify_audit_chain`, builds a contiguous Merkle batch, submits `anchorBatch`, awaits receipt confirmation, and verifies on-chain storage.
- `GET /api/v1/blockchain/anchors/{anchor_id}/verify` — Re-verifies the PostgreSQL audit hash chain, recomputes the local Merkle root over `[from_sequence..to_sequence]`, reconciles the EVM receipt, and verifies against `BatchAnchorRegistry.verifyBatch`.

Private keys are read exclusively from environment variables in `Settings` and never returned in API responses or error messages.

---

## 7. Deployment Distinction & Security Limitations

| Target | Network / Chain ID | Status | Notes |
|---|---|---|---|
| **Local Development** | **Anvil** (`31337`) | **PASS (Deployed & Verified)** | Ephemeral local EVM node on `127.0.0.1:8545`. Not a public blockchain; state resets when Anvil stops. |
| **Public Testnet** | **Ethereum Sepolia** (`11155111`) | **BLOCKED (Ready Script)** | Deployment script & config prepared; blocked locally due to missing `SEPOLIA_RPC_URL`, funded signer key, and Sepolia test ETH. |
| **Mainnet** | Ethereum Mainnet (`1`) | **Not Deployed / Blocked** | Explicitly excluded from M5 MVP scope; `network == "mainnet"` is rejected in `inspect_blockchain_config`. |

### Security Limitations
- If Anvil is restarted, local chain state is ephemeral; Sepolia/persistent EVM is required for durable external immutability.
- Batch anchoring is manual (`POST /api/v1/blockchain/anchors`) so unanchored trailing events depend on operator invocation before they gain an external checkpoint.
- Single relayer key holds gas & `authorizedSigner` privilege; rotating via `owner.setAuthorizedSigner` mitigates relayer key compromise.
