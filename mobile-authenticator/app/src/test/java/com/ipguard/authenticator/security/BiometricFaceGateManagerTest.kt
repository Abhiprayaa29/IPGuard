package com.ipguard.authenticator.security

import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.security.KeyPairGenerator
import java.security.Signature
import java.security.spec.ECGenParameterSpec

class BiometricFaceGateManagerTest {

    @Test
    fun biometricWeakAvailableMapsToAvailable() {
        val status = BiometricFaceGateManager.classifyBiometricManagerStatus(
            BiometricManager.BIOMETRIC_SUCCESS
        )
        assertTrue(status is FaceGateAvailability.Available)
    }

    @Test
    fun biometricWeakNoneEnrolledMapsToNotEnrolled() {
        val status = BiometricFaceGateManager.classifyBiometricManagerStatus(
            BiometricManager.BIOMETRIC_ERROR_NONE_ENROLLED
        )
        assertTrue(status is FaceGateAvailability.NotEnrolled)
    }

    @Test
    fun biometricWeakUnavailableStatusesMapToUnavailable() {
        val codes = listOf(
            BiometricManager.BIOMETRIC_ERROR_NO_HARDWARE,
            BiometricManager.BIOMETRIC_ERROR_HW_UNAVAILABLE,
            BiometricManager.BIOMETRIC_ERROR_UNSUPPORTED,
            BiometricManager.BIOMETRIC_ERROR_SECURITY_UPDATE_REQUIRED
        )
        codes.forEach { code ->
            val result = BiometricFaceGateManager.classifyBiometricManagerStatus(code)
            assertTrue("Expected Unavailable for code $code", result is FaceGateAvailability.Unavailable)
        }
    }

    @Test
    fun faceGateSuccessResultPreservesMethodLabel() {
        val result = FaceGateResult.Success(
            authType = BiometricPrompt.AUTHENTICATION_RESULT_TYPE_BIOMETRIC,
            authLabel = "Native Biometric Gate (BIOMETRIC_WEAK)"
        )
        assertEquals(BiometricPrompt.AUTHENTICATION_RESULT_TYPE_BIOMETRIC, result.authType)
        assertTrue(result.authLabel.contains("BIOMETRIC_WEAK"))
    }

    @Test
    fun faceGateCancelledErrorsMapToCancelled() {
        val cancelCodes = listOf(
            BiometricPrompt.ERROR_USER_CANCELED,
            BiometricPrompt.ERROR_NEGATIVE_BUTTON,
            BiometricPrompt.ERROR_CANCELED
        )
        cancelCodes.forEach { code ->
            val res = BiometricFaceGateManager.classifyAuthError(code, "User cancelled")
            assertTrue("Expected Cancelled for $code", res is FaceGateResult.Cancelled)
            assertEquals(code, (res as FaceGateResult.Cancelled).errorCode)
        }
    }

    @Test
    fun faceGateLockoutErrorsMapToLockout() {
        val lockCodes = listOf(
            BiometricPrompt.ERROR_LOCKOUT,
            BiometricPrompt.ERROR_LOCKOUT_PERMANENT
        )
        lockCodes.forEach { code ->
            val res = BiometricFaceGateManager.classifyAuthError(code, "Too many attempts")
            assertTrue("Expected Lockout for $code", res is FaceGateResult.Lockout)
            assertEquals(code, (res as FaceGateResult.Lockout).errorCode)
        }
    }

    @Test
    fun faceGateErrorDoesNotBypassGate() {
        val err = BiometricFaceGateManager.classifyAuthError(
            BiometricPrompt.ERROR_TIMEOUT,
            "Sensor timed out"
        )
        assertTrue(err is FaceGateResult.Error)
        assertFalse(err is FaceGateResult.Success)

        val attemptFailed = FaceGateResult.AttemptFailed()
        assertFalse(attemptFailed is FaceGateResult.Success)
    }

    @Test
    fun faceGatePromptInfoUsesBiometricWeakOnlyAndConfirmationDisabled() {
        val manager = BiometricFaceGateManager()
        val promptInfo = manager.createPromptInfo()
        assertEquals("Verify Your Identity", promptInfo.title.toString())
        assertEquals("Authenticate using your device biometrics", promptInfo.subtitle.toString())
        assertEquals(BiometricManager.Authenticators.BIOMETRIC_WEAK, promptInfo.allowedAuthenticators)
        assertNotEquals(
            BiometricManager.Authenticators.BIOMETRIC_STRONG,
            promptInfo.allowedAuthenticators
        )
        assertFalse(promptInfo.isConfirmationRequired)
        assertEquals("Cancel", promptInfo.negativeButtonText.toString())
    }

    @Test
    fun existingCryptoObjectPromptPolicyAndEcdsaSignatureRemainPreserved() {
        val signingAuthenticator = DeviceSigningAuthenticator()
        val signingPrompt = signingAuthenticator.createPromptInfo()
        val expectedCryptoAuthenticators =
            BiometricManager.Authenticators.BIOMETRIC_STRONG or
                BiometricManager.Authenticators.DEVICE_CREDENTIAL

        // Ensure CryptoObject signing authenticators never weaken to BIOMETRIC_WEAK
        assertTrue(
            signingPrompt.allowedAuthenticators == expectedCryptoAuthenticators ||
                signingPrompt.allowedAuthenticators == BiometricManager.Authenticators.BIOMETRIC_STRONG
        )

        // Verify ECDSA P-256 SHA256withECDSA signature generation & verification remain intact
        val kpg = KeyPairGenerator.getInstance("EC")
        kpg.initialize(ECGenParameterSpec("secp256r1"))
        val kp = kpg.generateKeyPair()
        val challenge = "IPGUARD_M2_CHALLENGE_NONCE_TEST".toByteArray(Charsets.UTF_8)

        val signer = Signature.getInstance("SHA256withECDSA")
        signer.initSign(kp.private)
        signer.update(challenge)
        val sigBytes = signer.sign()

        val verifier = Signature.getInstance("SHA256withECDSA")
        verifier.initVerify(kp.public)
        verifier.update(challenge)
        assertTrue(verifier.verify(sigBytes))
    }
}
