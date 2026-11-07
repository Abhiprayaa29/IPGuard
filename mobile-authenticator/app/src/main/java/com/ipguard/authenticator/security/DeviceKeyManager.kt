package com.ipguard.authenticator.security

import android.os.Build
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyInfo
import android.security.keystore.KeyProperties
import java.security.KeyFactory
import java.security.KeyPairGenerator
import java.security.KeyStore
import java.security.MessageDigest
import java.security.PrivateKey
import java.security.PublicKey
import java.security.spec.ECGenParameterSpec
import java.security.spec.X509EncodedKeySpec
import java.util.Base64

interface DeviceKeyManager {
    val alias: String
    fun hasSigningKey(): Boolean
    fun generateSigningKey(requireUserAuthentication: Boolean = true): KeySecurityMetadata
    fun ensureSigningKey(requireUserAuthentication: Boolean = true): KeySecurityMetadata
    fun rotateSigningKey(requireUserAuthentication: Boolean = true): KeySecurityMetadata
    fun getKeySecurityMetadata(): KeySecurityMetadata
    fun getExportedPublicKey(): ExportedPublicKey
    fun getPublicKey(): PublicKey
    fun getPrivateKey(): PrivateKey
    fun verifyPrivateKeyNonExportable(): Boolean
    fun deleteSigningKey(): Boolean
    fun validatePublicKeyParsing(base64PublicKey: String): Boolean

    companion object {
        const val KEY_ALIAS = "ipguard_device_signing_v1"
        const val KEY_ALGORITHM = KeyProperties.KEY_ALGORITHM_EC
        const val EC_CURVE = "secp256r1"
        const val KEYSTORE_PROVIDER = "AndroidKeyStore"
        const val DIGEST_ALGORITHM = KeyProperties.DIGEST_SHA256
    }
}

class AndroidKeystoreDeviceKeyManager(
    private val keyAlias: String = DeviceKeyManager.KEY_ALIAS
) : DeviceKeyManager {

    override val alias: String
        get() = keyAlias

    private val keyStore: KeyStore by lazy {
        KeyStore.getInstance(DeviceKeyManager.KEYSTORE_PROVIDER).apply {
            load(null)
        }
    }

    override fun hasSigningKey(): Boolean {
        reloadKeyStore()
        return keyStore.containsAlias(keyAlias) && keyStore.isKeyEntry(keyAlias)
    }

    override fun generateSigningKey(requireUserAuthentication: Boolean): KeySecurityMetadata {
        val keyPairGenerator = KeyPairGenerator.getInstance(
            DeviceKeyManager.KEY_ALGORITHM,
            DeviceKeyManager.KEYSTORE_PROVIDER
        )

        val builder = KeyGenParameterSpec.Builder(
            keyAlias,
            KeyProperties.PURPOSE_SIGN or KeyProperties.PURPOSE_VERIFY
        )
            .setAlgorithmParameterSpec(ECGenParameterSpec(DeviceKeyManager.EC_CURVE))
            .setDigests(DeviceKeyManager.DIGEST_ALGORITHM)

        if (requireUserAuthentication) {
            builder.setUserAuthenticationRequired(true)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                builder.setUserAuthenticationParameters(
                    0,
                    KeyProperties.AUTH_BIOMETRIC_STRONG or KeyProperties.AUTH_DEVICE_CREDENTIAL
                )
            } else {
                @Suppress("DEPRECATION")
                builder.setUserAuthenticationValidityDurationSeconds(-1)
            }
            try {
                builder.setInvalidatedByBiometricEnrollment(true)
            } catch (_: Throwable) {
                // Ignore if not supported on the host device
            }
        } else {
            builder.setUserAuthenticationRequired(false)
        }

        try {
            keyPairGenerator.initialize(builder.build())
            keyPairGenerator.generateKeyPair()
        } catch (error: Throwable) {
            val message = error.message ?: ""
            if (message.contains("lock screen", ignoreCase = true) ||
                message.contains("secure lock", ignoreCase = true) ||
                (error is IllegalStateException && message.contains("user authentication", ignoreCase = true))
            ) {
                throw DeviceLockScreenRequiredException(
                    "Device secure lock screen must be configured before generating user-authenticated signing key.",
                    error
                )
            }
            throw DeviceKeyException(
                "Failed to generate Android Keystore key pair for alias '$keyAlias': ${error.message}",
                error
            )
        }

        return getKeySecurityMetadata()
    }

    override fun ensureSigningKey(requireUserAuthentication: Boolean): KeySecurityMetadata {
        if (hasSigningKey()) {
            val metadata = getKeySecurityMetadata()
            validateSigningKeyPolicy(metadata, requireUserAuthentication)
            return metadata
        }
        return generateSigningKey(requireUserAuthentication)
    }

    override fun rotateSigningKey(requireUserAuthentication: Boolean): KeySecurityMetadata {
        if (hasSigningKey() && !deleteSigningKey()) {
            throw DeviceKeyException("Failed to delete the existing signing key before rotation.")
        }
        return generateSigningKey(requireUserAuthentication)
    }

    private fun validateSigningKeyPolicy(
        metadata: KeySecurityMetadata,
        requireUserAuthentication: Boolean
    ) {
        val publicKey = try {
            getPublicKey()
        } catch (_: Throwable) {
            null
        }
        val violations = SigningKeyPolicyValidator.validate(
            metadata = metadata,
            requireUserAuthentication = requireUserAuthentication,
            publicKey = publicKey,
            apiLevel = Build.VERSION.SDK_INT
        )

        if (violations.isNotEmpty()) {
            throw SigningKeyPolicyViolationException(
                "Existing signing key '$keyAlias' is incompatible: ${violations.joinToString("; ")}. " +
                    "Explicit key regeneration and device re-enrollment are required."
            )
        }
    }

    override fun getPublicKey(): PublicKey {
        reloadKeyStore()
        val certificate = keyStore.getCertificate(keyAlias)
            ?: throw DeviceKeyNotFoundException("Certificate not found for key alias: $keyAlias")
        return certificate.publicKey
    }

    override fun getExportedPublicKey(): ExportedPublicKey {
        val publicKey = getPublicKey()
        val rawBytes = publicKey.encoded
            ?: throw DeviceKeyException("Public key did not return X.509 encoded bytes")

        val base64Encoded = Base64.getEncoder().encodeToString(rawBytes)

        val digest = MessageDigest.getInstance("SHA-256")
        val fingerprintBytes = digest.digest(rawBytes)
        val fingerprint = fingerprintBytes.joinToString(":") { "%02X".format(it) }

        // Confirm roundtrip parsing validation
        validatePublicKeyBytes(rawBytes)

        return ExportedPublicKey(
            alias = keyAlias,
            algorithm = publicKey.algorithm,
            format = publicKey.format ?: "X.509",
            curve = DeviceKeyManager.EC_CURVE,
            base64Encoded = base64Encoded,
            sha256Fingerprint = fingerprint
        )
    }

    override fun getPrivateKey(): PrivateKey {
        reloadKeyStore()
        val entry = keyStore.getEntry(keyAlias, null) as? KeyStore.PrivateKeyEntry
        val privateKey = entry?.privateKey ?: (keyStore.getKey(keyAlias, null) as? PrivateKey)
            ?: throw DeviceKeyNotFoundException("Private key entry not found for alias: $keyAlias")

        if (privateKey.encoded != null) {
            throw KeySecurityViolationException(
                "CRITICAL SECURITY VIOLATION: Private key is exportable (encoded bytes were non-null)!"
            )
        }
        return privateKey
    }

    override fun verifyPrivateKeyNonExportable(): Boolean {
        val privateKey = getPrivateKey()
        return privateKey.encoded == null
    }

    @Suppress("DEPRECATION")
    override fun getKeySecurityMetadata(): KeySecurityMetadata {
        val privateKey = getPrivateKey()
        val factory = KeyFactory.getInstance(
            privateKey.algorithm,
            DeviceKeyManager.KEYSTORE_PROVIDER
        )
        val keyInfo = factory.getKeySpec(privateKey, KeyInfo::class.java)

        val securityLevel = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            when (keyInfo.securityLevel) {
                KeyProperties.SECURITY_LEVEL_STRONGBOX -> KeySecurityLevel.STRONGBOX
                KeyProperties.SECURITY_LEVEL_TRUSTED_ENVIRONMENT -> KeySecurityLevel.TRUSTED_ENVIRONMENT
                KeyProperties.SECURITY_LEVEL_SOFTWARE -> KeySecurityLevel.SOFTWARE
                else -> KeySecurityLevel.UNKNOWN
            }
        } else {
            if (keyInfo.isInsideSecureHardware) {
                KeySecurityLevel.TRUSTED_ENVIRONMENT
            } else {
                KeySecurityLevel.SOFTWARE
            }
        }

        val userAuthTypes = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            try {
                keyInfo.userAuthenticationType
            } catch (_: Throwable) {
                0
            }
        } else {
            0
        }

        val isInvalidated = try {
            keyInfo.isInvalidatedByBiometricEnrollment
        } catch (_: Throwable) {
            null
        }

        return KeySecurityMetadata(
            alias = keyAlias,
            algorithm = privateKey.algorithm,
            keySize = keyInfo.keySize,
            curve = DeviceKeyManager.EC_CURVE,
            digests = keyInfo.digests.toList(),
            purposes = keyInfo.purposes,
            isInsideSecureHardware = keyInfo.isInsideSecureHardware,
            securityLevel = securityLevel,
            userAuthenticationRequired = keyInfo.isUserAuthenticationRequired,
            userAuthenticationValidityDurationSeconds = keyInfo.userAuthenticationValidityDurationSeconds,
            userAuthenticationTypes = userAuthTypes,
            isInvalidatedByBiometricEnrollment = isInvalidated,
            isNonExportable = (privateKey.encoded == null)
        )
    }

    override fun deleteSigningKey(): Boolean {
        reloadKeyStore()
        if (keyStore.containsAlias(keyAlias)) {
            keyStore.deleteEntry(keyAlias)
        }
        reloadKeyStore()
        return !keyStore.containsAlias(keyAlias)
    }

    override fun validatePublicKeyParsing(base64PublicKey: String): Boolean {
        val rawBytes = Base64.getDecoder().decode(base64PublicKey)
        return validatePublicKeyBytes(rawBytes)
    }

    private fun validatePublicKeyBytes(rawBytes: ByteArray): Boolean {
        val keySpec = X509EncodedKeySpec(rawBytes)
        val keyFactory = KeyFactory.getInstance(DeviceKeyManager.KEY_ALGORITHM)
        val reparsedKey = keyFactory.generatePublic(keySpec)
        if (reparsedKey.algorithm != DeviceKeyManager.KEY_ALGORITHM) {
            throw DeviceKeyException("Parsed key algorithm '${reparsedKey.algorithm}' does not match expected '${DeviceKeyManager.KEY_ALGORITHM}'")
        }
        return true
    }

    private fun reloadKeyStore() {
        try {
            keyStore.load(null)
        } catch (_: Throwable) {
            // Keep existing loaded state if reload throws
        }
    }
}
