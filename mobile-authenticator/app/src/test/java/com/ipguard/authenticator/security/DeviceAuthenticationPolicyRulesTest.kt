package com.ipguard.authenticator.security

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class DeviceAuthenticationPolicyRulesTest {

    @Test
    fun deviceCredentialCryptoObjectIsUnsupportedBeforeApi30() {
        assertFalse(DeviceAuthenticationPolicy.canUseDeviceCredentialCryptoObject(apiLevel = 29))
    }

    @Test
    fun deviceCredentialCryptoObjectIsSupportedAtApi30() {
        assertTrue(DeviceAuthenticationPolicy.canUseDeviceCredentialCryptoObject(apiLevel = 30))
    }
}
