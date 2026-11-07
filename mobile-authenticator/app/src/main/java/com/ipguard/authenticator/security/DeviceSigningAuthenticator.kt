package com.ipguard.authenticator.security

import android.os.Build
import android.security.keystore.KeyPermanentlyInvalidatedException
import android.security.keystore.UserNotAuthenticatedException
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

    data class AttemptFailed(
        val message: String = "Authentication attempt failed. Try again."
    ) : SigningResult()

    data class Cancelled(
        val errorCode: Int,
        val message: String = "Authentication was cancelled."
    ) : SigningResult()

    data class Error(
        val errorCode: Int,
        val errorMessage: String
    ) : SigningResult()

    companion object {
        const val ERROR_CRYPTO_INIT_FAILED = -1
        const val ERROR_SIGNING_FAILED = -2
        const val ERROR_LOCAL_VERIFICATION_FAILED = -3
        const val ERROR_KEY_INVALIDATED = -4
        const val ERROR_PROMPT_UNAVAILABLE = -5
        const val ERROR_UNSUPPORTED_API = -6
    }
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

        if (DeviceAuthenticationPolicy.canUseDeviceCredentialCryptoObject()) {
            builder.setAllowedAuthenticators(
                BiometricManager.Authenticators.BIOMETRIC_STRONG or
                        BiometricManager.Authenticators.DEVICE_CREDENTIAL
            )
        } else {
            builder.setAllowedAuthenticators(BiometricManager.Authenticators.BIOMETRIC_STRONG)
            builder.setNegativeButtonText("Cancel")
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
        if (!DeviceAuthenticationPolicy.canUseDeviceCredentialCryptoObject()) {
            val strongBiometricStatus = BiometricManager.from(activity)
                .canAuthenticate(BiometricManager.Authenticators.BIOMETRIC_STRONG)
            if (strongBiometricStatus != BiometricManager.BIOMETRIC_SUCCESS) {
                onResult(
                    SigningResult.Error(
                        errorCode = SigningResult.ERROR_UNSUPPORTED_API,
                        errorMessage = "Device-credential signing requires Android 11 or newer. " +
                            "This device can only sign with an enrolled strong biometric."
                    )
                )
                return
            }
        }

        val executor = ContextCompat.getMainExecutor(activity)
        val promptInfo = createPromptInfo(promptTitle, promptSubtitle)
        val cryptoObject = try {
            createCryptoObject()
        } catch (e: KeyPermanentlyInvalidatedException) {
            onResult(
                SigningResult.Error(
                    errorCode = SigningResult.ERROR_KEY_INVALIDATED,
                    errorMessage = "The signing key was invalidated by a device credential change. Device re-enrollment is required."
                )
            )
            return
        } catch (e: UserNotAuthenticatedException) {
            onResult(
                SigningResult.Error(
                    errorCode = SigningResult.ERROR_CRYPTO_INIT_FAILED,
                    errorMessage = "The signing key requires user authentication before use. Start a new approval attempt."
                )
            )
            return
        } catch (e: Throwable) {
            onResult(
                SigningResult.Error(
                    errorCode = SigningResult.ERROR_CRYPTO_INIT_FAILED,
                    errorMessage = "Failed to initialize crypto object: ${e.message}"
                )
            )
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
                    if (!isVerified) {
                        onResult(
                            SigningResult.Error(
                                errorCode = SigningResult.ERROR_LOCAL_VERIFICATION_FAILED,
                                errorMessage = "Signature was generated but failed local verification. Approval is not valid."
                            )
                        )
                        return
                    }

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
                            verifiedLocally = true
                        )
                    )
                } catch (e: Throwable) {
                    onResult(
                        SigningResult.Error(
                            errorCode = SigningResult.ERROR_SIGNING_FAILED,
                            errorMessage = "Signing failed after authentication: ${e.message}"
                        )
                    )
                }
            }

            override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                super.onAuthenticationError(errorCode, errString)
                if (errorCode == BiometricPrompt.ERROR_USER_CANCELED ||
                    errorCode == BiometricPrompt.ERROR_NEGATIVE_BUTTON ||
                    errorCode == BiometricPrompt.ERROR_CANCELED
                ) {
                    onResult(
                        SigningResult.Cancelled(
                            errorCode = errorCode,
                            message = errString.toString().ifBlank { "Authentication was cancelled." }
                        )
                    )
                } else {
                    onResult(
                        SigningResult.Error(
                            errorCode = errorCode,
                            errorMessage = errString.toString().ifBlank { "Authentication failed with code $errorCode." }
                        )
                    )
                }
            }

            override fun onAuthenticationFailed() {
                super.onAuthenticationFailed()
                onResult(SigningResult.AttemptFailed())
            }
        }

        val prompt = BiometricPrompt(activity, executor, callback)
        try {
            prompt.authenticate(promptInfo, cryptoObject)
        } catch (e: Throwable) {
            onResult(
                SigningResult.Error(
                    errorCode = SigningResult.ERROR_PROMPT_UNAVAILABLE,
                    errorMessage = "Biometric prompt could not be started: ${e.message}"
                )
            )
        }
    }
}
