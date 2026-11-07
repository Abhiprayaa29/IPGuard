package com.ipguard.authenticator.security

import android.security.keystore.KeyProperties
import java.security.PublicKey
import java.security.interfaces.ECPublicKey

object SigningKeyPolicyValidator {

    fun validate(
        metadata: KeySecurityMetadata,
        requireUserAuthentication: Boolean,
        publicKey: PublicKey?,
        apiLevel: Int
    ): List<String> {
        val violations = mutableListOf<String>()

        if (metadata.algorithm != DeviceKeyManager.KEY_ALGORITHM) {
            violations.add("algorithm must be EC")
        }
        if (metadata.keySize != 256) {
            violations.add("key size must be 256 bits")
        }
        if (metadata.digests.none { it.equals("SHA-256", ignoreCase = true) }) {
            violations.add("digest must include SHA-256")
        }
        if (metadata.purposes and KeyProperties.PURPOSE_SIGN == 0) {
            violations.add("key must allow signing")
        }
        if (metadata.userAuthenticationRequired != requireUserAuthentication) {
            violations.add("user authentication policy does not match the requested policy")
        }
        if (requireUserAuthentication && apiLevel >= 30) {
            val allowedTypes =
                KeyProperties.AUTH_BIOMETRIC_STRONG or KeyProperties.AUTH_DEVICE_CREDENTIAL
            if (metadata.userAuthenticationTypes and allowedTypes == 0) {
                violations.add(
                    "key does not allow strong biometric or device credential authentication"
                )
            }
        }
        if (!metadata.isNonExportable) {
            violations.add("private key must be non-exportable")
        }
        if (metadata.isInvalidatedByBiometricEnrollment == true) {
            violations.add("key was invalidated by a biometric enrollment change")
        }
        if (publicKey !is ECPublicKey || publicKey.params.curve.field.fieldSize != 256) {
            violations.add("public key must use the P-256 curve")
        }

        return violations
    }
}
