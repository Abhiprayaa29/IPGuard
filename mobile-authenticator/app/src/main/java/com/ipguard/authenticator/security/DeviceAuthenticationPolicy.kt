package com.ipguard.authenticator.security

import android.app.KeyguardManager
import android.content.Context
import android.os.Build
import androidx.biometric.BiometricManager

enum class DeviceAuthMethod(val label: String) {
    DEVICE_CREDENTIAL("Device PIN / Pattern / Password"),
    BIOMETRIC_STRONG("Strong Biometric (Class 3)"),
    NONE("No Secure Lock Screen Configured")
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

    fun evaluate(context: Context): DeviceAuthenticationPolicySummary {
        val biometricManager = BiometricManager.from(context)
        val keyguardManager = context.getSystemService(Context.KEYGUARD_SERVICE) as? KeyguardManager

        val isSecure = keyguardManager?.isDeviceSecure == true || keyguardManager?.isKeyguardSecure == true

        val strongStatus = biometricManager.canAuthenticate(BiometricManager.Authenticators.BIOMETRIC_STRONG)
        val strongLabel = describeBiometricStatus(strongStatus)

        val credentialStatus = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            biometricManager.canAuthenticate(BiometricManager.Authenticators.DEVICE_CREDENTIAL)
        } else {
            if (isSecure) BiometricManager.BIOMETRIC_SUCCESS else BiometricManager.BIOMETRIC_ERROR_NONE_ENROLLED
        }
        val credentialLabel = describeCredentialStatus(credentialStatus, isSecure)

        // Policy resolution:
        // 1. If BIOMETRIC_STRONG is enrolled & ready -> BIOMETRIC_STRONG can be used.
        // 2. If strong biometric is not available (e.g. broken sensor on A54), but device credential is secure -> DEVICE_CREDENTIAL is primary.
        // 3. Otherwise -> NONE.
        val primaryMethod = when {
            strongStatus == BiometricManager.BIOMETRIC_SUCCESS -> DeviceAuthMethod.BIOMETRIC_STRONG
            credentialStatus == BiometricManager.BIOMETRIC_SUCCESS || isSecure -> DeviceAuthMethod.DEVICE_CREDENTIAL
            else -> DeviceAuthMethod.NONE
        }

        val explanation = when (primaryMethod) {
            DeviceAuthMethod.BIOMETRIC_STRONG ->
                "Class 3 Strong Biometric is active and configured as primary signing authorizer."
            DeviceAuthMethod.DEVICE_CREDENTIAL ->
                "Device PIN/Pattern is active as primary signing authorizer. Fingerprint is not required (sensor unavailable or not enrolled)."
            DeviceAuthMethod.NONE ->
                "No secure device lock screen found. A screen lock (PIN, pattern, or password) is required for IPGuard signing."
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

    private fun describeBiometricStatus(status: Int): String {
        return when (status) {
            BiometricManager.BIOMETRIC_SUCCESS -> "Available & Enrolled"
            BiometricManager.BIOMETRIC_ERROR_NONE_ENROLLED -> "None Enrolled (Sensor Not In Use)"
            BiometricManager.BIOMETRIC_ERROR_NO_HARDWARE -> "No Biometric Hardware"
            BiometricManager.BIOMETRIC_ERROR_HW_UNAVAILABLE -> "Sensor Hardware Unavailable"
            BiometricManager.BIOMETRIC_ERROR_SECURITY_UPDATE_REQUIRED -> "Security Update Required"
            BiometricManager.BIOMETRIC_ERROR_UNSUPPORTED -> "Unsupported"
            else -> "Status Code $status"
        }
    }

    private fun describeCredentialStatus(status: Int, isSecure: Boolean): String {
        return if (status == BiometricManager.BIOMETRIC_SUCCESS || isSecure) {
            "Configured & Active (PIN/Pattern/Password)"
        } else {
            "Not Configured"
        }
    }
}
