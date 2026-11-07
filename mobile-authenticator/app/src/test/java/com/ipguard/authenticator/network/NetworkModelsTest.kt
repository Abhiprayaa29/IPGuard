package com.ipguard.authenticator.network

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class NetworkModelsTest {

    @Test
    fun testVerifySessionRequestSerialization() {
        val request = VerifySessionRequest(
            deviceId = "ipguard-dev-test-1234",
            canonicalPayload = "sess_token:nonce_val:http://localhost:5173:1700000000",
            signature = "MEQCIGabc123=="
        )

        val json = JSONObject()
        json.put("device_id", request.deviceId)
        json.put("canonical_payload", request.canonicalPayload)
        json.put("signature", request.signature)

        assertEquals("ipguard-dev-test-1234", json.getString("device_id"))
        assertEquals("sess_token:nonce_val:http://localhost:5173:1700000000", json.getString("canonical_payload"))
        assertEquals("MEQCIGabc123==", json.getString("signature"))
    }

    @Test
    fun testRegisterDeviceRequestSerialization() {
        val request = RegisterDeviceRequest(
            sessionToken = "4f8a8b12c93d",
            deviceId = "ipguard-dev-test-5678",
            deviceName = "Samsung SM-A546E",
            model = "SM-A546E",
            androidVersion = "16",
            publicKeyX509 = "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...",
            securityLevel = "STRONGBOX",
            canonicalPayload = "sess:nonce:origin:1700000000",
            signature = "MEQCIGxyz..."
        )

        val json = JSONObject()
        json.put("session_token", request.sessionToken)
        json.put("device_id", request.deviceId)
        json.put("device_name", request.deviceName)
        json.put("model", request.model)
        json.put("android_version", request.androidVersion)
        json.put("public_key_x509", request.publicKeyX509)
        json.put("security_level", request.securityLevel)
        json.put("canonical_payload", request.canonicalPayload)
        json.put("signature", request.signature)

        assertEquals("4f8a8b12c93d", json.getString("session_token"))
        assertEquals("ipguard-dev-test-5678", json.getString("device_id"))
        assertEquals("STRONGBOX", json.getString("security_level"))
    }

    @Test
    fun testSessionStatusDtoParsing() {
        val rawResponse = """
            {
                "session_token": "token123",
                "status": "SCANNED",
                "session_type": "AUTHENTICATION",
                "expires_at": "2026-11-07T15:00:00Z"
            }
        """.trimIndent()

        val json = JSONObject(rawResponse)
        val dto = SessionStatusDto(
            sessionToken = json.getString("session_token"),
            status = json.getString("status"),
            sessionType = json.getString("session_type"),
            expiresAt = json.getString("expires_at")
        )

        assertEquals("token123", dto.sessionToken)
        assertEquals("SCANNED", dto.status)
        assertEquals("AUTHENTICATION", dto.sessionType)
        assertEquals("2026-11-07T15:00:00Z", dto.expiresAt)
    }

    @Test
    fun testDeviceRegisteredDtoParsing() {
        val rawResponse = """
            {
                "id": "dev_uuid_123",
                "device_id": "ipguard-dev-456",
                "device_name": "Samsung Galaxy A54",
                "status": "enrolled",
                "public_key_fingerprint": "SHA256:abcd"
            }
        """.trimIndent()

        val json = JSONObject(rawResponse)
        val dto = DeviceRegisteredDto(
            id = json.getString("id"),
            deviceId = json.getString("device_id"),
            deviceName = json.getString("device_name"),
            status = json.getString("status"),
            publicKeyFingerprint = json.getString("public_key_fingerprint")
        )

        assertEquals("dev_uuid_123", dto.id)
        assertEquals("ipguard-dev-456", dto.deviceId)
        assertEquals("Samsung Galaxy A54", dto.deviceName)
        assertEquals("enrolled", dto.status)
        assertEquals("SHA256:abcd", dto.publicKeyFingerprint)
    }

    @Test
    fun testApiResultClassification() {
        val success = ApiResult.Success("data")
        val httpError = ApiResult.HttpError(code = 400, errorCode = "bad_request", message = "Bad Request")
        val networkError = ApiResult.NetworkError("Connect timed out")

        assertTrue(success is ApiResult.Success)
        assertEquals("data", success.data)

        assertTrue(httpError is ApiResult.HttpError)
        assertEquals(400, httpError.code)
        assertEquals("bad_request", httpError.errorCode)
        assertEquals("Bad Request", httpError.message)

        assertTrue(networkError is ApiResult.NetworkError)
        assertEquals("Connect timed out", networkError.message)
    }
}
