package com.ipguard.authenticator.security

import org.junit.Assert.assertNotEquals
import org.junit.Test
import java.security.PrivateKey
import java.security.PublicKey

class DeviceKeyVerificationRunnerTest {

    private class FakeKeyManager(override val alias: String) : DeviceKeyManager {
        override fun hasSigningKey(): Boolean = error("Runner touched the key manager")
        override fun generateSigningKey(requireUserAuthentication: Boolean): KeySecurityMetadata =
            error("Runner touched the key manager")

        override fun ensureSigningKey(requireUserAuthentication: Boolean): KeySecurityMetadata =
            error("Runner touched the key manager")

        override fun rotateSigningKey(requireUserAuthentication: Boolean): KeySecurityMetadata =
            error("Runner touched the key manager")

        override fun getKeySecurityMetadata(): KeySecurityMetadata =
            error("Runner touched the key manager")

        override fun getExportedPublicKey(): ExportedPublicKey =
            error("Runner touched the key manager")

        override fun getPublicKey(): PublicKey = error("Runner touched the key manager")
        override fun getPrivateKey(): PrivateKey = error("Runner touched the key manager")
        override fun verifyPrivateKeyNonExportable(): Boolean =
            error("Runner touched the key manager")

        override fun deleteSigningKey(): Boolean = error("Runner touched the key manager")
        override fun validatePublicKeyParsing(base64PublicKey: String): Boolean =
            error("Runner touched the key manager")
    }

    @Test
    fun testKeyAliasIsSeparateFromProduction() {
        assertNotEquals(DeviceKeyManager.KEY_ALIAS, DeviceKeyVerificationRunner.TEST_KEY_ALIAS)
    }

    @Test(expected = IllegalArgumentException::class)
    fun refusesToRunAgainstProductionAlias() {
        DeviceKeyVerificationRunner.runAll(
            deviceKeyManager = FakeKeyManager(DeviceKeyManager.KEY_ALIAS)
        )
    }
}
