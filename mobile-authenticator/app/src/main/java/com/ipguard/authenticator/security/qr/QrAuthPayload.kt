package com.ipguard.authenticator.security.qr

import java.nio.charset.StandardCharsets

/**
 * Immutable data model representing a cryptographically validated QR authentication challenge.
 */
data class QrAuthPayload(
    val version: String,
    val type: QrSessionType,
    val sessionToken: String,
    val nonce: String,
    val origin: String,
    val timestamp: Long
) {
    /**
     * Builds the exact canonical string payload matching backend:
     * `{session_token}:{nonce}:{origin}:{timestamp}`
     */
    fun buildCanonicalPayload(): String {
        return "$sessionToken:$nonce:$origin:$timestamp"
    }

    /**
     * Returns UTF-8 bytes of the canonical payload ready for ECDSA P-256 signing.
     */
    fun getCanonicalBytes(): ByteArray {
        return buildCanonicalPayload().toByteArray(StandardCharsets.UTF_8)
    }
}
