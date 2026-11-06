package com.ipguard.authenticator.security

enum class KeySecurityLevel(val label: String) {
    SOFTWARE("Software-backed"),
    TRUSTED_ENVIRONMENT("Trusted Execution Environment (TEE)"),
    STRONGBOX("StrongBox Keymaster"),
    UNKNOWN("Unknown / unavailable")
}
