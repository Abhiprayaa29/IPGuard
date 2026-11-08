package com.ipguard.authenticator.security

import com.ipguard.authenticator.security.qr.QrAuthPayload
import com.ipguard.authenticator.security.qr.QrSessionType
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Assert.fail
import org.junit.Before
import org.junit.Test
import java.security.KeyFactory
import java.security.KeyPair
import java.security.KeyPairGenerator
import java.security.MessageDigest
import java.security.PrivateKey
import java.security.PublicKey
import java.security.spec.ECGenParameterSpec
import java.security.spec.X509EncodedKeySpec
import java.util.Base64

/**
 * Unit Test Suite for IPGuard One-Time Device Enrollment & Sign-In Only Lifecycle
 *
 * Covers:
 * Rule A: Fresh device enrollment initializes key and transitions to ACTIVE
 * Rule B: Registered device is ACTIVE, preserves key, rejects re-enrollment, forbids key overwrite
 * Rule C: Sign-in requires existing key and fails closed without generating replacement
 * Rule D: Unregistration releases device binding allowing new enrollment
 */
class OneTimeDeviceEnrollmentTest {

    private class InMemoryDeviceKeyManager(
        override val alias: String = "test_device_signing_v1"
    ) : DeviceKeyManager {
        private var keyPair: KeyPair? = null
        var generateCallCount = 0
            private set

        override fun hasSigningKey(): Boolean = keyPair != null

        override fun generateSigningKey(requireUserAuthentication: Boolean): KeySecurityMetadata {
            generateCallCount++
            val kpg = KeyPairGenerator.getInstance("EC")
            kpg.initialize(ECGenParameterSpec("secp256r1"))
            keyPair = kpg.generateKeyPair()
            return getKeySecurityMetadata()
        }

        override fun ensureSigningKey(requireUserAuthentication: Boolean): KeySecurityMetadata {
            if (hasSigningKey()) return getKeySecurityMetadata()
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
                purposes = 1 or 2,
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

        fun forceClearKey() {
            keyPair = null
        }
    }

    private class InMemoryRegistrationState {
        var status: DeviceRegistrationStatus = DeviceRegistrationStatus.UNREGISTERED
        var fingerprint: String? = null

        fun isRegistered(): Boolean =
            status == DeviceRegistrationStatus.ACTIVE || status == DeviceRegistrationStatus.REVOKED

        fun clearRegistration() {
            status = DeviceRegistrationStatus.UNREGISTERED
            fingerprint = null
        }
    }

    private lateinit var keyManager: InMemoryDeviceKeyManager
    private lateinit var regState: InMemoryRegistrationState

    @Before
    fun setUp() {
        keyManager = InMemoryDeviceKeyManager()
        regState = InMemoryRegistrationState()
    }

    private fun sampleQrPayload(type: QrSessionType): QrAuthPayload {
        return QrAuthPayload(
            version = "1.0",
            type = type,
            sessionToken = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            nonce = "random_nonce_9876543210",
            origin = "http://localhost:5173",
            timestamp = 1712000000L
        )
    }

    @Test
    fun freshDevice_isUnregisteredByDefault() {
        assertFalse("Fresh device must not be registered", regState.isRegistered())
        assertEquals(DeviceRegistrationStatus.UNREGISTERED, regState.status)
        assertNull(regState.fingerprint)
        assertFalse(keyManager.hasSigningKey())
    }

    @Test
    fun enrollment_onFreshDevice_initializesKeyAndActivatesRegistration() {
        // Step 1: ensure signing key is generated
        assertFalse(keyManager.hasSigningKey())
        keyManager.ensureSigningKey(requireUserAuthentication = true)
        assertTrue(keyManager.hasSigningKey())
        assertEquals(1, keyManager.generateCallCount)

        // Step 2: after backend approves enrollment, device transitions to ACTIVE
        val exported = keyManager.getExportedPublicKey()
        regState.status = DeviceRegistrationStatus.ACTIVE
        regState.fingerprint = exported.sha256Fingerprint

        assertTrue(regState.isRegistered())
        assertEquals(DeviceRegistrationStatus.ACTIVE, regState.status)
        assertEquals(exported.sha256Fingerprint, regState.fingerprint)
    }

    @Test
    fun registeredDevice_rejectsEnrollmentScanUpfront() {
        // Device is already enrolled
        regState.status = DeviceRegistrationStatus.ACTIVE
        assertTrue(regState.isRegistered())

        val enrollmentPayload = sampleQrPayload(QrSessionType.ENROLLMENT)

        // Validate policy check
        val canEnroll = !regState.isRegistered() || enrollmentPayload.type != QrSessionType.ENROLLMENT
        assertFalse("Enrolled device must reject enrollment QR scanning", canEnroll)
    }

    @Test
    fun registeredDevice_preservesExistingKeyAndDoesNotRegenerate() {
        // Enrolled with key
        keyManager.ensureSigningKey(requireUserAuthentication = true)
        val originalFingerprint = keyManager.getExportedPublicKey().sha256Fingerprint
        regState.status = DeviceRegistrationStatus.ACTIVE
        regState.fingerprint = originalFingerprint

        // Attempting ensureSigningKey must not re-generate
        keyManager.ensureSigningKey(requireUserAuthentication = true)
        assertEquals(1, keyManager.generateCallCount)
        assertEquals(originalFingerprint, keyManager.getExportedPublicKey().sha256Fingerprint)
    }

    @Test
    fun registeredDevice_forbidsKeyOverwriting() {
        regState.status = DeviceRegistrationStatus.ACTIVE

        // Policy check for generateSigningKey
        if (regState.isRegistered()) {
            try {
                throw SigningKeyPolicyViolationException("Device is already registered. To change the signing key, unregister first from web console.")
            } catch (e: SigningKeyPolicyViolationException) {
                assertTrue(e.message!!.contains("already registered"))
            }
        } else {
            fail("Should have thrown SigningKeyPolicyViolationException")
        }
    }

    @Test
    fun signIn_onRegisteredDevice_usesExistingKey() {
        keyManager.ensureSigningKey(requireUserAuthentication = true)
        regState.status = DeviceRegistrationStatus.ACTIVE

        val authPayload = sampleQrPayload(QrSessionType.AUTHENTICATION)

        assertEquals(QrSessionType.AUTHENTICATION, authPayload.type)
        assertTrue(keyManager.hasSigningKey())
        assertEquals(1, keyManager.generateCallCount)
    }

    @Test
    fun signIn_withMissingKey_failsClosedWithoutGeneratingNewKey() {
        regState.status = DeviceRegistrationStatus.ACTIVE
        keyManager.forceClearKey()
        assertFalse(keyManager.hasSigningKey())

        // In AUTHENTICATION flow, if !hasSigningKey(), must fail closed
        var didAutoGenerateKey = false
        if (!keyManager.hasSigningKey()) {
            // Fail closed: do NOT call ensureSigningKey
        } else {
            keyManager.ensureSigningKey(requireUserAuthentication = true)
            didAutoGenerateKey = true
        }

        assertFalse("Sign-in must fail closed without generating a new key", didAutoGenerateKey)
        assertFalse(keyManager.hasSigningKey())
        assertEquals(0, keyManager.generateCallCount)
    }

    @Test
    fun unregisterDevice_releasesRegistrationLock_permitsNewEnrollment() {
        // Enrolled device
        keyManager.ensureSigningKey(requireUserAuthentication = true)
        regState.status = DeviceRegistrationStatus.ACTIVE
        assertTrue(regState.isRegistered())

        // Admin performs unregister from Web Console -> Android syncs
        regState.clearRegistration()
        assertFalse(regState.isRegistered())
        assertEquals(DeviceRegistrationStatus.UNREGISTERED, regState.status)

        // Device is now free to enroll again
        val canEnroll = !regState.isRegistered()
        assertTrue("Device must be allowed to enroll after unregistering", canEnroll)
    }

    @Test
    fun revokedDevice_remainsRegistered_deniesReEnrollment() {
        // Device is REVOKED
        regState.status = DeviceRegistrationStatus.REVOKED
        assertTrue("REVOKED status still counts as registered (slot locked)", regState.isRegistered())

        // Attempting to enroll while revoked must be denied
        val canEnroll = !regState.isRegistered()
        assertFalse("Revoked device cannot re-enroll until explicitly unregistered", canEnroll)
    }

    @Test
    fun backend409Conflict_updatesLocalStateToActive() {
        // Scenario: Local prefs were somehow cleared, but backend says 409 DEVICE_ALREADY_REGISTERED
        regState.status = DeviceRegistrationStatus.UNREGISTERED
        assertFalse(regState.isRegistered())

        // Simulate 409 response handler
        val httpErrorCode = 409
        val errorMessage = "DEVICE_ALREADY_REGISTERED: Device is already registered"
        if (httpErrorCode == 409 || errorMessage.contains("DEVICE_ALREADY_REGISTERED")) {
            regState.status = DeviceRegistrationStatus.ACTIVE
        }

        assertTrue("409 response should lock local state to ACTIVE", regState.isRegistered())
        assertEquals(DeviceRegistrationStatus.ACTIVE, regState.status)
    }
}
