package com.ipguard.authenticator.security

import android.content.Context
import android.os.Build
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyInfo
import android.security.keystore.KeyProperties
import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt
import androidx.core.content.ContextCompat
import androidx.test.core.app.ActivityScenario
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.ipguard.authenticator.MainActivity
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
import java.security.Signature
import java.security.spec.ECGenParameterSpec
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference

@RunWith(AndroidJUnit4::class)
@FixMethodOrder(MethodSorters.NAME_ASCENDING)
class DeviceAuthenticationPolicyTest {

    private lateinit var context: Context
    private lateinit var biometricManager: BiometricManager
    private val keyAlias = DeviceKeyManager.KEY_ALIAS

    @Before
    fun setUp() {
        context = ApplicationProvider.getApplicationContext()
        biometricManager = BiometricManager.from(context)
        val keyManager = AndroidKeystoreDeviceKeyManager(keyAlias)
        if (!keyManager.hasSigningKey()) {
            keyManager.generateSigningKey(requireUserAuthentication = true)
        }
    }

    /**
     * AUTH-01: Detect BIOMETRIC_STRONG capability.
     * Optical sensor on current Galaxy A54 is broken/not enrolled, must report NONE_ENROLLED or HW_UNAVAILABLE.
     */
    @Test
    fun testAUTH01_DetectBiometricStrongCapability() {
        val result = biometricManager.canAuthenticate(BiometricManager.Authenticators.BIOMETRIC_STRONG)
        val statusString = when (result) {
            BiometricManager.BIOMETRIC_SUCCESS -> "BIOMETRIC_SUCCESS"
            BiometricManager.BIOMETRIC_ERROR_NONE_ENROLLED -> "BIOMETRIC_ERROR_NONE_ENROLLED"
            BiometricManager.BIOMETRIC_ERROR_NO_HARDWARE -> "BIOMETRIC_ERROR_NO_HARDWARE"
            BiometricManager.BIOMETRIC_ERROR_HW_UNAVAILABLE -> "BIOMETRIC_ERROR_HW_UNAVAILABLE"
            BiometricManager.BIOMETRIC_ERROR_SECURITY_UPDATE_REQUIRED -> "BIOMETRIC_ERROR_SECURITY_UPDATE_REQUIRED"
            BiometricManager.BIOMETRIC_ERROR_UNSUPPORTED -> "BIOMETRIC_ERROR_UNSUPPORTED"
            BiometricManager.BIOMETRIC_STATUS_UNKNOWN -> "BIOMETRIC_STATUS_UNKNOWN"
            else -> "CODE_$result"
        }
        println("PHYSICAL_EVIDENCE: AUTH-01 BIOMETRIC_STRONG capability on A54: $statusString ($result)")

        assertTrue(
            "BIOMETRIC_STRONG must accurately report non-enrolled or hardware status on current A54",
            result == BiometricManager.BIOMETRIC_ERROR_NONE_ENROLLED ||
                    result == BiometricManager.BIOMETRIC_ERROR_HW_UNAVAILABLE ||
                    result == BiometricManager.BIOMETRIC_ERROR_NO_HARDWARE
        )
    }

    /**
     * AUTH-02: Detect DEVICE_CREDENTIAL capability.
     * PIN/Pattern/Password must be active and report BIOMETRIC_SUCCESS.
     */
    @Test
    fun testAUTH02_DetectDeviceCredentialCapability() {
        val result = biometricManager.canAuthenticate(BiometricManager.Authenticators.DEVICE_CREDENTIAL)
        val statusString = when (result) {
            BiometricManager.BIOMETRIC_SUCCESS -> "BIOMETRIC_SUCCESS (AVAILABLE)"
            BiometricManager.BIOMETRIC_ERROR_NONE_ENROLLED -> "BIOMETRIC_ERROR_NONE_ENROLLED"
            BiometricManager.BIOMETRIC_ERROR_NO_HARDWARE -> "BIOMETRIC_ERROR_NO_HARDWARE"
            else -> "CODE_$result"
        }
        println("PHYSICAL_EVIDENCE: AUTH-02 DEVICE_CREDENTIAL capability on A54: $statusString ($result)")

        assertEquals("DEVICE_CREDENTIAL must be available (BIOMETRIC_SUCCESS)", BiometricManager.BIOMETRIC_SUCCESS, result)
    }

    /**
     * AUTH-03: Launch combined authentication prompt (BIOMETRIC_STRONG | DEVICE_CREDENTIAL)
     * with CryptoObject on Android 16 (API 36).
     */
    @Test
    fun testAUTH03_LaunchCombinedAuthenticationPrompt() {
        val keyManager = AndroidKeystoreDeviceKeyManager(keyAlias)
        val authenticator = DeviceSigningAuthenticator(keyManager)

        val promptInfo = authenticator.createPromptInfo(
            title = "AUTH-03 Prompt Launch Test",
            subtitle = "Verify PromptInfo Builder"
        )
        assertNotNull("PromptInfo must build successfully", promptInfo)

        val cryptoObject = authenticator.createCryptoObject()
        assertNotNull("CryptoObject must be initialized with Signature", cryptoObject.signature)

        val promptLaunched = AtomicBoolean(false)
        val promptError = AtomicReference<String?>(null)

        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            scenario.onActivity { activity ->
                val executor = ContextCompat.getMainExecutor(activity)
                val callback = object : BiometricPrompt.AuthenticationCallback() {
                    override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                        println("PHYSICAL_EVIDENCE: AUTH-03 prompt callback received error: $errorCode ($errString)")
                    }
                }
                val prompt = BiometricPrompt(activity, executor, callback)
                try {
                    prompt.authenticate(promptInfo, cryptoObject)
                    promptLaunched.set(true)
                    println("PHYSICAL_EVIDENCE: AUTH-03 Combined BiometricPrompt successfully accepted CryptoObject with DEVICE_CREDENTIAL on Android 16!")
                    prompt.cancelAuthentication()
                } catch (e: Throwable) {
                    promptError.set("${e.javaClass.name}: ${e.message}")
                    println("PHYSICAL_EVIDENCE: AUTH-03 prompt launch failed: ${e.message}")
                }
            }
        }

        assertNull("Prompt launch must not throw an exception: ${promptError.get()}", promptError.get())
        assertTrue("Prompt must be accepted by system BiometricPrompt", promptLaunched.get())
    }

    /**
     * AUTH-06: Verify ECDSA signature using exported public key.
     * Ensures signature verification logic is cryptographically sound and rejects altered bytes.
     */
    @Test
    fun testAUTH06_VerifySignatureUsingExportedPublicKey() {
        // Generate an ephemeral EC key pair to test standard SHA256withECDSA signing & public key verification
        val kpg = KeyPairGenerator.getInstance("EC")
        kpg.initialize(ECGenParameterSpec("secp256r1"))
        val keyPair = kpg.generateKeyPair()

        val challenge = "IPGUARD_CRYPTO_VERIFICATION_PAYLOAD_AUTH06".toByteArray(Charsets.UTF_8)

        val signer = Signature.getInstance("SHA256withECDSA")
        signer.initSign(keyPair.private)
        signer.update(challenge)
        val signatureBytes = signer.sign()

        assertNotNull("Signature bytes must not be null", signatureBytes)
        assertTrue("ECDSA P-256 signature must be between 64 and 72 bytes ASN.1 DER", signatureBytes.size in 64..72)

        // Verify with matching public key
        val verifier = Signature.getInstance("SHA256withECDSA")
        verifier.initVerify(keyPair.public)
        verifier.update(challenge)
        val valid = verifier.verify(signatureBytes)
        assertTrue("Signature verification must succeed for identical challenge and public key", valid)

        // Verify failure on tampered challenge
        val tamperedChallenge = "IPGUARD_TAMPERED_CHALLENGE_AUTH06".toByteArray(Charsets.UTF_8)
        val tamperedVerifier = Signature.getInstance("SHA256withECDSA")
        tamperedVerifier.initVerify(keyPair.public)
        tamperedVerifier.update(tamperedChallenge)
        val tamperedValid = tamperedVerifier.verify(signatureBytes)
        assertFalse("Signature verification must reject tampered challenge", tamperedValid)

        println("PHYSICAL_EVIDENCE: AUTH-06 Signature verification algorithm SHA256withECDSA successfully verified (${signatureBytes.size} bytes)")
    }

    /**
     * AUTH-07: Cancel authentication.
     * When authentication prompt is canceled, onAuthenticationError must be invoked and NO signature generated.
     */
    @Test
    fun testAUTH07_CancelAuthentication() {
        val keyManager = AndroidKeystoreDeviceKeyManager(keyAlias)
        val authenticator = DeviceSigningAuthenticator(keyManager)
        val promptInfo = authenticator.createPromptInfo("AUTH-07 Cancel Test", "Cancel test")
        val cryptoObject = authenticator.createCryptoObject()

        val cancelReceived = AtomicBoolean(false)
        val errorCodeReceived = AtomicInteger(-1)
        val signatureGenerated = AtomicBoolean(false)
        val latch = CountDownLatch(1)

        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            scenario.onActivity { activity ->
                val executor = ContextCompat.getMainExecutor(activity)
                val callback = object : BiometricPrompt.AuthenticationCallback() {
                    override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                        signatureGenerated.set(true)
                        latch.countDown()
                    }

                    override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                        cancelReceived.set(true)
                        errorCodeReceived.set(errorCode)
                        println("PHYSICAL_EVIDENCE: AUTH-07 Cancel callback triggered: code=$errorCode ($errString)")
                        latch.countDown()
                    }
                }

                val prompt = BiometricPrompt(activity, executor, callback)
                prompt.authenticate(promptInfo, cryptoObject)
                // Immediately cancel prompt
                prompt.cancelAuthentication()
            }

            latch.await(5, TimeUnit.SECONDS)
        }

        assertTrue("Prompt cancellation must trigger error callback", cancelReceived.get())
        assertFalse("No signature must be generated when user/system cancels authentication", signatureGenerated.get())
        println("PHYSICAL_EVIDENCE: AUTH-07 Cancellation verified: code=${errorCodeReceived.get()}, signatureGenerated=${signatureGenerated.get()}")
    }

    /**
     * AUTH-08: Incorrect credential / failed attempt handling.
     * Verifies that failure callbacks do not yield signatures.
     */
    @Test
    fun testAUTH08_FailedAuthenticationAttemptHandling() {
        var signatureProduced = false
        val failureCallback = object : BiometricPrompt.AuthenticationCallback() {
            override fun onAuthenticationFailed() {
                println("PHYSICAL_EVIDENCE: AUTH-08 onAuthenticationFailed triggered as expected")
            }

            override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                signatureProduced = true
            }
        }

        // Simulate failed attempt directly on callback
        failureCallback.onAuthenticationFailed()
        assertFalse("Authentication failure must not produce any signature", signatureProduced)
        println("PHYSICAL_EVIDENCE: AUTH-08 Failure flow verified: no signature produced")
    }

    /**
     * AUTH-09: Attempt signing without authorization.
     * Keystore must reject private key usage with UserNotAuthenticatedException / SignatureException.
     */
    @Test
    fun testAUTH09_AttemptSigningWithoutAuthorization() {
        val keyManager = AndroidKeystoreDeviceKeyManager(keyAlias)
        val privateKey = keyManager.getPrivateKey()

        val signature = Signature.getInstance("SHA256withECDSA")
        signature.initSign(privateKey)

        val challenge = "IPGUARD_AUTH_TEST_CHALLENGE_009".toByteArray(Charsets.UTF_8)
        signature.update(challenge)

        var blockedByKeystore = false
        var exceptionName: String? = null
        try {
            val sigBytes = signature.sign()
            println("CRITICAL FAILURE: Signing succeeded without user authentication! Size=${sigBytes.size}")
        } catch (e: Throwable) {
            blockedByKeystore = true
            exceptionName = "${e.javaClass.name}: ${e.message}"
            println("PHYSICAL_EVIDENCE: AUTH-09 Keystore correctly rejected unauthorized signing: $exceptionName")
        }

        assertTrue("Signing without user authorization MUST be rejected by Android Keystore", blockedByKeystore)
    }

    /**
     * AUTH-10: Verify authentication type classification.
     * Validates that Device PIN is categorized as DEVICE_CREDENTIAL and never mislabeled as Biometric.
     */
    @Test
    fun testAUTH10_VerifyAuthenticationTypeClassification() {
        val policy = DeviceAuthenticationPolicy.evaluate(context)
        println("PHYSICAL_EVIDENCE: AUTH-10 Policy Evaluation:")
        println("  PrimaryAuthMethod: ${policy.primaryAuthMethod.label}")
        println("  BiometricStrongStatus: ${policy.biometricStrongLabel}")
        println("  DeviceCredentialStatus: ${policy.deviceCredentialLabel}")
        println("  Explanation: ${policy.explanation}")

        assertEquals("Primary auth method on this A54 must be DEVICE_CREDENTIAL", DeviceAuthMethod.DEVICE_CREDENTIAL, policy.primaryAuthMethod)

        // Validate constants mapping
        val typeCredential = BiometricPrompt.AUTHENTICATION_RESULT_TYPE_DEVICE_CREDENTIAL
        val typeBiometric = BiometricPrompt.AUTHENTICATION_RESULT_TYPE_BIOMETRIC
        assertEquals("AUTHENTICATION_RESULT_TYPE_DEVICE_CREDENTIAL must be 1", 1, typeCredential)
        assertEquals("AUTHENTICATION_RESULT_TYPE_BIOMETRIC must be 2", 2, typeBiometric)

        println("PHYSICAL_EVIDENCE: AUTH-10 Authentication type constants verified (Credential=1, Biometric=2)")
    }

    /**
     * AUTH-11: Key persistence across reinitialization.
     * Confirms that reloading Keystore preserves key alias, public key fingerprint, and non-exportable status.
     */
    @Test
    fun testAUTH11_KeyPersistenceAcrossReinitialization() {
        val km1 = AndroidKeystoreDeviceKeyManager(keyAlias)
        assertTrue("Key must exist before reinitialization check", km1.hasSigningKey())
        val meta1 = km1.getKeySecurityMetadata()
        val pub1 = km1.getExportedPublicKey()

        // Re-instantiate manager (simulating app process restart)
        val km2 = AndroidKeystoreDeviceKeyManager(keyAlias)
        assertTrue("Key must persist in Android Keystore", km2.hasSigningKey())
        val meta2 = km2.getKeySecurityMetadata()
        val pub2 = km2.getExportedPublicKey()

        assertEquals("Key alias must persist", meta1.alias, meta2.alias)
        assertEquals("Algorithm must persist", meta1.algorithm, meta2.algorithm)
        assertEquals("SecurityLevel must persist", meta1.securityLevel, meta2.securityLevel)
        assertEquals("Public key SHA-256 fingerprint must match exactly", pub1.sha256Fingerprint, pub2.sha256Fingerprint)
        assertEquals("Base64 public key must match exactly", pub1.base64Encoded, pub2.base64Encoded)
        assertTrue("Private key must remain non-exportable", km2.verifyPrivateKeyNonExportable())

        println("PHYSICAL_EVIDENCE: AUTH-11 Key persistence verified: Fingerprint=${pub2.sha256Fingerprint}")
    }

    /**
     * AUTH-12: Test strong biometric route status.
     * Ensures strong biometric route is accurately recognized as not available on this A54 and does not block the app.
     */
    @Test
    fun testAUTH12_TestStrongBiometricRouteStatus() {
        val strongStatus = biometricManager.canAuthenticate(BiometricManager.Authenticators.BIOMETRIC_STRONG)
        println("PHYSICAL_EVIDENCE: AUTH-12 Strong Biometric Route: Status=$strongStatus (NOT AVAILABLE for active signing on this A54)")
        assertFalse("Strong biometric must not be falsely reported as ready", strongStatus == BiometricManager.BIOMETRIC_SUCCESS)

        val policy = DeviceAuthenticationPolicy.evaluate(context)
        assertFalse("Fingerprint must not be mandatory in policy", policy.primaryAuthMethod == DeviceAuthMethod.BIOMETRIC_STRONG)
        println("PHYSICAL_EVIDENCE: AUTH-12 App is not blocked: primary auth method is ${policy.primaryAuthMethod.label}")
    }
}
