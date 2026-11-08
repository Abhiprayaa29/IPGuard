package com.ipguard.authenticator.network

data class VerifySessionRequest(
    val deviceId: String,
    val canonicalPayload: String,
    val signature: String
)

data class RegisterDeviceRequest(
    val sessionToken: String,
    val deviceId: String,
    val deviceName: String,
    val model: String,
    val androidVersion: String,
    val publicKeyX509: String,
    val securityLevel: String,
    val canonicalPayload: String,
    val signature: String
)

data class SessionStatusDto(
    val sessionToken: String,
    val status: String,
    val sessionType: String,
    val expiresAt: String
)

data class DeviceRegisteredDto(
    val id: String,
    val deviceId: String,
    val deviceName: String,
    val status: String,
    val publicKeyFingerprint: String
)

data class DeviceStatusDto(
    val deviceId: String,
    val status: String,
    val registrationStatus: String,
    val accessStatus: String,
    val publicKeyFingerprint: String? = null
)
