# IPGuard M5 — Blockchain Integration Test & Verification Report

**Test Date:** 2026-11-11  
**Branch:** `feature/product-ui-redesign-device-lifecycle`  
**Networks Tested:** Local Anvil (`chainId: 31337`); Ethereum Sepolia (`BLOCKED` — missing credentials/faucet ETH)

---

## 1. Automated Test Summary

| Component | Command | Result | Status |
|---|---|---|---|
| **Solidity Smart Contract (Foundry)** | `cd blockchain && forge test -vv` | `8 passed, 0 failed, 0 skipped` (`BatchAnchorRegistryTest`) | **PASS** |
| **Backend M5 Merkle Unit Tests** | `pytest tests/test_merkle.py -v` | `5 passed, 0 failed` | **PASS** |
| **Backend M5 Anchoring & Auth Tests** | `pytest tests/test_blockchain_anchoring.py -v` | `5 passed, 0 failed` | **PASS** |
| **Full Backend Regression (M1–M5)** | `cd backend && python -m pytest -v -q` | `234 passed, 1 skipped` (`test_audit_chain_postgres.py` opt-in when `IPGUARD_TEST_POSTGRES_URL` unset) | **PASS** |
| **Frontend TypeScript & Build** | `cd frontend && npm run typecheck && npm run build` | `0` TS errors, Vite built `2208` modules cleanly | **PASS** |
| **Live Anvil E2E UI Flow (Playwright)** | `/system-status` -> `Anchor Audit Batch` -> `Verify On-Chain` | Real Anvil tx mined & verified `PASS` | **PASS** |
| **Ethereum Sepolia Public Testnet** | Env preflight check (`SEPOLIA_RPC_URL`, `BLOCKCHAIN_SIGNER_PRIVATE_KEY`) | Missing RPC URL, funded Sepolia key, and test ETH | **BLOCKED** |

---

## 2. Smart Contract Test Matrix (`BatchAnchorRegistry.t.sol`)
- `test_AuthorizedAnchoringAndRetrieval` — Verifies `BatchAnchored` storage retrieval & `verifyBatch` truthiness (`PASS`).
- `test_UnauthorizedAnchoringReverts` — Non-signer caller reverts with `UnauthorizedSigner` (`PASS`).
- `test_ZeroRootOrHeadReverts` — Rejects zero Merkle root and zero head hash (`PASS`).
- `test_InvalidSequenceRangeReverts` — Rejects `fromSequence == 0` and inverted ranges (`PASS`).
- `test_DuplicateAndOverlappingBatchReverts` — Reverts on identical or overlapping ranges (`PASS`).
- `test_GapSequenceRevertsAndContiguousSucceeds` — Rejects skipped sequence gaps (`1..10` -> `12..20`), accepts `11..20` (`PASS`).
- `test_SignerRotationByOwnerOnly` — Owner rotates signer while attacker calls revert (`PASS`).
- `test_ComputeMerkleRootOddEvenAndSingle` — Verifies single-leaf (`0x00`), odd duplication rule, and internal (`0x01`) node Keccak-256 math (`PASS`).

---

## 3. Live PostgreSQL + Anvil Verification Details

### Pre-Existing Dev Fixture Gap Observed (Safety Guard Proof)
- Running `verify_audit_chain` on PostgreSQL found `origin-bound-device-01` has a pre-existing sequence gap at sequence `35` (`reason_code='sequence_gap_or_reorder'`). Consistent with M5 safety policy, historical audit rows were **not** altered and anchoring is refused on any chain failing `verify_audit_chain`.

### Verified Clean Chain End-to-End Evidence (Local Anvil)
- **Audit Chain ID:** `stego-owner-464a6f53fa13`
- **Audit Chain Integrity:** `VALID` (`10` events, sequence range `1..10`)
- **BatchAnchorRegistry Contract:** `0x5FbDB2315678afecb367f032d93F642f64180aa3`
- **Deployer (Owner):** `0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266` (Tx: `0x12db6519b437b4b54965bcbe385b08e197dbea97ad816817877ae6501ef7980d`, Block `1`)
- **Authorized Signer:** `0x70997970C51812dc3A010C7d01b50e0d17dc79C8`
- **Batch Merkle Root (Python == Solidity):** `0xb5193d3a219ca08b211f0d25c1421d23a071f494bcf4399f759bcae10b784458`
- **Head Hash:** `0x200c1bd84518e63ad269f84b9e2d47ee3d9a8a8982f190fee1d71038effd282d`
- **Anchor Tx Hash (Anvil):** `0x47fdd75a67f74aa314f496e286b6df6c5d970807e01192904d99bc5fa50f92fd`
- **Anvil Block Number:** `2` (`status: 1`, `gasUsed: 208336`)
- **Web Console Screenshots Captured (`1440×900`):**
  - `docs/visual-evidence/web/blockchain-anchoring-ready.png`
  - `docs/visual-evidence/web/blockchain-anchoring-confirmed.png`
  - `docs/visual-evidence/web/blockchain-anchoring-verified.png`
