package com.ipguard.authenticator.security

data class ExportedPublicKey(
    val alias: String,
    val algorithm: String,
    val format: String,
    val curve: String,
    val base64Encoded: String,
    val sha256Fingerprint: String
)
