package com.ipguard.authenticator.security

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.security.KeyFactory
import java.security.KeyPairGenerator
import java.security.MessageDigest
import java.security.interfaces.ECPublicKey
import java.security.spec.ECGenParameterSpec
import java.security.spec.X509EncodedKeySpec
import java.util.Base64

class ExportedPublicKeyTest {

    @Test
    fun testEcP256PublicKeyEncodingAndParsing() {
        val keyPairGenerator = KeyPairGenerator.getInstance("EC")
        keyPairGenerator.initialize(ECGenParameterSpec("secp256r1"))
        val keyPair = keyPairGenerator.generateKeyPair()

        val rawPublicKey = keyPair.public
        assertNotNull(rawPublicKey)
        assertEquals("EC", rawPublicKey.algorithm)
        assertEquals("X.509", rawPublicKey.format)

        val rawBytes = rawPublicKey.encoded
        assertNotNull(rawBytes)

        val base64 = Base64.getEncoder().encodeToString(rawBytes)
        assertFalse("Base64 string must not contain newlines", base64.contains("\n"))
        assertFalse("Base64 string must not contain carriage returns", base64.contains("\r"))

        // SHA-256 fingerprint
        val digest = MessageDigest.getInstance("SHA-256")
        val fingerprintBytes = digest.digest(rawBytes)
        val fingerprint = fingerprintBytes.joinToString(":") { "%02X".format(it) }
        assertTrue("Fingerprint must match standard colon-delimited hex format", fingerprint.matches(Regex("^([0-9A-F]{2}:){31}[0-9A-F]{2}$")))

        // Test roundtrip parsing with KeyFactory
        val decodedBytes = Base64.getDecoder().decode(base64)
        val keySpec = X509EncodedKeySpec(decodedBytes)
        val keyFactory = KeyFactory.getInstance("EC")
        val parsedPublicKey = keyFactory.generatePublic(keySpec)

        assertNotNull(parsedPublicKey)
        assertTrue(parsedPublicKey is ECPublicKey)
        assertEquals("EC", parsedPublicKey.algorithm)
        assertEquals(rawPublicKey, parsedPublicKey)
    }

    @Test
    fun testKeySecurityLevelLabels() {
        assertEquals("Software-backed", KeySecurityLevel.SOFTWARE.label)
        assertEquals("Trusted Execution Environment (TEE)", KeySecurityLevel.TRUSTED_ENVIRONMENT.label)
        assertEquals("StrongBox Keymaster", KeySecurityLevel.STRONGBOX.label)
        assertEquals("Unknown / unavailable", KeySecurityLevel.UNKNOWN.label)
    }

    @Test
    fun testDeviceKeyExceptions() {
        val baseEx = DeviceKeyException("Base error")
        assertEquals("Base error", baseEx.message)

        val notFoundEx: Any = DeviceKeyNotFoundException("Key not found")
        assertTrue(notFoundEx is DeviceKeyException)

        val lockEx: Any = DeviceLockScreenRequiredException("Lock screen needed")
        assertTrue(lockEx is DeviceKeyException)

        val violationEx: Any = KeySecurityViolationException("Security violation")
        assertTrue(violationEx is DeviceKeyException)
    }
}
