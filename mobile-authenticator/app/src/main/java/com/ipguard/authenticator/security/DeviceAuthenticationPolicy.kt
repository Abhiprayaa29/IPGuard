package com.ipguard.authenticator.security

import android.app.KeyguardManager
import android.content.Context
import android.os.Build
import androidx.annotation.StringRes
import androidx.biometric.BiometricManager
import com.ipguard.authenticator.R

enum class DeviceAuthMethod(@get:StringRes val labelRes: Int) {
    DEVICE_CREDENTIAL(R.string.policy_method_device_credential),
    BIOMETRIC_STRONG(R.string.policy_method_biometric_strong),
    NONE(R.string.policy_method_none);

    fun label(context: Context): String = context.getString(labelRes)
}

data class DeviceAuthenticationPolicySummary(
    val isDeviceSecure: Boolean,
    val biometricStrongStatus: Int,
    val biometricStrongLabel: String,
    val deviceCredentialStatus: Int,
    val deviceCredentialLabel: String,
    val primaryAuthMethod: DeviceAuthMethod,
    val explanation: String
)

object DeviceAuthenticationPolicy {

    fun canUseDeviceCredentialCryptoObject(apiLevel: Int = Build.VERSION.SDK_INT): Boolean {
        return apiLevel >= Build.VERSION_CODES.R
    }

    fun evaluate(context: Context): DeviceAuthenticationPolicySummary {
        val biometricManager = BiometricManager.from(context)
        val keyguardManager = context.getSystemService(Context.KEYGUARD_SERVICE) as? KeyguardManager

        val isSecure = keyguardManager?.isDeviceSecure == true || keyguardManager?.isKeyguardSecure == true
        val credentialCryptoSupported = canUseDeviceCredentialCryptoObject()

        val strongStatus = biometricManager.canAuthenticate(BiometricManager.Authenticators.BIOMETRIC_STRONG)
        val strongLabel = describeBiometricStatus(context, strongStatus)

        val credentialStatus = if (credentialCryptoSupported) {
            biometricManager.canAuthenticate(BiometricManager.Authenticators.DEVICE_CREDENTIAL)
        } else {
            BiometricManager.BIOMETRIC_ERROR_UNSUPPORTED
        }
        val credentialLabel = describeCredentialStatus(context, credentialStatus, isSecure)

        val primaryMethod = when {
            strongStatus == BiometricManager.BIOMETRIC_SUCCESS -> DeviceAuthMethod.BIOMETRIC_STRONG
            credentialCryptoSupported &&
                (credentialStatus == BiometricManager.BIOMETRIC_SUCCESS || isSecure) ->
                DeviceAuthMethod.DEVICE_CREDENTIAL
            else -> DeviceAuthMethod.NONE
        }

        val explanation = when {
            primaryMethod == DeviceAuthMethod.BIOMETRIC_STRONG ->
                context.getString(R.string.policy_explanation_biometric)
            primaryMethod == DeviceAuthMethod.DEVICE_CREDENTIAL ->
                context.getString(R.string.policy_explanation_credential)
            isSecure && !credentialCryptoSupported ->
                context.getString(R.string.policy_explanation_secure_unsupported)
            else ->
                context.getString(R.string.policy_explanation_no_lock)
        }

        return DeviceAuthenticationPolicySummary(
            isDeviceSecure = isSecure,
            biometricStrongStatus = strongStatus,
            biometricStrongLabel = strongLabel,
            deviceCredentialStatus = credentialStatus,
            deviceCredentialLabel = credentialLabel,
            primaryAuthMethod = primaryMethod,
            explanation = explanation
        )
    }

    private fun describeBiometricStatus(context: Context, status: Int): String {
        return when (status) {
            BiometricManager.BIOMETRIC_SUCCESS -> context.getString(R.string.policy_bio_available)
            BiometricManager.BIOMETRIC_ERROR_NONE_ENROLLED -> context.getString(R.string.policy_bio_none_enrolled)
            BiometricManager.BIOMETRIC_ERROR_NO_HARDWARE -> context.getString(R.string.policy_bio_no_hardware)
            BiometricManager.BIOMETRIC_ERROR_HW_UNAVAILABLE -> context.getString(R.string.policy_bio_hw_unavailable)
            BiometricManager.BIOMETRIC_ERROR_SECURITY_UPDATE_REQUIRED -> context.getString(R.string.policy_bio_security_update)
            BiometricManager.BIOMETRIC_ERROR_UNSUPPORTED -> context.getString(R.string.policy_bio_unsupported)
            else -> context.getString(R.string.policy_bio_status_code, status)
        }
    }

    private fun describeCredentialStatus(context: Context, status: Int, isSecure: Boolean): String {
        if (!canUseDeviceCredentialCryptoObject()) {
            return context.getString(R.string.policy_credential_unsupported)
        }
        return if (status == BiometricManager.BIOMETRIC_SUCCESS || isSecure) {
            context.getString(R.string.policy_credential_active)
        } else {
            context.getString(R.string.policy_credential_not_configured)
        }
    }
}
