package com.ipguard.authenticator.security

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class SigningResultPolicyTest {

    private fun success(verifiedLocally: Boolean): SigningResult.Success {
        return SigningResult.Success(
            challenge = "challenge".toByteArray(),
            signature = ByteArray(64),
            base64Signature = "c2lnbmF0dXJl",
            authenticationType = 1,
            authMethodLabel = "Device Credential",
            verifiedLocally = verifiedLocally
        )
    }

    @Test
    fun successWithLocalVerificationIsVerified() {
        val outcome = SigningResultPolicy.classify(success(verifiedLocally = true))

        assertTrue(outcome is SigningOutcome.Verified)
    }

    @Test
    fun successWithoutLocalVerificationIsTerminalFailure() {
        val outcome = SigningResultPolicy.classify(success(verifiedLocally = false))

        assertTrue(outcome is SigningOutcome.Terminal)
        assertEquals(
            SigningResult.ERROR_LOCAL_VERIFICATION_FAILED,
            (outcome as SigningOutcome.Terminal).errorCode
        )
    }

    @Test
    fun attemptFailedIsNonTerminal() {
        val outcome = SigningResultPolicy.classify(
            SigningResult.AttemptFailed("Try again.")
        )

        assertTrue(outcome is SigningOutcome.NonTerminal)
        assertEquals("Try again.", (outcome as SigningOutcome.NonTerminal).message)
    }

    @Test
    fun cancelledAndErrorAreTerminal() {
        val cancelled = SigningResultPolicy.classify(
            SigningResult.Cancelled(errorCode = 10, message = "Cancelled.")
        )
        val error = SigningResultPolicy.classify(
            SigningResult.Error(errorCode = 7, errorMessage = "Locked out.")
        )

        assertTrue(cancelled is SigningOutcome.Terminal)
        assertTrue(error is SigningOutcome.Terminal)
        assertEquals(10, (cancelled as SigningOutcome.Terminal).errorCode)
        assertEquals(7, (error as SigningOutcome.Terminal).errorCode)
    }
}
