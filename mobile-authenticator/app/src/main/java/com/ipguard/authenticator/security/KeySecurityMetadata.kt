package com.ipguard.authenticator.security

data class KeySecurityMetadata(
    val alias: String,
    val algorithm: String,
    val keySize: Int,
    val curve: String,
    val digests: List<String>,
    val purposes: Int,
    val isInsideSecureHardware: Boolean,
    val securityLevel: KeySecurityLevel,
    val userAuthenticationRequired: Boolean,
    val userAuthenticationValidityDurationSeconds: Int,
    val userAuthenticationTypes: Int,
    val isInvalidatedByBiometricEnrollment: Boolean?,
    val isNonExportable: Boolean
)
