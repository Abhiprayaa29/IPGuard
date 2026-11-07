package com.ipguard.authenticator.security.qr

import org.json.JSONException
import org.json.JSONObject
import java.net.URI

class QrAuthPayloadParser(
    private val maxPayloadLength: Int = 2048,
    private val supportedVersion: String = "1.0",
    private val maxAgeSeconds: Long = 180L,
    private val maxFutureDriftSeconds: Long = 60L
) {
    private val hex64Regex = Regex("^[0-9a-fA-F]{64}$")
    private val forbiddenFields = setOf(
        "browser_channel_token",
        "channel_token",
        "access_token",
        "private_key",
        "admin_key",
        "dev_admin_key"
    )

    fun parse(rawContent: String?, currentEpochSeconds: Long = System.currentTimeMillis() / 1000L): QrPayloadValidationResult {
        if (rawContent.isNullOrBlank()) {
            return QrPayloadValidationResult.Invalid(
                reason = "QR payload is empty or blank",
                errorCode = QrPayloadValidationResult.Invalid.CODE_EMPTY_PAYLOAD
            )
        }

        if (rawContent.length > maxPayloadLength) {
            return QrPayloadValidationResult.Invalid(
                reason = "QR payload exceeds maximum length limit of $maxPayloadLength bytes",
                errorCode = QrPayloadValidationResult.Invalid.CODE_OVERSIZED_PAYLOAD
            )
        }

        val json = try {
            JSONObject(rawContent)
        } catch (e: JSONException) {
            return QrPayloadValidationResult.Invalid(
                reason = "QR payload is not valid JSON: ${e.message}",
                errorCode = QrPayloadValidationResult.Invalid.CODE_MALFORMED_JSON
            )
        }

        // Anti QR-Jacking & Secret Leak Boundary
        for (forbidden in forbiddenFields) {
            if (json.has(forbidden)) {
                return QrPayloadValidationResult.Invalid(
                    reason = "QR payload contains forbidden credential or browser secret field '$forbidden'",
                    errorCode = QrPayloadValidationResult.Invalid.CODE_FORBIDDEN_FIELD
                )
            }
        }

        // 1. Version validation
        val version = json.optString("version")
        if (version != supportedVersion) {
            return QrPayloadValidationResult.Invalid(
                reason = "Unsupported QR protocol version '$version'. Supported version is '$supportedVersion'",
                errorCode = QrPayloadValidationResult.Invalid.CODE_UNSUPPORTED_VERSION
            )
        }

        // 2. Type validation
        val typeString = json.optString("type")
        val sessionType = QrSessionType.fromString(typeString)
            ?: return QrPayloadValidationResult.Invalid(
                reason = "Unsupported session type '$typeString'. Must be AUTHENTICATION or ENROLLMENT",
                errorCode = QrPayloadValidationResult.Invalid.CODE_UNSUPPORTED_TYPE
            )

        // 3. Session token validation
        val sessionToken = json.optString("session_token")
        if (!hex64Regex.matches(sessionToken)) {
            return QrPayloadValidationResult.Invalid(
                reason = "Session token must be exactly 64 hexadecimal characters",
                errorCode = QrPayloadValidationResult.Invalid.CODE_INVALID_TOKEN
            )
        }

        // 4. Nonce validation
        val nonce = json.optString("nonce")
        if (!hex64Regex.matches(nonce)) {
            return QrPayloadValidationResult.Invalid(
                reason = "Challenge nonce must be exactly 64 hexadecimal characters",
                errorCode = QrPayloadValidationResult.Invalid.CODE_INVALID_NONCE
            )
        }

        // 5. Origin validation
        val origin = json.optString("origin").trim().trimEnd('/')
        val originValidation = validateOrigin(origin)
        if (originValidation != null) {
            return QrPayloadValidationResult.Invalid(
                reason = originValidation,
                errorCode = QrPayloadValidationResult.Invalid.CODE_INVALID_ORIGIN
            )
        }

        // 6. Timestamp validation
        val timestamp = json.optLong("timestamp", -1L)
        if (timestamp <= 0L) {
            return QrPayloadValidationResult.Invalid(
                reason = "Timestamp must be a positive integer Unix epoch",
                errorCode = QrPayloadValidationResult.Invalid.CODE_INVALID_TIMESTAMP
            )
        }

        // Timestamp TTL check
        val age = currentEpochSeconds - timestamp
        if (age > maxAgeSeconds) {
            return QrPayloadValidationResult.Invalid(
                reason = "QR challenge has expired (age: ${age}s, max: ${maxAgeSeconds}s)",
                errorCode = QrPayloadValidationResult.Invalid.CODE_EXPIRED_TIMESTAMP
            )
        }
        if (timestamp - currentEpochSeconds > maxFutureDriftSeconds) {
            return QrPayloadValidationResult.Invalid(
                reason = "QR challenge timestamp is in the future by more than ${maxFutureDriftSeconds}s",
                errorCode = QrPayloadValidationResult.Invalid.CODE_INVALID_TIMESTAMP
            )
        }

        return QrPayloadValidationResult.Valid(
            payload = QrAuthPayload(
                version = version,
                type = sessionType,
                sessionToken = sessionToken,
                nonce = nonce,
                origin = origin,
                timestamp = timestamp
            )
        )
    }

    private fun validateOrigin(origin: String): String? {
        if (origin.isBlank()) {
            return "Origin must not be blank"
        }
        if (!origin.startsWith("http://") && !origin.startsWith("https://")) {
            return "Origin must use http or https scheme"
        }
        if (origin.contains('?') || origin.contains('#')) {
            return "Origin must not contain query parameters or fragment"
        }
        return try {
            val uri = URI(origin)
            if (uri.host.isNullOrBlank()) {
                "Origin hostname is missing or invalid"
            } else if (uri.path != null && uri.path.isNotEmpty() && uri.path != "/") {
                "Origin must not contain a path component: '${uri.path}'"
            } else {
                null
            }
        } catch (e: Exception) {
            "Malformed origin URI: ${e.message}"
        }
    }
}
