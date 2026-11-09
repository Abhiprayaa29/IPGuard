package com.ipguard.authenticator.security

import android.content.Context

enum class DeviceRegistrationStatus {
    UNREGISTERED,
    ACTIVE,
    REVOKED
}

/**
 * Manages persistent device enrollment lifecycle state in Android Authenticator.
 * Enforces one-time enrollment: once registered, the device transitions to ACTIVE
 * and can only sign in unless explicitly released via web console unregistration.
 */
class DeviceRegistrationManager(private val context: Context) {

    private val prefs by lazy {
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    }

    fun isRegistered(): Boolean {
        val status = getRegistrationStatus()
        return status == DeviceRegistrationStatus.ACTIVE || status == DeviceRegistrationStatus.REVOKED
    }

    fun getRegistrationStatus(): DeviceRegistrationStatus {
        val statusStr = prefs.getString(KEY_REGISTRATION_STATUS, DeviceRegistrationStatus.UNREGISTERED.name)
        return try {
            DeviceRegistrationStatus.valueOf(statusStr ?: DeviceRegistrationStatus.UNREGISTERED.name)
        } catch (_: Exception) {
            DeviceRegistrationStatus.UNREGISTERED
        }
    }

    fun setRegistrationStatus(status: DeviceRegistrationStatus) {
        prefs.edit().putString(KEY_REGISTRATION_STATUS, status.name).apply()
    }

    fun getRegisteredFingerprint(): String? {
        return prefs.getString(KEY_FINGERPRINT, null)
    }

    fun setRegisteredFingerprint(fingerprint: String?) {
        prefs.edit().putString(KEY_FINGERPRINT, fingerprint).apply()
    }

    fun clearRegistration() {
        prefs.edit()
            .putString(KEY_REGISTRATION_STATUS, DeviceRegistrationStatus.UNREGISTERED.name)
            .remove(KEY_FINGERPRINT)
            .apply()
    }

    companion object {
        private const val PREFS_NAME = "ipguard_device_registration"
        private const val KEY_REGISTRATION_STATUS = "registration_status"
        private const val KEY_FINGERPRINT = "registered_fingerprint"
    }
}
