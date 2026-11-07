package com.ipguard.authenticator.security.qr

import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Test

class CanonicalPayloadContractTest {

    @Test
    fun testCanonicalPayloadMatchesBackendFormat() {
        val payload = QrAuthPayload(
            version = "1",
            type = QrSessionType.AUTHENTICATION,
            sessionToken = "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90",
            nonce = "11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff",
            origin = "http://localhost:5173",
            timestamp = 1731000000L
        )

        val expectedString = "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90:11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff:http://localhost:5173:1731000000"
        
        assertEquals(expectedString, payload.buildCanonicalPayload())
        assertArrayEquals(expectedString.toByteArray(Charsets.UTF_8), payload.getCanonicalBytes())
    }

    @Test
    fun testEnrollmentCanonicalPayload() {
        val payload = QrAuthPayload(
            version = "1",
            type = QrSessionType.ENROLLMENT,
            sessionToken = "token_4f8a8b12c93d",
            nonce = "nonce_112233445566",
            origin = "https://admin.ipguard.internal",
            timestamp = 1732000000L
        )

        val expectedString = "token_4f8a8b12c93d:nonce_112233445566:https://admin.ipguard.internal:1732000000"
        assertEquals(expectedString, payload.buildCanonicalPayload())
    }
}
