# IPGuard M5 Blockchain Module (`BatchAnchorRegistry`)

This directory contains the Foundry smart contract project for IPGuard Milestone 5 (**Hybrid Batch Audit Anchoring**).

## Why Batch Anchoring?
Instead of publishing individual PostgreSQL audit events per HTTP action (which slows down QR authentication, Secure Notes, and Asset Vault writes and wastes gas), IPGuard appends events to PostgreSQL `audit_events` via SHA-256 hash chaining (`AUDIT_DOMAIN = IPGUARD-AUDIT-V1\x00`), verifies the complete chain, constructs a deterministic Keccak-256 Merkle root (`0x00` leaf / `0x01` node prefix), and anchors contiguous sequence ranges on-chain.

No plaintext notes, filenames, tokens, biometric data, or raw `canonical_payload` bytes are stored on-chain.

## Structure
- `contracts/BatchAnchorRegistry.sol` — Owner & authorized-signer separated registry storing `auditChainId`, `fromSequence`, `toSequence`, `merkleRoot`, `headHash`, `blockTimestamp`, and `signer`.
- `test/BatchAnchorRegistry.t.sol` — Foundry unit tests covering authorized/unauthorized signers, zero-hash rejection, sequence gaps/overlaps/duplicates, signer rotation, and odd/even/single Merkle root parity.
- `script/Deploy.s.sol` — Deployment script supporting separated `AUTHORIZED_SIGNER_ADDRESS` for Anvil local and Ethereum Sepolia testnet.
- `foundry.toml` — Solc `0.8.24` configuration.

## Local Development Workflow (Anvil)
```powershell
# Terminal 1: Start local EVM chain (Chain ID 31337)
anvil --host 127.0.0.1 --port 8545 --chain-id 31337

# Terminal 2: Compile & run Solidity tests
cd blockchain
forge test -vv

# Deploy using Anvil account #0 as owner and account #1 as separated authorized signer
$env:AUTHORIZED_SIGNER_ADDRESS = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
forge script script/Deploy.s.sol:DeployScript `
  --rpc-url http://127.0.0.1:8545 `
  --unlocked --sender 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266 `
  --broadcast -vv
```

## Public Testnet Preparation (Ethereum Sepolia — Chain ID `11155111`)
Set environment variables without committing secrets to Git:
```powershell
$env:SEPOLIA_RPC_URL = "https://sepolia.infura.io/v3/<PROJECT_ID>"
$env:AUTHORIZED_SIGNER_ADDRESS = "<PUBLIC_SIGNER_ADDRESS>"
forge script script/Deploy.s.sol:DeployScript `
  --rpc-url $env:SEPOLIA_RPC_URL `
  --private-key <DEPLOYER_KEY_FROM_SECURE_ENV> `
  --broadcast -vv
```
Mainnet deployment is explicitly out of scope and blocked by backend configuration.
