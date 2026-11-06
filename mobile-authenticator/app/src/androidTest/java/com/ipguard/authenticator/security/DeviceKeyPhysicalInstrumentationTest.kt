package com.ipguard.authenticator.security

import android.content.Context
import android.os.Build
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyInfo
import android.security.keystore.KeyProperties
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.FixMethodOrder
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.runners.MethodSorters
import java.security.KeyFactory
import java.security.KeyPairGenerator
import java.security.KeyStore
import java.security.PrivateKey
import java.security.spec.ECGenParameterSpec
import java.security.spec.X509EncodedKeySpec
import java.util.Base64

@RunWith(AndroidJUnit4::class)
@FixMethodOrder(MethodSorters.NAME_ASCENDING)
class DeviceKeyPhysicalInstrumentationTest {

    private val testAlias = "ipguard_device_signing_test_v1"
    private lateinit var keyManager: AndroidKeystoreDeviceKeyManager
    private lateinit var context: Context

    @Before
    fun setUp() {
        context = ApplicationProvider.getApplicationContext()
        keyManager = AndroidKeystoreDeviceKeyManager(testAlias)
    }

    @Test
    fun test01_KA01_GenerateSigningKeyOnPhysicalKeystore() {
        // Clean any prior leftover test key
        keyManager.deleteSigningKey()

        // Generate key on physical AndroidKeyStore
        val metadata = keyManager.generateSigningKey(requireUserAuthentication = false)
        assertNotNull(metadata)
        assertEquals(testAlias, metadata.alias)
        assertEquals("EC", metadata.algorithm)
        assertEquals(256, metadata.keySize)
        assertEquals("secp256r1", metadata.curve)
        assertTrue("Digests must include SHA-256", metadata.digests.contains("SHA-256"))
        
        println("PHYSICAL_EVIDENCE: KA-01 generated key successfully. SecurityLevel=${metadata.securityLevel.label}, isInsideSecureHardware=${metadata.isInsideSecureHardware}")
    }

    @Test
    fun test02_KA02_CheckKeyAvailability() {
        val exists = keyManager.hasSigningKey()
        assertTrue("Key must exist in Android Keystore", exists)
        println("PHYSICAL_EVIDENCE: KA-02 hasSigningKey=$exists")
    }

    @Test
    fun test03_KA03_Idempotency() {
        val initialKey = keyManager.getExportedPublicKey()
        val initialFingerprint = initialKey.sha256Fingerprint

        // Call ensureSigningKey (idempotent call)
        val metadata = keyManager.ensureSigningKey(requireUserAuthentication = false)
        assertNotNull(metadata)

        val subsequentKey = keyManager.getExportedPublicKey()
        assertEquals(
            "Fingerprint must match exactly across idempotent initialization",
            initialFingerprint,
            subsequentKey.sha256Fingerprint
        )
        assertEquals(initialKey.base64Encoded, subsequentKey.base64Encoded)
        println("PHYSICAL_EVIDENCE: KA-03 Idempotency confirmed. Fingerprint=$initialFingerprint")
    }

    @Test
    fun test04_KA04_PersistenceAcrossInstances() {
        val existingFingerprint = keyManager.getExportedPublicKey().sha256Fingerprint

        // Instantiate fresh manager to simulate app process restart reading Keystore
        val freshManager = AndroidKeystoreDeviceKeyManager(testAlias)
        assertTrue("Fresh manager instance must find key in Android Keystore", freshManager.hasSigningKey())

        val reloadedKey = freshManager.getExportedPublicKey()
        assertEquals(
            "Reloaded key fingerprint must match original",
            existingFingerprint,
            reloadedKey.sha256Fingerprint
        )
        println("PHYSICAL_EVIDENCE: KA-04 Persistence confirmed across manager reload. Fingerprint=$existingFingerprint")
    }

    @Test
    fun test05_KA05_ExportPublicKeyX509Base64() {
        val exported = keyManager.getExportedPublicKey()
        assertNotNull(exported)
        assertEquals("X.509", exported.format)
        assertEquals("EC", exported.algorithm)
        assertEquals(testAlias, exported.alias)

        val b64 = exported.base64Encoded
        assertFalse("Base64 must not contain newlines", b64.contains("\n"))
        assertFalse("Base64 must not contain carriage returns", b64.contains("\r"))
        assertTrue("Base64 length must be reasonable for P-256 SubjectPublicKeyInfo", b64.length in 120..140)

        val fp = exported.sha256Fingerprint
        assertTrue("Fingerprint must match colon-delimited hex format", fp.matches(Regex("^([0-9A-F]{2}:){31}[0-9A-F]{2}$")))
        println("PHYSICAL_EVIDENCE: KA-05 Exported public key b64 length=${b64.length}, fingerprint=$fp")
    }

    @Test
    fun test06_KA06_PublicKeyRoundtripParsing() {
        val exported = keyManager.getExportedPublicKey()
        val success = keyManager.validatePublicKeyParsing(exported.base64Encoded)
        assertTrue("KeyFactory must successfully reparse exported Base64 X.509 bytes", success)
        println("PHYSICAL_EVIDENCE: KA-06 Reparsing validated successfully via standard KeyFactory('EC')")
    }

    @Test
    fun test07_KA07_PrivateKeyNonExportabilityOnHardware() {
        val privateKey = keyManager.getPrivateKey()
        assertNotNull(privateKey)
        
        // CRITICAL: On real Android Keystore, privateKey.encoded MUST be null!
        val encodedBytes = privateKey.encoded
        assertNull("CRITICAL SECURITY AUDIT: privateKey.encoded must be NULL in Android Keystore!", encodedBytes)
        
        val isNonExportable = keyManager.verifyPrivateKeyNonExportable()
        assertTrue("verifyPrivateKeyNonExportable() must return true", isNonExportable)
        println("PHYSICAL_EVIDENCE: KA-07 Private key class=${privateKey.javaClass.name}, encodedBytes=$encodedBytes (strictly null, non-exportable)")
    }

    @Test
    fun test08_KA08_KeyInfoInspectionOnPhysicalHardware() {
        val metadata = keyManager.getKeySecurityMetadata()
        assertNotNull(metadata)
        assertEquals("EC", metadata.algorithm)
        assertEquals(256, metadata.keySize)
        assertTrue(metadata.digests.contains("SHA-256"))

        val privateKey = keyManager.getPrivateKey()
        val factory = KeyFactory.getInstance(privateKey.algorithm, "AndroidKeyStore")
        val keyInfo = factory.getKeySpec(privateKey, KeyInfo::class.java)

        val securityLevelStr = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            when (keyInfo.securityLevel) {
                KeyProperties.SECURITY_LEVEL_STRONGBOX -> "STRONGBOX"
                KeyProperties.SECURITY_LEVEL_TRUSTED_ENVIRONMENT -> "TRUSTED_ENVIRONMENT"
                KeyProperties.SECURITY_LEVEL_SOFTWARE -> "SOFTWARE"
                else -> "UNKNOWN"
            }
        } else {
            "API < 31"
        }

        @Suppress("DEPRECATION")
        val isInsideHardware = keyInfo.isInsideSecureHardware

        println("PHYSICAL_EVIDENCE: KA-08 KeyInfo on ${Build.MANUFACTURER} ${Build.MODEL} (SDK ${Build.VERSION.SDK_INT}):")
        println("  securityLevel=$securityLevelStr (int=${if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) keyInfo.securityLevel else -1})")
        println("  isInsideSecureHardware=$isInsideHardware")
        println("  keySize=${keyInfo.keySize}")
        println("  purposes=${keyInfo.purposes}")
        println("  digests=${keyInfo.digests.joinToString()}")

        assertTrue("Key must have positive key size", metadata.keySize == 256)
    }

    @Test
    fun test09_KA09_UserAuthenticationPolicyInspection() {
        val metadata = keyManager.getKeySecurityMetadata()
        println("PHYSICAL_EVIDENCE: KA-09 userAuthenticationRequired=${metadata.userAuthenticationRequired}, duration=${metadata.userAuthenticationValidityDurationSeconds}")
    }

    @Test
    fun test10_KA10_ExplicitKeyDeletion() {
        val deleted = keyManager.deleteSigningKey()
        assertTrue("deleteSigningKey() must return true", deleted)

        val existsAfter = keyManager.hasSigningKey()
        assertFalse("Key must NOT exist in Keystore after deletion", existsAfter)
        println("PHYSICAL_EVIDENCE: KA-10 Explicit key deletion confirmed. hasSigningKey=$existsAfter")
    }

    @Test
    fun test11_PhysicalDeviceBiometricAndLockScreenInspection() {
        val km = context.getSystemService(Context.KEYGUARD_SERVICE) as? android.app.KeyguardManager
        val isDeviceSecure = km?.isDeviceSecure ?: false
        val isKeyguardSecure = km?.isKeyguardSecure ?: false

        println("PHYSICAL_EVIDENCE: LockScreen Inspection:")
        println("  isDeviceSecure=$isDeviceSecure")
        println("  isKeyguardSecure=$isKeyguardSecure")

        // Test generation with user authentication required on physical device
        val authTestAlias = "ipguard_user_auth_test_key"
        val authManager = AndroidKeystoreDeviceKeyManager(authTestAlias)
        try {
            authManager.deleteSigningKey()
        } catch (_: Throwable) {}

        var authKeyGenerated = false
        var authKeyError: String? = null
        try {
            val meta = authManager.generateSigningKey(requireUserAuthentication = true)
            authKeyGenerated = true
            println("PHYSICAL_EVIDENCE: User-authenticated key generation SUCCEEDED. SecurityLevel=${meta.securityLevel.label}, userAuthRequired=${meta.userAuthenticationRequired}")
            authManager.deleteSigningKey()
        } catch (e: Throwable) {
            authKeyError = "${e.javaClass.simpleName}: ${e.message}"
            println("PHYSICAL_EVIDENCE: User-authenticated key generation result: $authKeyError")
        }
    }

    @Test
    fun test12_ProductionKeyLifecycleAndPersistence() {
        val prodAlias = DeviceKeyManager.KEY_ALIAS
        val prodManager = AndroidKeystoreDeviceKeyManager(prodAlias)

        // Ensure key is created with user authentication required = true
        val meta1 = prodManager.ensureSigningKey(requireUserAuthentication = true)
        assertNotNull(meta1)
        assertTrue("Production key must exist in Keystore", prodManager.hasSigningKey())
        assertTrue("Production key must require user authentication", meta1.userAuthenticationRequired)
        assertEquals("EC", meta1.algorithm)
        assertEquals(256, meta1.keySize)

        val pubKey1 = prodManager.getExportedPublicKey()
        val fp1 = pubKey1.sha256Fingerprint

        // Verify non-exportability of production private key
        val privateKey = prodManager.getPrivateKey()
        assertNull("Production private key must be strictly non-exportable", privateKey.encoded)
        assertTrue("verifyPrivateKeyNonExportable must return true", prodManager.verifyPrivateKeyNonExportable())

        // Test idempotency on production key
        val meta2 = prodManager.ensureSigningKey(requireUserAuthentication = true)
        val pubKey2 = prodManager.getExportedPublicKey()
        assertEquals("Production key fingerprint must be identical across ensureSigningKey calls", fp1, pubKey2.sha256Fingerprint)

        println("PHYSICAL_EVIDENCE: Production key '${prodAlias}' successfully established in Keystore.")
        println("  Fingerprint=$fp1")
        println("  SecurityLevel=${meta1.securityLevel.label}")
        println("  userAuthenticationRequired=${meta1.userAuthenticationRequired}")
        println("  isInsideSecureHardware=${meta1.isInsideSecureHardware}")
        println("  privateKeyNonExportable=true")
    }
}
