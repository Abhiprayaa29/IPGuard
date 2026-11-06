package com.ipguard.authenticator.security

import android.os.Build
import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt
import androidx.core.content.ContextCompat
import androidx.fragment.app.FragmentActivity
import java.security.Signature
import java.util.Base64

sealed class SigningResult {
    data class Success(
        val challenge: ByteArray,
        val signature: ByteArray,
        val base64Signature: String,
        val authenticationType: Int,
        val authMethodLabel: String,
        val verifiedLocally: Boolean,
        val timestamp: Long = System.currentTimeMillis()
    ) : SigningResult() {
        override fun equals(other: Any?): Boolean {
            if (this === other) return true
            if (javaClass != other?.javaClass) return false
            other as Success
            return challenge.contentEquals(other.challenge) && signature.contentEquals(other.signature)
        }

        override fun hashCode(): Int {
            var result = challenge.contentHashCode()
            result = 31 * result + signature.contentHashCode()
            return result
        }
    }

    data class Failed(
        val reason: String = "Authentication attempt was rejected or failed."
    ) : SigningResult()

    data class Error(
        val errorCode: Int,
        val errorMessage: String
    ) : SigningResult()
}

class DeviceSigningAuthenticator(
    private val keyManager: DeviceKeyManager = AndroidKeystoreDeviceKeyManager()
) {

    fun createPromptInfo(
        title: String = "Approve IPGuard Signing",
        subtitle: String = "Verify using device PIN, pattern, or biometric"
    ): BiometricPrompt.PromptInfo {
        val builder = BiometricPrompt.PromptInfo.Builder()
            .setTitle(title)
            .setSubtitle(subtitle)

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            builder.setAllowedAuthenticators(
                BiometricManager.Authenticators.BIOMETRIC_STRONG or
                        BiometricManager.Authenticators.DEVICE_CREDENTIAL
            )
        } else {
            @Suppress("DEPRECATION")
            builder.setDeviceCredentialAllowed(true)
        }

        return builder.build()
    }

    fun createCryptoObject(): BiometricPrompt.CryptoObject {
        val privateKey = keyManager.getPrivateKey()
        val signature = Signature.getInstance("SHA256withECDSA")
        signature.initSign(privateKey)
        return BiometricPrompt.CryptoObject(signature)
    }

    fun verifySignature(challenge: ByteArray, signatureBytes: ByteArray): Boolean {
        return try {
            val publicKey = keyManager.getPublicKey()
            val verifySignature = Signature.getInstance("SHA256withECDSA")
            verifySignature.initVerify(publicKey)
            verifySignature.update(challenge)
            verifySignature.verify(signatureBytes)
        } catch (_: Throwable) {
            false
        }
    }

    fun authenticateAndSign(
        activity: FragmentActivity,
        challenge: ByteArray,
        promptTitle: String = "Approve IPGuard Signing",
        promptSubtitle: String = "Verify using device PIN, pattern, or biometric",
        onResult: (SigningResult) -> Unit
    ) {
        val executor = ContextCompat.getMainExecutor(activity)
        val promptInfo = createPromptInfo(promptTitle, promptSubtitle)
        val cryptoObject = try {
            createCryptoObject()
        } catch (e: Throwable) {
            onResult(SigningResult.Error(errorCode = -1, errorMessage = "Failed to initialize crypto object: ${e.message}"))
            return
        }

        val callback = object : BiometricPrompt.AuthenticationCallback() {
            override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                super.onAuthenticationSucceeded(result)
                try {
                    val authorizedSignature = result.cryptoObject?.signature
                        ?: throw IllegalStateException("CryptoObject or Signature missing from AuthenticationResult")

                    authorizedSignature.update(challenge)
                    val signatureBytes = authorizedSignature.sign()
                    val base64Signature = Base64.getEncoder().encodeToString(signatureBytes)
                    val isVerified = verifySignature(challenge, signatureBytes)

                    val authType = result.authenticationType
                    val authLabel = when (authType) {
                        BiometricPrompt.AUTHENTICATION_RESULT_TYPE_DEVICE_CREDENTIAL ->
                            "Device Credential (PIN / Pattern / Password)"
                        BiometricPrompt.AUTHENTICATION_RESULT_TYPE_BIOMETRIC ->
                            "Biometric (Class 3 Strong)"
                        else ->
                            "Device Authentication (Type $authType)"
                    }

                    onResult(
                        SigningResult.Success(
                            challenge = challenge,
                            signature = signatureBytes,
                            base64Signature = base64Signature,
                            authenticationType = authType,
                            authMethodLabel = authLabel,
                            verifiedLocally = isVerified
                        )
                    )
                } catch (e: Throwable) {
                    onResult(SigningResult.Error(errorCode = -2, errorMessage = "Signing failed after authentication: ${e.message}"))
                }
            }

            override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                super.onAuthenticationError(errorCode, errString)
                onResult(SigningResult.Error(errorCode = errorCode, errorMessage = errString.toString()))
            }

            override fun onAuthenticationFailed() {
                super.onAuthenticationFailed()
                onResult(SigningResult.Failed())
            }
        }

        val prompt = BiometricPrompt(activity, executor, callback)
        prompt.authenticate(promptInfo, cryptoObject)
    }
}
