package com.ipguard.authenticator.security

open class DeviceKeyException(
    message: String,
    cause: Throwable? = null
) : Exception(message, cause)

class DeviceKeyNotFoundException(
    message: String
) : DeviceKeyException(message)

class DeviceLockScreenRequiredException(
    message: String,
    cause: Throwable? = null
) : DeviceKeyException(message, cause)

class KeySecurityViolationException(
    message: String
) : DeviceKeyException(message)
