package com.ipguard.authenticator.security

import android.content.Context
import android.util.Log
import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt
import androidx.core.content.ContextCompat
import androidx.fragment.app.FragmentActivity

sealed interface FaceGateAvailability {
    data object Available : FaceGateAvailability
    data class NotEnrolled(val reason: String) : FaceGateAvailability
    data class Unavailable(val reason: String) : FaceGateAvailability
}

sealed class FaceGateResult {
    data class Success(
        val authType: Int,
        val authLabel: String
    ) : FaceGateResult()

    data class AttemptFailed(
        val message: String = "Face Authentication Failed — Please Retry"
    ) : FaceGateResult()

    data class Cancelled(
        val errorCode: Int,
        val message: String
    ) : FaceGateResult()

    data class Lockout(
        val errorCode: Int,
        val message: String
    ) : FaceGateResult()

    data class NotEnrolled(
        val errorCode: Int,
        val message: String
    ) : FaceGateResult()

    data class Error(
        val errorCode: Int,
        val message: String
    ) : FaceGateResult()
}

/**
 * Native Android Face / Weak Biometric pre-signing authentication gate.
 * Uses AndroidX BiometricPrompt with BIOMETRIC_WEAK (no CryptoObject) strictly as a
 * preliminary OS biometric check prior to existing Keystore ECDSA P-256 CryptoObject signing.
 */
class BiometricFaceGateManager {

    fun evaluateAvailability(context: Context): FaceGateAvailability {
        val status = BiometricManager.from(context)
            .canAuthenticate(BiometricManager.Authenticators.BIOMETRIC_WEAK)
        val result = classifyBiometricManagerStatus(status)
        Log.i(TAG, "FACE_GATE_AVAILABILITY_CHECK statusCode=$status result=${result::class.simpleName}")
        return result
    }

    fun createPromptInfo(
        title: String = "Verify Your Identity",
        subtitle: String = "Authenticate using your device biometrics",
        negativeButtonText: String = "Cancel"
    ): BiometricPrompt.PromptInfo {
        return BiometricPrompt.PromptInfo.Builder()
            .setTitle(title)
            .setSubtitle(subtitle)
            .setAllowedAuthenticators(BiometricManager.Authenticators.BIOMETRIC_WEAK)
            .setConfirmationRequired(false)
            .setNegativeButtonText(negativeButtonText.ifBlank { "Cancel" })
            .build()
    }

    fun authenticate(
        activity: FragmentActivity,
        title: String = "Verify Your Identity",
        subtitle: String = "Authenticate using your device biometrics",
        negativeButtonText: String = "Cancel",
        onResult: (FaceGateResult) -> Unit
    ) {
        when (val availability = evaluateAvailability(activity)) {
            is FaceGateAvailability.NotEnrolled -> {
                onResult(
                    FaceGateResult.NotEnrolled(
                        errorCode = BiometricPrompt.ERROR_NO_BIOMETRICS,
                        message = availability.reason
                    )
                )
                return
            }
            is FaceGateAvailability.Unavailable -> {
                onResult(
                    FaceGateResult.Error(
                        errorCode = BiometricPrompt.ERROR_HW_UNAVAILABLE,
                        message = availability.reason
                    )
                )
                return
            }
            is FaceGateAvailability.Available -> Unit
        }

        val executor = ContextCompat.getMainExecutor(activity)
        val promptInfo = createPromptInfo(
            title = title,
            subtitle = subtitle,
            negativeButtonText = negativeButtonText
        )

        val callback = object : BiometricPrompt.AuthenticationCallback() {
            override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                super.onAuthenticationSucceeded(result)
                Log.i(TAG, "FACE_GATE_AUTHENTICATION_SUCCEEDED authType=${result.authenticationType}")
                onResult(
                    FaceGateResult.Success(
                        authType = result.authenticationType,
                        authLabel = "Biometric Authentication Successful"
                    )
                )
            }

            override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                super.onAuthenticationError(errorCode, errString)
                val classified = classifyAuthError(errorCode, errString)
                when (classified) {
                    is FaceGateResult.Cancelled ->
                        Log.i(TAG, "FACE_GATE_AUTHENTICATION_CANCELLED code=$errorCode")
                    else ->
                        Log.w(TAG, "FACE_GATE_AUTHENTICATION_ERROR code=$errorCode")
                }
                onResult(classified)
            }

            override fun onAuthenticationFailed() {
                super.onAuthenticationFailed()
                Log.w(TAG, "FACE_GATE_AUTHENTICATION_FAILED")
                onResult(FaceGateResult.AttemptFailed())
            }
        }

        val prompt = BiometricPrompt(activity, executor, callback)
        try {
            Log.i(TAG, "FACE_GATE_PROMPT_REQUESTED allowed=BIOMETRIC_WEAK")
            prompt.authenticate(promptInfo)
        } catch (e: Throwable) {
            Log.e(TAG, "FACE_GATE_AUTHENTICATION_ERROR launch_exception=${e.javaClass.simpleName}")
            onResult(
                FaceGateResult.Error(
                    errorCode = BiometricPrompt.ERROR_UNABLE_TO_PROCESS,
                    message = "Face Authentication Failed — Please Retry (${e.javaClass.simpleName})"
                )
            )
        }
    }

    companion object {
        const val TAG = "IPGuardBiometric"

        fun classifyBiometricManagerStatus(status: Int): FaceGateAvailability {
            return when (status) {
                BiometricManager.BIOMETRIC_SUCCESS ->
                    FaceGateAvailability.Available
                BiometricManager.BIOMETRIC_ERROR_NONE_ENROLLED ->
                    FaceGateAvailability.NotEnrolled(
                        "No face or biometric credential is enrolled in Android device settings."
                    )
                BiometricManager.BIOMETRIC_ERROR_NO_HARDWARE ->
                    FaceGateAvailability.Unavailable(
                        "Biometric hardware for Face / Weak Biometric authentication is not present on this device."
                    )
                BiometricManager.BIOMETRIC_ERROR_HW_UNAVAILABLE ->
                    FaceGateAvailability.Unavailable(
                        "Biometric hardware is currently busy or unavailable."
                    )
                BiometricManager.BIOMETRIC_ERROR_SECURITY_UPDATE_REQUIRED ->
                    FaceGateAvailability.Unavailable(
                        "A device security update is required before biometric authentication can be used."
                    )
                BiometricManager.BIOMETRIC_ERROR_UNSUPPORTED ->
                    FaceGateAvailability.Unavailable(
                        "BIOMETRIC_WEAK authentication is not supported on this Android configuration."
                    )
                else ->
                    FaceGateAvailability.Unavailable(
                        "Biometric authentication unavailable (status code $status)."
                    )
            }
        }

        fun classifyAuthError(errorCode: Int, errString: CharSequence): FaceGateResult {
            val text = errString.toString().trim()
            return when (errorCode) {
                BiometricPrompt.ERROR_USER_CANCELED,
                BiometricPrompt.ERROR_NEGATIVE_BUTTON,
                BiometricPrompt.ERROR_CANCELED ->
                    FaceGateResult.Cancelled(
                        errorCode = errorCode,
                        message = text.ifBlank { "Face Authentication cancelled." }
                    )

                BiometricPrompt.ERROR_LOCKOUT,
                BiometricPrompt.ERROR_LOCKOUT_PERMANENT ->
                    FaceGateResult.Lockout(
                        errorCode = errorCode,
                        message = text.ifBlank {
                            "Too many failed biometric attempts. Biometric gate is locked."
                        }
                    )

                BiometricPrompt.ERROR_NO_BIOMETRICS ->
                    FaceGateResult.NotEnrolled(
                        errorCode = errorCode,
                        message = text.ifBlank {
                            "No face or biometric credential is enrolled on this device."
                        }
                    )

                else ->
                    FaceGateResult.Error(
                        errorCode = errorCode,
                        message = text.ifBlank { "Face Authentication Failed — Please Retry (code $errorCode)." }
                    )
            }
        }
    }
}
