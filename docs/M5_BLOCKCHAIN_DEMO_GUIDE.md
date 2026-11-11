# IPGuard M5 — Blockchain Batch Anchoring Demo Guide (3–5 Minutes)

## Prerequisites (Local Anvil Setup)
1. Start PostgreSQL 17 and verify Alembic head is at `0011_audit_blockchain_anchors`:
   ```powershell
   cd D:\Projects\IPGuard\backend
   .\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head
   ```
2. Start local Anvil node (`chainId = 31337`):
   ```powershell
   anvil --host 127.0.0.1 --port 8545 --chain-id 31337
   ```
3. Deploy `BatchAnchorRegistry` with separated owner & authorized signer and ensure `backend/.env` sets `BLOCKCHAIN_NETWORK=anvil`, `BLOCKCHAIN_RPC_URL=http://127.0.0.1:8545`, `BLOCKCHAIN_CHAIN_ID=31337`, `BLOCKCHAIN_CONTRACT_ADDRESS`, and `BLOCKCHAIN_SIGNER_PRIVATE_KEY` (untracked in `.env`).
4. Start backend (`uvicorn app.main:app --host 127.0.0.1 --port 8000`) and frontend (`npm run dev -- --port 5173`).

---

## Live Demonstration Walkthrough (~4 Minutes)
1. **Open IPGuard Web Console & Authenticate:**
   Sign in via `/login` with your enrolled Android authenticator (`ACTIVE`), or show an active hardware session.
2. **Navigate to System Status (`/system-status`):**
   Scroll to the **M5 Blockchain Audit Anchoring** panel. Point out:
   - Explicit network label (`LOCAL DEVELOPMENT NETWORK (anvil · chainId 31337)`, or `ETHEREUM SEPOLIA TESTNET` when configured for Sepolia).
   - Deployed `Contract Address` and `Authorized Signer`.
   - Real-time PostgreSQL audit-chain validity (`VALID`) and `Unanchored Events` count.
3. **Click `Anchor Audit Batch`:**
   Explain what executes on the backend:
   - `verify_audit_chain` re-verifies every prior PostgreSQL `audit_events` row (`SHA-256` + `prev_hash` + `sequence`).
   - `merkle.py` builds a Keccak-256 Merkle tree over contiguous `event_hash` digests (`0x00` leaves, `0x01` internal nodes).
   - FastAPI submits a single `anchorBatch` transaction to `BatchAnchorRegistry` using the server-side `authorizedSigner`.
4. **Show Confirmation Receipt:**
   Point out status transitioning to `Confirmed` alongside the returned `Merkle Root`, `Transaction Hash`, `Block Number`, and `Events Anchored` count (and note that on Sepolia the `Transaction Hash` links directly to `sepolia.etherscan.io`, whereas Anvil never fabricates a public explorer link).
5. **Click `Verify On-Chain`:**
   Show the green `On-Chain Verification: VERIFIED PASS` check proving live parity across DB Record, Audit Hash Chain, Local Merkle Recompute, Transaction Receipt, and On-Chain `verifyBatch`.
6. **Emphasize Privacy Scope:**
   Note that zero plaintext notes, file contents, user credentials, or `canonical_payload` fields are stored on-chain — only cryptographic hashes and sequence bounds.
