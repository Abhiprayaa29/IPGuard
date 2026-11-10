# IPGuard — Data Flow Documentation

**Document ID:** `docs/DATA_FLOW.md`  
**Classification:** Operational Data Flow Specification  
**Status:** Frozen & Verified (Milestones M0–M4)  
**Last Updated:** November 10, 2026  

---

## 1. Overview

This document specifies the end-to-end data pipelines and sequence flows across the IPGuard ecosystem. All flows preserve strict confidentiality, authenticated integrity, and verifiable non-repudiation.

---

## 2. Flow 1: Device Registration & Hardware Keystore Enrollment (M2)

Enrolls a physical Android smartphone as an authorized hardware authenticator.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Android as Android Authenticator
    participant Keystore as Android Keystore (TEE)
    participant API as FastAPI Backend (/api/v1/auth)
    participant DB as PostgreSQL 17

    User->>Android: Launch app & tap "Enroll Device"
    Android->>Keystore: GenerateKeyPair(secp256r1, non-exportable)
    Keystore-->>Android: Return Public Key PEM
    Android->>Android: Calculate Device Fingerprint (SHA-256)
    Android->>API: POST /devices/register {device_name, public_key_pem, fingerprint}
    API->>DB: BEGIN TRANSACTION
    API->>DB: SELECT * FROM devices WHERE fingerprint = ? FOR UPDATE
    alt Device already registered
        DB-->>API: Duplicate Found
        API-->>Android: HTTP 409 Conflict (Duplicate Registration Rejected)
    else New device
        API->>DB: INSERT INTO devices (id, fingerprint, public_key, status='ACTIVE')
        API->>DB: COMMIT
        API-->>Android: HTTP 201 Created {device_id, enrolled_at}
        Android->>Android: Persist enrollment state locally
        Android-->>User: Display "Device Enrolled Successfully"
    end
```

---

## 3. Flow 2: Web QR Authentication Handshake & Session Activation (M2)

Facilitates passwordless login to the Web Console using the enrolled hardware authenticator.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Web as Web Console (Browser)
    participant API as FastAPI Backend (/api/v1/auth)
    participant DB as PostgreSQL 17
    participant Android as Android Authenticator
    participant Keystore as Android Keystore (TEE)

    User->>Web: Open IPGuard Web Console
    Web->>API: POST /sessions/challenge
    API->>API: Generate Nonce (CSPRNG 32 bytes) + Browser Secret
    API->>DB: INSERT INTO auth_sessions (session_id, challenge, status='PENDING', expires_at=now+60s)
    API-->>Web: HTTP 200 {session_id, challenge, qr_code_payload, browser_secret}
    Web->>Web: Store browser_secret in sessionStorage; render dynamic QR
    Web->>API: Poll GET /sessions/{session_id}/status (every 2s)

    User->>Android: Open CameraX QR Scanner & Point to Screen
    Android->>Android: Decode QR payload {session_id, challenge}
    User->>Android: Confirm Login Approval
    Android->>Keystore: Sign challenge with private key (ECDSA P-256 + SHA-256)
    Keystore-->>Android: Return DER signature
    Android->>API: POST /sessions/{session_id}/approve {device_id, signature_der}
    API->>DB: SELECT * FROM devices WHERE id = device_id
    API->>API: Verify ECDSA signature against stored public_key_pem
    API->>DB: UPDATE auth_sessions SET status='APPROVED', device_id=? WHERE id=?
    API-->>Android: HTTP 200 {status: "APPROVED"}

    Web->>API: Next poll GET /sessions/{session_id}/status
    API-->>Web: HTTP 200 {status: "APPROVED", exchange_token}
    Web->>API: POST /sessions/{session_id}/exchange {browser_secret, exchange_token}
    API->>API: Validate browser_secret & Issue JWT Bearer Token (300s TTL)
    API-->>Web: HTTP 200 {access_token, token_type: "bearer", device_id}
    Web->>Web: Save token in sessionStorage & Redirect to /vault
```

---

## 4. Flow 3: Asset Upload & Encrypted Storage Pipeline (M3)

Ingests user files into the secure vault without storing unencrypted plaintext on disk.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Web as Web Console (/vault)
    participant API as FastAPI Backend (/api/v1/assets)
    participant Disk as Encrypted File Storage
    participant DB as PostgreSQL 17

    User->>Web: Drag & Drop PNG File into Vault
    Web->>API: POST /upload (Multipart Form Data, Bearer Token)
    API->>API: Validate session & extract authenticated device_id
    API->>API: Inspect file header (PNG magic bytes: 89 50 4E 47 0D 0A 1A 0A)
    API->>API: Compute master plaintext SHA-256
    API->>API: Derive subkey: HKDF(MasterKey, salt=nonce, info="v1|device_id|asset_id")
    API->>API: Encrypt stream via XChaCha20-Poly1305 (24-byte nonce)
    API->>Disk: Write ciphertext file (backend/storage/{storage_key}.enc)
    API->>DB: INSERT INTO assets (id, owner_device_id, original_filename, sha256_hash, storage_path, cipher_type='XCHACHA20_POLY1305')
    API-->>Web: HTTP 201 Created {asset_id, filename, size, mime_type, created_at}
    Web-->>User: Update Vault Table with "Original Asset" badge
```

---

## 5. Flow 4: Steganographic Watermark Embedding Pipeline (M4)

Generates a watermarked derivative image signed with Ed25519 and embedded via 1-bit LSB.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Web as Web Console
    participant API as FastAPI Backend (/api/v1/assets)
    participant Stego as PNG Stego Engine
    participant Disk as Storage Disk
    participant DB as PostgreSQL 17

    User->>Web: Select Asset & Open "Embed Watermark" Modal
    User->>Web: Fill custom metadata (Copyright, License) & Submit
    Web->>API: POST /steganography/embed {asset_id, metadata, custom_text}
    API->>Disk: Read & Decrypt master ciphertext in-memory (XChaCha20-Poly1305)
    API->>Stego: Load Truecolor RGB/RGBA pixels via Pillow
    Stego->>Stego: Validate Carrier Capacity: (W * H * 3 bits) >= Frame Size
    Stego->>Stego: Construct IPGW Binary Header (170 bytes)
    Stego->>Stego: Sign Header + JSON Payload with Server Ed25519 Key
    Stego->>Stego: Embed binary bits into LSBs of RGB pixel channels
    Stego->>Stego: Encode lossless PNG in memory
    API->>API: Derive new subkey & Encrypt derivative via XChaCha20-Poly1305
    API->>Disk: Write derivative ciphertext file
    API->>DB: BEGIN TRANSACTION
    API->>DB: INSERT INTO assets (id=derivative_id, source_asset_id=master_id, derivative_type='PNG_LSB', watermark_id=wm_uuid)
    API->>DB: SELECT * FROM audit_chain_heads FOR UPDATE
    API->>DB: Append Event to audit_events (rolling SHA-256 hash)
    API->>DB: COMMIT
    API-->>Web: HTTP 200 {derivative_id, watermark_id, ed25519_key_id, signature}
    Web-->>User: Display Success Notification & Refresh Vault Table
```

---

## 6. Flow 5: Watermark Verification & Extraction Pipeline (M4)

Verifies and extracts cryptographic watermarks from an embedded PNG derivative.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Web as Web Console
    participant API as FastAPI Backend (/api/v1/assets)
    participant Stego as PNG Stego Engine

    alt Verification Workflow
        User->>Web: Click "Verify Watermark" on Derivative Asset
        Web->>API: GET /steganography/{derivative_id}/verify
        API->>Stego: Read LSBs from RGB pixels
        Stego->>Stego: Check Magic Bytes == "IPGW"
        Stego->>Stego: Recompute Payload SHA-256 & Compare
        Stego->>Stego: Verify Ed25519 Signature against public key registry
        Stego-->>API: VerificationResult {is_valid: true, key_id, digests_match: true}
        API-->>Web: HTTP 200 {status: "VERIFIED", key_id, signed_at, lineage}
        Web-->>User: Render Verification Success Modal (Green Status)
    else Extraction Workflow
        User->>Web: Click "Extract Watermark"
        Web->>API: GET /steganography/{derivative_id}/extract
        API->>Stego: Read & Decode LSB Header and Payload
        alt Any tampering detected (Bit-flip, altered pixels)
            Stego-->>API: Signature Verification Failure
            API-->>Web: HTTP 409 Conflict {"detail": "Watermark payload corrupt or tampered"}
            Web-->>User: Display Tamper Warning Alert
        else Authentic image
            Stego-->>API: Decoded JSON metadata & cryptographic proofs
            API-->>Web: HTTP 200 {watermark_id, copyright, license, signature, raw_payload}
            Web-->>User: Display Extracted Metadata Cards & JSON Viewer
        end
    end
```

---

## 7. Flow 6: Background Periodic Integrity Auditing (M4)

Validates the physical storage integrity and detects offline corruption or tampering.

```mermaid
sequenceDiagram
    autonumber
    participant Worker as Integrity Background Worker
    participant DB as PostgreSQL 17
    participant Disk as Encrypted File Storage

    Worker->>DB: Query assets requiring integrity sweep
    loop For Each Asset
        Worker->>Disk: Read raw ciphertext from disk
        Worker->>Worker: Compute current SHA-256 digest of ciphertext
        alt Ciphertext Digest Matches Stored Baseline
            Worker->>DB: UPDATE assets SET last_integrity_check=now(), integrity_status='OK'
        else Ciphertext Modified / Bit Rot Detected
            Worker->>DB: UPDATE assets SET integrity_status='CORRUPTED'
            Worker->>DB: SELECT * FROM audit_chain_heads FOR UPDATE
            Worker->>DB: Append ALERT event to audit_events table
            Worker->>Worker: Log critical security warning
        end
    end
```
