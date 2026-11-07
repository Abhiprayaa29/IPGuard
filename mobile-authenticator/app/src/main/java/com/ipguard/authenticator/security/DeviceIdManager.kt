package com.ipguard.authenticator.security

import android.content.Context
import java.util.UUID

class DeviceIdManager(private val context: Context) {

    private val prefs by lazy {
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    }

    fun getOrCreateDeviceId(): String {
        val existing = prefs.getString(KEY_DEVICE_ID, null)
        if (!existing.isNullOrBlank()) {
            return existing
        }

        // Generate application-scoped persistent random ID
        val newId = "ipguard-dev-" + UUID.randomUUID().toString().replace("-", "").take(16)
        prefs.edit().putString(KEY_DEVICE_ID, newId).apply()
        return newId
    }

    companion object {
        private const val PREFS_NAME = "ipguard_device_identity"
        private const val KEY_DEVICE_ID = "app_scoped_device_id"
    }
}
