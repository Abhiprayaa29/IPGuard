package com.ipguard.authenticator.security.qr

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

class QrAuthPayloadParserTest {

    private val parser = QrAuthPayloadParser()
    private val now = 1793976800L
    private val validToken = "a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0"
    private val validNonce = "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"
    private val validOrigin = "http://localhost:5173"

    private fun buildJson(
        version: String = "1.0",
        type: String = "AUTHENTICATION",
        token: String = validToken,
        nonce: String = validNonce,
        origin: String = validOrigin,
        timestamp: Long = now
    ): String {
        return """
            {
                "version": "$version",
                "type": "$type",
                "session_token": "$token",
                "nonce": "$nonce",
                "origin": "$origin",
                "timestamp": $timestamp
            }
        """.trimIndent()
    }

    @Test
    fun parse_validAuthenticationPayload_succeeds() {
        val raw = buildJson(type = "AUTHENTICATION")
        val result = parser.parse(raw, currentEpochSeconds = now + 10)

        assertTrue(result is QrPayloadValidationResult.Valid)
        val payload = (result as QrPayloadValidationResult.Valid).payload
        assertEquals("1.0", payload.version)
        assertEquals(QrSessionType.AUTHENTICATION, payload.type)
        assertEquals(validToken, payload.sessionToken)
        assertEquals(validNonce, payload.nonce)
        assertEquals(validOrigin, payload.origin)
        assertEquals(now, payload.timestamp)

        // Verify canonical payload format: {session_token}:{nonce}:{origin}:{timestamp}
        assertEquals(
            "$validToken:$validNonce:$validOrigin:$now",
            payload.buildCanonicalPayload()
        )
    }

    @Test
    fun parse_validEnrollmentPayload_succeeds() {
        val raw = buildJson(type = "ENROLLMENT")
        val result = parser.parse(raw, currentEpochSeconds = now)

        assertTrue(result is QrPayloadValidationResult.Valid)
        val payload = (result as QrPayloadValidationResult.Valid).payload
        assertEquals(QrSessionType.ENROLLMENT, payload.type)
    }

    @Test
    fun parse_emptyOrBlank_returnsInvalid() {
        val result1 = parser.parse("", now)
        assertTrue(result1 is QrPayloadValidationResult.Invalid)
        assertEquals(QrPayloadValidationResult.Invalid.CODE_EMPTY_PAYLOAD, (result1 as QrPayloadValidationResult.Invalid).errorCode)

        val result2 = parser.parse("   ", now)
        assertTrue(result2 is QrPayloadValidationResult.Invalid)
    }

    @Test
    fun parse_oversized_returnsInvalid() {
        val oversized = "a".repeat(2049)
        val result = parser.parse(oversized, now)
        assertTrue(result is QrPayloadValidationResult.Invalid)
        assertEquals(QrPayloadValidationResult.Invalid.CODE_OVERSIZED_PAYLOAD, (result as QrPayloadValidationResult.Invalid).errorCode)
    }

    @Test
    fun parse_malformedJson_returnsInvalid() {
        val result = parser.parse("{not-valid-json", now)
        assertTrue(result is QrPayloadValidationResult.Invalid)
        assertEquals(QrPayloadValidationResult.Invalid.CODE_MALFORMED_JSON, (result as QrPayloadValidationResult.Invalid).errorCode)
    }

    @Test
    fun parse_forbiddenSecretField_returnsInvalid() {
        val withSecret = """
            {
                "version": "1.0",
                "type": "AUTHENTICATION",
                "session_token": "$validToken",
                "nonce": "$validNonce",
                "origin": "$validOrigin",
                "timestamp": $now,
                "browser_channel_token": "secret_token_123"
            }
        """.trimIndent()
        val result = parser.parse(withSecret, now)
        assertTrue(result is QrPayloadValidationResult.Invalid)
        assertEquals(QrPayloadValidationResult.Invalid.CODE_FORBIDDEN_FIELD, (result as QrPayloadValidationResult.Invalid).errorCode)
    }

    @Test
    fun parse_unsupportedVersion_returnsInvalid() {
        val raw = buildJson(version = "2.0")
        val result = parser.parse(raw, now)
        assertTrue(result is QrPayloadValidationResult.Invalid)
        assertEquals(QrPayloadValidationResult.Invalid.CODE_UNSUPPORTED_VERSION, (result as QrPayloadValidationResult.Invalid).errorCode)
    }

    @Test
    fun parse_unsupportedType_returnsInvalid() {
        val raw = buildJson(type = "UNKNOWN_TRANSACTION")
        val result = parser.parse(raw, now)
        assertTrue(result is QrPayloadValidationResult.Invalid)
        assertEquals(QrPayloadValidationResult.Invalid.CODE_UNSUPPORTED_TYPE, (result as QrPayloadValidationResult.Invalid).errorCode)
    }

    @Test
    fun parse_invalidSessionToken_returnsInvalid() {
        val raw = buildJson(token = "too_short")
        val result = parser.parse(raw, now)
        assertTrue(result is QrPayloadValidationResult.Invalid)
        assertEquals(QrPayloadValidationResult.Invalid.CODE_INVALID_TOKEN, (result as QrPayloadValidationResult.Invalid).errorCode)
    }

    @Test
    fun parse_invalidNonce_returnsInvalid() {
        val raw = buildJson(nonce = "z".repeat(64)) // 'z' is not a valid hex character
        val result = parser.parse(raw, now)
        assertTrue(result is QrPayloadValidationResult.Invalid)
        assertEquals(QrPayloadValidationResult.Invalid.CODE_INVALID_NONCE, (result as QrPayloadValidationResult.Invalid).errorCode)
    }

    @Test
    fun parse_invalidOrigin_returnsInvalid() {
        // Query param in origin
        val raw1 = buildJson(origin = "http://localhost:5173?evil=true")
        val res1 = parser.parse(raw1, now)
        assertTrue(res1 is QrPayloadValidationResult.Invalid)
        assertEquals(QrPayloadValidationResult.Invalid.CODE_INVALID_ORIGIN, (res1 as QrPayloadValidationResult.Invalid).errorCode)

        // Missing scheme
        val raw2 = buildJson(origin = "localhost:5173")
        val res2 = parser.parse(raw2, now)
        assertTrue(res2 is QrPayloadValidationResult.Invalid)
    }

    @Test
    fun parse_expiredTimestamp_returnsInvalid() {
        // Timestamp is 200s older than current time (maxAge is 180s)
        val raw = buildJson(timestamp = now - 200)
        val result = parser.parse(raw, currentEpochSeconds = now)
        assertTrue(result is QrPayloadValidationResult.Invalid)
        assertEquals(QrPayloadValidationResult.Invalid.CODE_EXPIRED_TIMESTAMP, (result as QrPayloadValidationResult.Invalid).errorCode)
    }

    @Test
    fun parse_futureTimestampDrift_returnsInvalid() {
        // Timestamp is 100s in the future
        val raw = buildJson(timestamp = now + 100)
        val result = parser.parse(raw, currentEpochSeconds = now)
        assertTrue(result is QrPayloadValidationResult.Invalid)
        assertEquals(QrPayloadValidationResult.Invalid.CODE_INVALID_TIMESTAMP, (result as QrPayloadValidationResult.Invalid).errorCode)
    }
}
