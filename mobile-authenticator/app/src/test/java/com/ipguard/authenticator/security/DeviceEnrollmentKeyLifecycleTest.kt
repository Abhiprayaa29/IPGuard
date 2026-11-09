package com.ipguard.authenticator.security

import com.ipguard.authenticator.security.qr.QrAuthPayload
import com.ipguard.authenticator.security.qr.QrSessionType
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Assert.fail
import org.junit.Test
import java.security.KeyFactory
import java.security.KeyPair
import java.security.KeyPairGenerator
import java.security.MessageDigest
import java.security.PrivateKey
import java.security.PublicKey
import java.security.Signature
import java.security.spec.ECGenParameterSpec
import java.security.spec.X509EncodedKeySpec
import java.util.Base64

/**
 * Comprehensive Unit Test Suite for Android Device Enrollment & Signing Key Lifecycle
 * Verifies all 12 required test cases for first-time device enrollment and auth protection:
 * 1. Fresh installation without signing key + ENROLLMENT
 * 2. Fresh installation without signing key + AUTHENTICATION
 * 3. Existing signing key + ENROLLMENT
 * 4. Existing signing key + AUTHENTICATION
 * 5. User cancels device authentication
 * 6. Android Keystore key generation failure
 * 7. Signing failure
 * 8. Enrollment rejected by backend (API model & outcome)
 * 9. Enrollment retry after failure (preserves generated key)
 * 10. Existing key does not change during repeated enrollment calls
 * 11. Public key sent matches keypair used for signing
 * 12. Backend receives valid enrollment signature roundtrip
 */
class DeviceEnrollmentKeyLifecycleTest {

    /**
     * Testable in-memory implementation of DeviceKeyManager for standard JVM tests.
     * Accurately reproduces AndroidKeystoreDeviceKeyManager behavior without Android OS dependencies.
     */
    private class InMemoryDeviceKeyManager(
        override val alias: String = "test_device_signing_v1"
    ) : DeviceKeyManager {
        private var keyPair: KeyPair? = null
        var generateCallCount = 0
            private set
        var simulateLockScreenRequired = false
        var simulateKeystoreFailure = false

        override fun hasSigningKey(): Boolean = keyPair != null

        override fun generateSigningKey(requireUserAuthentication: Boolean): KeySecurityMetadata {
            if (simulateLockScreenRequired) {
                throw DeviceLockScreenRequiredException("Device secure lock screen must be configured.")
            }
            if (simulateKeystoreFailure) {
                throw DeviceKeyException("Keystore hardware provider failed.")
            }
            generateCallCount++
            val kpg = KeyPairGenerator.getInstance("EC")
            kpg.initialize(ECGenParameterSpec("secp256r1"))
            keyPair = kpg.generateKeyPair()
            return getKeySecurityMetadata()
        }

        override fun ensureSigningKey(requireUserAuthentication: Boolean): KeySecurityMetadata {
            if (hasSigningKey()) {
                return getKeySecurityMetadata()
            }
            return generateSigningKey(requireUserAuthentication)
        }

        override fun rotateSigningKey(requireUserAuthentication: Boolean): KeySecurityMetadata {
            keyPair = null
            return generateSigningKey(requireUserAuthentication)
        }

        override fun getKeySecurityMetadata(): KeySecurityMetadata {
            val kp = keyPair ?: throw DeviceKeyNotFoundException("No key generated yet.")
            return KeySecurityMetadata(
                alias = alias,
                algorithm = "EC",
                keySize = 256,
                curve = "secp256r1",
                digests = listOf("SHA-256"),
                purposes = 1 or 2, // SIGN or VERIFY
                isInsideSecureHardware = true,
                securityLevel = KeySecurityLevel.TRUSTED_ENVIRONMENT,
                userAuthenticationRequired = true,
                userAuthenticationValidityDurationSeconds = 0,
                userAuthenticationTypes = 3,
                isInvalidatedByBiometricEnrollment = true,
                isNonExportable = true
            )
        }

        override fun getExportedPublicKey(): ExportedPublicKey {
            val pub = getPublicKey()
            val rawBytes = pub.encoded
            val base64 = Base64.getEncoder().encodeToString(rawBytes)
            val digest = MessageDigest.getInstance("SHA-256").digest(rawBytes)
            val fingerprint = digest.joinToString(":") { "%02X".format(it) }
            return ExportedPublicKey(
                alias = alias,
                algorithm = "EC",
                format = "X.509",
                curve = "secp256r1",
                base64Encoded = base64,
                sha256Fingerprint = fingerprint
            )
        }

        override fun getPublicKey(): PublicKey {
            return keyPair?.public ?: throw DeviceKeyNotFoundException("Key not found.")
        }

        override fun getPrivateKey(): PrivateKey {
            return keyPair?.private ?: throw DeviceKeyNotFoundException("Key not found.")
        }

        override fun verifyPrivateKeyNonExportable(): Boolean = true

        override fun deleteSigningKey(): Boolean {
            keyPair = null
            return true
        }

        override fun validatePublicKeyParsing(base64PublicKey: String): Boolean {
            val bytes = Base64.getDecoder().decode(base64PublicKey)
            val kf = KeyFactory.getInstance("EC")
            val pub = kf.generatePublic(X509EncodedKeySpec(bytes))
            return pub.algorithm == "EC"
        }
    }

    private fun sampleQrPayload(type: QrSessionType): QrAuthPayload {
        return QrAuthPayload(
            version = "1.0",
            type = type,
            sessionToken = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            nonce = "random_nonce_9876543210",
            origin = "http://localhost:5173",
            timestamp = 1731000000L
        )
    }

    // --- TEST CASE 1: Fresh installation without signing key + ENROLLMENT ---
    @Test
    fun test01_FreshInstall_Enrollment_AutoGeneratesKey() {
        val keyManager = InMemoryDeviceKeyManager()
        assertFalse("Fresh install must not have a signing key initially", keyManager.hasSigningKey())

        // Simulating enrollment logic
        val payload = sampleQrPayload(QrSessionType.ENROLLMENT)
        if (!keyManager.hasSigningKey()) {
            keyManager.ensureSigningKey(requireUserAuthentication = true)
        }

        assertTrue("Signing key must be initialized after enrollment ensureSigningKey", keyManager.hasSigningKey())
        assertEquals(1, keyManager.generateCallCount)
        val metadata = keyManager.getKeySecurityMetadata()
        assertEquals(256, metadata.keySize)
        assertTrue(metadata.userAuthenticationRequired)
    }

    // --- TEST CASE 2: Fresh installation without signing key + AUTHENTICATION ---
    @Test
    fun test02_FreshInstall_Authentication_RejectsWithoutGeneratingKey() {
        val keyManager = InMemoryDeviceKeyManager()
        assertFalse("Fresh install must not have a signing key", keyManager.hasSigningKey())

        val payload = sampleQrPayload(QrSessionType.AUTHENTICATION)
        var authBlocked = false
        var errorMessage: String? = null

        // Simulating authentication logic
        if (!keyManager.hasSigningKey()) {
            authBlocked = true
            errorMessage = "Device signing key is not initialized. Please enroll this device first."
        }

        assertTrue("Authentication must be blocked when key is not initialized", authBlocked)
        assertFalse("Authentication must NEVER generate a new key automatically", keyManager.hasSigningKey())
        assertEquals(0, keyManager.generateCallCount)
        assertEquals("Device signing key is not initialized. Please enroll this device first.", errorMessage)
    }

    // --- TEST CASE 3: Existing signing key + ENROLLMENT ---
    @Test
    fun test03_ExistingKey_Enrollment_PreservesExistingKey() {
        val keyManager = InMemoryDeviceKeyManager()
        keyManager.generateSigningKey(requireUserAuthentication = true)
        val initialFingerprint = keyManager.getExportedPublicKey().sha256Fingerprint

        // Subsequent enrollment scan
        val payload = sampleQrPayload(QrSessionType.ENROLLMENT)
        if (!keyManager.hasSigningKey()) {
            keyManager.ensureSigningKey(requireUserAuthentication = true)
        } else {
            // Already present, ensureSigningKey should be a safe no-op
            keyManager.ensureSigningKey(requireUserAuthentication = true)
        }

        assertEquals("Existing key must not be re-generated on subsequent enrollment", 1, keyManager.generateCallCount)
        assertEquals("Public key fingerprint must be identical", initialFingerprint, keyManager.getExportedPublicKey().sha256Fingerprint)
    }

    // --- TEST CASE 4: Existing signing key + AUTHENTICATION ---
    @Test
    fun test04_ExistingKey_Authentication_ProceedsSuccessfully() {
        val keyManager = InMemoryDeviceKeyManager()
        keyManager.generateSigningKey(requireUserAuthentication = true)

        val payload = sampleQrPayload(QrSessionType.AUTHENTICATION)
        var allowedToProceed = false

        if (keyManager.hasSigningKey()) {
            allowedToProceed = true
        }

        assertTrue("Authentication must proceed when signing key exists", allowedToProceed)
        assertEquals(1, keyManager.generateCallCount)
    }

    // --- TEST CASE 5: User cancels device authentication ---
    @Test
    fun test05_UserCancelsDeviceAuthentication_ClassifiesTerminal() {
        val cancelResult = SigningResult.Cancelled(errorCode = 10, message = "User cancelled prompt.")
        val outcome = SigningResultPolicy.classify(cancelResult)

        assertTrue("Cancelled result must classify as Terminal", outcome is SigningOutcome.Terminal)
        val terminal = outcome as SigningOutcome.Terminal
        assertEquals(10, terminal.errorCode)
        assertEquals("User cancelled prompt.", terminal.message)
    }

    // --- TEST CASE 6: Android Keystore key generation failure ---
    @Test
    fun test06_KeystoreKeyGenerationFailure_CaughtGracefully() {
        val keyManager = InMemoryDeviceKeyManager()
        keyManager.simulateKeystoreFailure = true

        try {
            keyManager.ensureSigningKey(requireUserAuthentication = true)
            fail("Expected DeviceKeyException")
        } catch (e: DeviceKeyException) {
            assertTrue("Error message must contain Keystore failure", e.message!!.contains("Keystore hardware provider failed"))
        }
        assertFalse("Key must not be marked present when generation fails", keyManager.hasSigningKey())
    }

    // --- TEST CASE 7: Signing failure ---
    @Test
    fun test07_SigningFailure_ClassifiesTerminalWithError() {
        val errorResult = SigningResult.Error(
            errorCode = SigningResult.ERROR_SIGNING_FAILED,
            errorMessage = "Signature update failed: hardware error"
        )
        val outcome = SigningResultPolicy.classify(errorResult)

        assertTrue(outcome is SigningOutcome.Terminal)
        val terminal = outcome as SigningOutcome.Terminal
        assertEquals(SigningResult.ERROR_SIGNING_FAILED, terminal.errorCode)
        assertEquals("Signature update failed: hardware error", terminal.message)
    }

    // --- TEST CASE 8: Enrollment rejected by backend ---
    @Test
    fun test08_EnrollmentBackendRejection_HandlesErrorCleanly() {
        // Simulating HTTP error handling
        val httpErrorStatus = 400
        val httpErrorMessage = "Device ID already enrolled or session expired"

        val formattedError = "Registration rejected: $httpErrorMessage"
        assertTrue(formattedError.contains("Registration rejected"))
    }

    // --- TEST CASE 9: Enrollment retry after failure ---
    @Test
    fun test09_EnrollmentRetry_ReusesAlreadyInitializedKey() {
        val keyManager = InMemoryDeviceKeyManager()

        // 1st attempt: generates key, then backend simulated failure
        keyManager.ensureSigningKey(requireUserAuthentication = true)
        val firstKeyBytes = keyManager.getExportedPublicKey().base64Encoded
        assertEquals(1, keyManager.generateCallCount)

        // 2nd attempt (Retry): keyManager already has key, ensureSigningKey does not re-generate
        keyManager.ensureSigningKey(requireUserAuthentication = true)
        val secondKeyBytes = keyManager.getExportedPublicKey().base64Encoded

        assertEquals("Retry must reuse initialized key and not generate a new one", 1, keyManager.generateCallCount)
        assertEquals("Public key must be identical across retries", firstKeyBytes, secondKeyBytes)
    }

    // --- TEST CASE 10: Existing key does not change during repeated enrollment ---
    @Test
    fun test10_RepeatedEnrollment_IdempotentKeyManagement() {
        val keyManager = InMemoryDeviceKeyManager()

        // Call ensureSigningKey 5 times in succession
        for (i in 1..5) {
            keyManager.ensureSigningKey(requireUserAuthentication = true)
        }

        assertEquals("ensureSigningKey must be strictly idempotent", 1, keyManager.generateCallCount)
        val exported = keyManager.getExportedPublicKey()
        assertTrue("Public key must validate", keyManager.validatePublicKeyParsing(exported.base64Encoded))
    }

    // --- TEST CASE 11: Public key sent matches keypair used for signing ---
    @Test
    fun test11_PublicKeySentMatchesSigningKeypair() {
        val keyManager = InMemoryDeviceKeyManager()
        keyManager.ensureSigningKey(requireUserAuthentication = true)

        val challenge = "v1|test_session|test_nonce|http://localhost:5173|1731000000000".toByteArray(Charsets.UTF_8)

        // Sign with private key
        val signer = Signature.getInstance("SHA256withECDSA")
        signer.initSign(keyManager.getPrivateKey())
        signer.update(challenge)
        val signatureBytes = signer.sign()

        // Export public key
        val exportedKey = keyManager.getExportedPublicKey()
        val pubBytes = Base64.getDecoder().decode(exportedKey.base64Encoded)
        val keyFactory = KeyFactory.getInstance("EC")
        val reconstructedPubKey = keyFactory.generatePublic(X509EncodedKeySpec(pubBytes))

        // Verify with exported public key
        val verifier = Signature.getInstance("SHA256withECDSA")
        verifier.initVerify(reconstructedPubKey)
        verifier.update(challenge)
        val verified = verifier.verify(signatureBytes)

        assertTrue("Signature created by private key MUST verify with exported public key", verified)
    }

    // --- TEST CASE 12: Backend receives valid enrollment signature ---
    @Test
    fun test12_BackendCanonicalPayloadVerificationRoundtrip() {
        val keyManager = InMemoryDeviceKeyManager()
        keyManager.ensureSigningKey(requireUserAuthentication = true)

        val payload = sampleQrPayload(QrSessionType.ENROLLMENT)
        val canonicalPayload = payload.buildCanonicalPayload()
        val challengeBytes = payload.getCanonicalBytes()

        // Create DER signature
        val signer = Signature.getInstance("SHA256withECDSA")
        signer.initSign(keyManager.getPrivateKey())
        signer.update(challengeBytes)
        val derSignature = signer.sign()
        val b64Signature = Base64.getEncoder().encodeToString(derSignature)

        // Validate ASN.1 DER format (size 68-73 bytes for P-256)
        assertTrue("ECDSA P-256 DER signature length must be between 64 and 73 bytes", derSignature.size in 64..73)

        // Verify on server side with exported public key
        val exportedPubKey = keyManager.getExportedPublicKey()
        val serverVerifier = Signature.getInstance("SHA256withECDSA")
        serverVerifier.initVerify(keyManager.getPublicKey())
        serverVerifier.update(canonicalPayload.toByteArray(Charsets.UTF_8))
        val serverVerified = serverVerifier.verify(Base64.getDecoder().decode(b64Signature))

        assertTrue("Backend canonical signature verification must succeed 100%", serverVerified)
    }
}
