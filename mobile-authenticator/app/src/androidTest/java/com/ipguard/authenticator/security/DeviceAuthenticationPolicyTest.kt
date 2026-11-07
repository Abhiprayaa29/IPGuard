package com.ipguard.authenticator.security

import android.app.KeyguardManager
import android.content.Context
import android.os.Build
import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt
import androidx.core.content.ContextCompat
import androidx.test.core.app.ActivityScenario
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.ipguard.authenticator.MainActivity
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import java.security.Signature
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference

@RunWith(AndroidJUnit4::class)
class DeviceAuthenticationPolicyTest {

    private lateinit var context: Context
    private lateinit var biometricManager: BiometricManager
    private lateinit var keyManager: AndroidKeystoreDeviceKeyManager
    private val testAlias = "ipguard_auth_policy_test_v1"

    @Before
    fun setUp() {
        context = ApplicationProvider.getApplicationContext()
        biometricManager = BiometricManager.from(context)
        keyManager = AndroidKeystoreDeviceKeyManager(testAlias)
        keyManager.deleteSigningKey()
        keyManager.generateSigningKey(requireUserAuthentication = true)
    }

    @After
    fun tearDown() {
        runCatching { keyManager.deleteSigningKey() }
    }

    @Test
    fun testAUTH01_DetectBiometricStrongCapability() {
        val result = biometricManager.canAuthenticate(BiometricManager.Authenticators.BIOMETRIC_STRONG)
        val knownStatus = setOf(
            BiometricManager.BIOMETRIC_SUCCESS,
            BiometricManager.BIOMETRIC_ERROR_NONE_ENROLLED,
            BiometricManager.BIOMETRIC_ERROR_NO_HARDWARE,
            BiometricManager.BIOMETRIC_ERROR_HW_UNAVAILABLE,
            BiometricManager.BIOMETRIC_ERROR_SECURITY_UPDATE_REQUIRED,
            BiometricManager.BIOMETRIC_ERROR_UNSUPPORTED,
            BiometricManager.BIOMETRIC_STATUS_UNKNOWN
        )
        println("PHYSICAL_EVIDENCE: AUTH-01 BIOMETRIC_STRONG capability: $result")

        assertTrue("BIOMETRIC_STRONG must return a documented status", result in knownStatus)
    }

    @Test
    fun testAUTH02_DetectDeviceCredentialCapability() {
        assumeTrue(Build.VERSION.SDK_INT >= Build.VERSION_CODES.R)
        val result = biometricManager.canAuthenticate(BiometricManager.Authenticators.DEVICE_CREDENTIAL)
        val keyguardManager = context.getSystemService(Context.KEYGUARD_SERVICE) as? KeyguardManager
        println("PHYSICAL_EVIDENCE: AUTH-02 DEVICE_CREDENTIAL capability: $result")

        if (keyguardManager?.isDeviceSecure == true) {
            assertEquals(
                "A secure device must report DEVICE_CREDENTIAL as available",
                BiometricManager.BIOMETRIC_SUCCESS,
                result
            )
        }
    }

    @Test
    fun testAUTH03_LaunchCombinedAuthenticationPrompt() {
        assumeTrue(Build.VERSION.SDK_INT >= Build.VERSION_CODES.R)
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
                        println("PHYSICAL_EVIDENCE: AUTH-03 prompt error: $errorCode ($errString)")
                    }
                }
                val prompt = BiometricPrompt(activity, executor, callback)
                try {
                    prompt.authenticate(promptInfo, cryptoObject)
                    promptLaunched.set(true)
                    prompt.cancelAuthentication()
                } catch (e: Throwable) {
                    promptError.set("${e.javaClass.name}: ${e.message}")
                }
            }
        }

        assertNull("Prompt launch must not throw: ${promptError.get()}", promptError.get())
        assertTrue("Prompt must be accepted by the system", promptLaunched.get())
    }

    @Test
    fun testAUTH06_KeystoreSignatureRoundTrip() {
        val alias = "ipguard_auth06_keystore_test_v1"
        val manager = AndroidKeystoreDeviceKeyManager(alias)
        try {
            manager.deleteSigningKey()
            manager.generateSigningKey(requireUserAuthentication = false)

            val challenge = "IPGUARD_CRYPTO_VERIFICATION_PAYLOAD_AUTH06".toByteArray(Charsets.UTF_8)
            val signer = Signature.getInstance("SHA256withECDSA")
            signer.initSign(manager.getPrivateKey())
            signer.update(challenge)
            val signatureBytes = signer.sign()

            assertNotNull("Signature bytes must not be null", signatureBytes)
            assertTrue(
                "ECDSA P-256 signature must use ASN.1 DER encoding",
                signatureBytes.size in 64..72
            )
            assertTrue(
                "Android Keystore signature must verify with the exported public key",
                DeviceSigningAuthenticator(manager).verifySignature(challenge, signatureBytes)
            )
            assertFalse(
                "Signature verification must reject a tampered challenge",
                DeviceSigningAuthenticator(manager).verifySignature(
                    "IPGUARD_TAMPERED_CHALLENGE_AUTH06".toByteArray(Charsets.UTF_8),
                    signatureBytes
                )
            )
            println("PHYSICAL_EVIDENCE: AUTH-06 Keystore ECDSA round trip verified (${signatureBytes.size} bytes)")
        } finally {
            manager.deleteSigningKey()
        }
    }

    @Test
    fun testAUTH07_CancelAuthentication() {
        val strongStatus = biometricManager.canAuthenticate(
            BiometricManager.Authenticators.BIOMETRIC_STRONG
        )
        assumeTrue(
            Build.VERSION.SDK_INT >= Build.VERSION_CODES.R ||
                strongStatus == BiometricManager.BIOMETRIC_SUCCESS
        )

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
                        latch.countDown()
                    }
                }

                val prompt = BiometricPrompt(activity, executor, callback)
                prompt.authenticate(promptInfo, cryptoObject)
                prompt.cancelAuthentication()
            }

            latch.await(5, TimeUnit.SECONDS)
        }

        assertTrue("Prompt cancellation must trigger error callback", cancelReceived.get())
        assertFalse("No signature must be generated when authentication is cancelled", signatureGenerated.get())
        println("PHYSICAL_EVIDENCE: AUTH-07 cancellation code=${errorCodeReceived.get()}")
    }

    @Test
    fun testAUTH08_AttemptFailedIsNonTerminalContract() {
        val outcome = SigningResultPolicy.classify(SigningResult.AttemptFailed("Try again."))

        assertTrue("A failed attempt must not terminate the prompt", outcome is SigningOutcome.NonTerminal)
        println("PHYSICAL_EVIDENCE: AUTH-08 callback contract verified (non-terminal)")
    }

    @Test
    fun testAUTH09_AttemptSigningWithoutAuthorization() {
        var blockedByKeystore = false
        try {
            val privateKey = keyManager.getPrivateKey()
            val signature = Signature.getInstance("SHA256withECDSA")
            signature.initSign(privateKey)
            signature.update("IPGUARD_AUTH_TEST_CHALLENGE_009".toByteArray(Charsets.UTF_8))
            val sigBytes = signature.sign()
            println("CRITICAL FAILURE: signing succeeded without authentication (${sigBytes.size} bytes)")
        } catch (e: Throwable) {
            blockedByKeystore = true
            println("PHYSICAL_EVIDENCE: AUTH-09 Keystore rejected unauthorized signing: ${e.javaClass.name}")
        }

        assertTrue("Signing without user authorization must be rejected", blockedByKeystore)
    }

    @Test
    fun testAUTH10_VerifyAuthenticationTypeClassification() {
        val policy = DeviceAuthenticationPolicy.evaluate(context)
        println("PHYSICAL_EVIDENCE: AUTH-10 primary=${policy.primaryAuthMethod.label}")

        when (policy.primaryAuthMethod) {
            DeviceAuthMethod.BIOMETRIC_STRONG -> assertEquals(
                BiometricManager.BIOMETRIC_SUCCESS,
                policy.biometricStrongStatus
            )
            DeviceAuthMethod.DEVICE_CREDENTIAL -> {
                assertTrue(DeviceAuthenticationPolicy.canUseDeviceCredentialCryptoObject())
                assertTrue(
                    "Device credential policy requires a usable credential",
                    policy.deviceCredentialStatus == BiometricManager.BIOMETRIC_SUCCESS ||
                        policy.isDeviceSecure
                )
            }
            DeviceAuthMethod.NONE -> assertFalse(
                "NONE must not be reported when strong biometric is available",
                policy.biometricStrongStatus == BiometricManager.BIOMETRIC_SUCCESS
            )
        }

        assertEquals(1, BiometricPrompt.AUTHENTICATION_RESULT_TYPE_DEVICE_CREDENTIAL)
        assertEquals(2, BiometricPrompt.AUTHENTICATION_RESULT_TYPE_BIOMETRIC)
    }

    @Test
    fun testAUTH11_KeyPersistenceAcrossReinitialization() {
        assertTrue("Key must exist before reinitialization check", keyManager.hasSigningKey())
        val meta1 = keyManager.getKeySecurityMetadata()
        val pub1 = keyManager.getExportedPublicKey()

        val km2 = AndroidKeystoreDeviceKeyManager(testAlias)
        assertTrue("Key must persist in Android Keystore", km2.hasSigningKey())
        val meta2 = km2.getKeySecurityMetadata()
        val pub2 = km2.getExportedPublicKey()

        assertEquals(meta1.alias, meta2.alias)
        assertEquals(meta1.algorithm, meta2.algorithm)
        assertEquals(meta1.securityLevel, meta2.securityLevel)
        assertEquals(pub1.sha256Fingerprint, pub2.sha256Fingerprint)
        assertEquals(pub1.base64Encoded, pub2.base64Encoded)
        assertTrue(km2.verifyPrivateKeyNonExportable())
    }

    @Test
    fun testAUTH12_BiometricPolicyDoesNotOverclaim() {
        val policy = DeviceAuthenticationPolicy.evaluate(context)
        val strongStatus = biometricManager.canAuthenticate(
            BiometricManager.Authenticators.BIOMETRIC_STRONG
        )

        if (strongStatus != BiometricManager.BIOMETRIC_SUCCESS) {
            assertFalse(
                "Policy must not claim strong biometric when it is unavailable",
                policy.primaryAuthMethod == DeviceAuthMethod.BIOMETRIC_STRONG
            )
        }
        if (!DeviceAuthenticationPolicy.canUseDeviceCredentialCryptoObject() &&
            strongStatus != BiometricManager.BIOMETRIC_SUCCESS
        ) {
            assertEquals(
                "API 28-29 without strong biometric must fail closed",
                DeviceAuthMethod.NONE,
                policy.primaryAuthMethod
            )
        }
        println("PHYSICAL_EVIDENCE: AUTH-12 primary=${policy.primaryAuthMethod.label}, strong=$strongStatus")
    }
}
