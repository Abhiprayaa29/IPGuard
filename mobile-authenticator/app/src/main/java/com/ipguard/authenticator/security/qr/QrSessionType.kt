package com.ipguard.authenticator.security.qr

enum class QrSessionType(val value: String) {
    AUTHENTICATION("AUTHENTICATION"),
    ENROLLMENT("ENROLLMENT");

    companion object {
        fun fromString(typeString: String): QrSessionType? {
            return entries.firstOrNull { it.value.equals(typeString, ignoreCase = false) }
        }
    }
}
