package com.ipguard.authenticator.security

import android.app.KeyguardManager
import android.content.Context
import android.os.Build
import android.security.keystore.KeyInfo
import android.security.keystore.KeyProperties
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Assert.fail
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import java.security.KeyFactory

@RunWith(AndroidJUnit4::class)
class DeviceKeyPhysicalInstrumentationTest {

    private val testAlias = "ipguard_physical_instrumentation_test_v1"
    private lateinit var keyManager: AndroidKeystoreDeviceKeyManager
    private lateinit var context: Context

    @Before
    fun setUp() {
        context = ApplicationProvider.getApplicationContext()
        keyManager = AndroidKeystoreDeviceKeyManager(testAlias)
        keyManager.deleteSigningKey()
        keyManager.generateSigningKey(requireUserAuthentication = false)
    }

    @After
    fun tearDown() {
        runCatching { keyManager.deleteSigningKey() }
    }

    @Test
    fun test01_KA01_GenerateSigningKeyOnPhysicalKeystore() {
        keyManager.deleteSigningKey()
        val metadata = keyManager.generateSigningKey(requireUserAuthentication = false)

        assertNotNull(metadata)
        assertEquals(testAlias, metadata.alias)
        assertEquals("EC", metadata.algorithm)
        assertEquals(256, metadata.keySize)
        assertEquals("secp256r1", metadata.curve)
        assertTrue("Digests must include SHA-256", metadata.digests.contains("SHA-256"))
        println("PHYSICAL_EVIDENCE: KA-01 securityLevel=${metadata.securityLevel.label}")
    }

    @Test
    fun test02_KA02_CheckKeyAvailability() {
        assertTrue("Test key must exist in Android Keystore", keyManager.hasSigningKey())
    }

    @Test
    fun test03_KA03_Idempotency() {
        val initialKey = keyManager.getExportedPublicKey()
        val metadata = keyManager.ensureSigningKey(requireUserAuthentication = false)
        val subsequentKey = keyManager.getExportedPublicKey()

        assertNotNull(metadata)
        assertEquals(initialKey.sha256Fingerprint, subsequentKey.sha256Fingerprint)
        assertEquals(initialKey.base64Encoded, subsequentKey.base64Encoded)
    }

    @Test
    fun test04_KA04_PersistenceAcrossInstances() {
        val existingFingerprint = keyManager.getExportedPublicKey().sha256Fingerprint
        val freshManager = AndroidKeystoreDeviceKeyManager(testAlias)
        assertTrue("Fresh manager must find the test key", freshManager.hasSigningKey())
        assertEquals(existingFingerprint, freshManager.getExportedPublicKey().sha256Fingerprint)
    }

    @Test
    fun test05_KA05_ExportPublicKeyX509Base64() {
        val exported = keyManager.getExportedPublicKey()

        assertEquals("X.509", exported.format)
        assertEquals("EC", exported.algorithm)
        assertEquals(testAlias, exported.alias)
        assertFalse(exported.base64Encoded.contains("\n"))
        assertFalse(exported.base64Encoded.contains("\r"))
        assertTrue(exported.base64Encoded.length in 120..140)
        assertTrue(
            exported.sha256Fingerprint.matches(Regex("^([0-9A-F]{2}:){31}[0-9A-F]{2}$"))
        )
    }

    @Test
    fun test06_KA06_PublicKeyRoundtripParsing() {
        val exported = keyManager.getExportedPublicKey()
        assertTrue(keyManager.validatePublicKeyParsing(exported.base64Encoded))
    }

    @Test
    fun test07_KA07_PrivateKeyNonExportabilityOnHardware() {
        val privateKey = keyManager.getPrivateKey()

        assertNotNull(privateKey)
        assertNull("Keystore private key encoding must be null", privateKey.encoded)
        assertTrue(keyManager.verifyPrivateKeyNonExportable())
    }

    @Test
    fun test08_KA08_KeyInfoInspectionOnPhysicalHardware() {
        val metadata = keyManager.getKeySecurityMetadata()

        assertEquals("EC", metadata.algorithm)
        assertEquals(256, metadata.keySize)
        assertTrue(metadata.digests.contains("SHA-256"))
        assertTrue(metadata.isNonExportable)

        val privateKey = keyManager.getPrivateKey()
        val factory = KeyFactory.getInstance(privateKey.algorithm, DeviceKeyManager.KEYSTORE_PROVIDER)
        val keyInfo = factory.getKeySpec(privateKey, KeyInfo::class.java)
        @Suppress("DEPRECATION")
        val isInsideSecureHardware = keyInfo.isInsideSecureHardware

        println(
            "PHYSICAL_EVIDENCE: KA-08 ${Build.MANUFACTURER} ${Build.MODEL} " +
                "SDK=${Build.VERSION.SDK_INT}, keySize=${keyInfo.keySize}, " +
                "insideSecureHardware=$isInsideSecureHardware"
        )
    }

    @Test
    fun test09_KA09_UserAuthenticationPolicyInspection() {
        val metadata = keyManager.getKeySecurityMetadata()

        assertFalse(metadata.userAuthenticationRequired)
        println(
            "PHYSICAL_EVIDENCE: KA-09 userAuthRequired=${metadata.userAuthenticationRequired}, " +
                "duration=${metadata.userAuthenticationValidityDurationSeconds}"
        )
    }

    @Test
    fun test10_KA10_ExplicitKeyDeletion() {
        assertTrue(keyManager.deleteSigningKey())
        assertFalse(keyManager.hasSigningKey())
    }

    @Test
    fun test11_UserAuthenticatedKeyGenerationMatchesDeviceSecurity() {
        val keyguardManager = context.getSystemService(Context.KEYGUARD_SERVICE) as? KeyguardManager
        val isDeviceSecure = keyguardManager?.isDeviceSecure == true
        val authTestAlias = "ipguard_user_auth_test_key_v1"
        val authManager = AndroidKeystoreDeviceKeyManager(authTestAlias)
        authManager.deleteSigningKey()

        try {
            if (isDeviceSecure) {
                val metadata = authManager.generateSigningKey(requireUserAuthentication = true)
                assertTrue(metadata.userAuthenticationRequired)
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                    assertTrue(metadata.userAuthenticationTypes != 0)
                }
            } else {
                try {
                    authManager.generateSigningKey(requireUserAuthentication = true)
                    fail("A device without a secure lock screen must not generate an auth key")
                } catch (_: DeviceLockScreenRequiredException) {
                    // Expected fail-closed behavior.
                }
            }
        } finally {
            authManager.deleteSigningKey()
        }
    }

    @Test
    fun test12_KeyRotationAndPolicyValidationStayTestOnly() {
        val rotationAlias = "ipguard_rotation_test_v1"
        val manager = AndroidKeystoreDeviceKeyManager(rotationAlias)

        try {
            manager.deleteSigningKey()
            manager.generateSigningKey(requireUserAuthentication = false)
            val firstFingerprint = manager.getExportedPublicKey().sha256Fingerprint

            assertNotNull(manager.ensureSigningKey(requireUserAuthentication = false))
            assertEquals(firstFingerprint, manager.getExportedPublicKey().sha256Fingerprint)

            manager.rotateSigningKey(requireUserAuthentication = false)
            assertNotEquals(firstFingerprint, manager.getExportedPublicKey().sha256Fingerprint)
            assertTrue(manager.verifyPrivateKeyNonExportable())
            assertNotEquals(DeviceKeyManager.KEY_ALIAS, manager.alias)
        } finally {
            manager.deleteSigningKey()
        }
    }
}
