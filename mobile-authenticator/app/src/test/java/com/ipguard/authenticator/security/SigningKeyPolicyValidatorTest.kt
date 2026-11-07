package com.ipguard.authenticator.security

import android.security.keystore.KeyProperties
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.security.KeyPairGenerator
import java.security.PublicKey
import java.security.spec.ECGenParameterSpec

class SigningKeyPolicyValidatorTest {

    private val ecPublicKey: PublicKey = KeyPairGenerator.getInstance("EC").run {
        initialize(ECGenParameterSpec("secp256r1"))
        generateKeyPair().public
    }

    private fun metadata(
        algorithm: String = "EC",
        keySize: Int = 256,
        digests: List<String> = listOf("SHA-256"),
        purposes: Int = KeyProperties.PURPOSE_SIGN or KeyProperties.PURPOSE_VERIFY,
        userAuthenticationRequired: Boolean = true,
        userAuthenticationTypes: Int =
            KeyProperties.AUTH_BIOMETRIC_STRONG or KeyProperties.AUTH_DEVICE_CREDENTIAL,
        invalidated: Boolean? = false,
        nonExportable: Boolean = true
    ): KeySecurityMetadata {
        return KeySecurityMetadata(
            alias = DeviceKeyManager.KEY_ALIAS,
            algorithm = algorithm,
            keySize = keySize,
            curve = DeviceKeyManager.EC_CURVE,
            digests = digests,
            purposes = purposes,
            isInsideSecureHardware = true,
            securityLevel = KeySecurityLevel.TRUSTED_ENVIRONMENT,
            userAuthenticationRequired = userAuthenticationRequired,
            userAuthenticationValidityDurationSeconds = -1,
            userAuthenticationTypes = userAuthenticationTypes,
            isInvalidatedByBiometricEnrollment = invalidated,
            isNonExportable = nonExportable
        )
    }

    private fun validate(
        metadata: KeySecurityMetadata = metadata(),
        publicKey: PublicKey? = ecPublicKey,
        apiLevel: Int = 36
    ): List<String> {
        return SigningKeyPolicyValidator.validate(
            metadata = metadata,
            requireUserAuthentication = true,
            publicKey = publicKey,
            apiLevel = apiLevel
        )
    }

    @Test
    fun validKeyHasNoViolations() {
        assertTrue(validate().isEmpty())
    }

    @Test
    fun existingKeyWithoutRequiredUserAuthenticationIsRejected() {
        val violations = validate(metadata(userAuthenticationRequired = false))

        assertTrue(violations.any { it.contains("authentication policy") })
    }

    @Test
    fun invalidatedKeyIsRejected() {
        val violations = validate(metadata(invalidated = true))

        assertTrue(violations.any { it.contains("invalidated") })
    }

    @Test
    fun exportablePrivateKeyIsRejected() {
        val violations = validate(metadata(nonExportable = false))

        assertTrue(violations.any { it.contains("non-exportable") })
    }

    @Test
    fun nonP256PublicKeyIsRejected() {
        val rsaPublicKey = KeyPairGenerator.getInstance("RSA").run {
            initialize(2048)
            generateKeyPair().public
        }

        val violations = validate(publicKey = rsaPublicKey)

        assertTrue(violations.any { it.contains("P-256") })
    }

    @Test
    fun authenticationTypesAreNotRequiredBeforeApi30() {
        val violations = validate(
            metadata = metadata(userAuthenticationTypes = 0),
            apiLevel = 29
        )

        assertFalse(violations.any { it.contains("strong biometric") })
    }
}
