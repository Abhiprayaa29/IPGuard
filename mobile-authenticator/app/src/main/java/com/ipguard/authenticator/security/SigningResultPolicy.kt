package com.ipguard.authenticator.security

sealed interface SigningOutcome {
    data class Verified(val result: SigningResult.Success) : SigningOutcome
    data class NonTerminal(val message: String) : SigningOutcome
    data class Terminal(val errorCode: Int, val message: String) : SigningOutcome
}

object SigningResultPolicy {
    fun classify(result: SigningResult): SigningOutcome {
        return when (result) {
            is SigningResult.Success -> {
                if (result.verifiedLocally) {
                    SigningOutcome.Verified(result)
                } else {
                    SigningOutcome.Terminal(
                        errorCode = SigningResult.ERROR_LOCAL_VERIFICATION_FAILED,
                        message = "Signature failed local verification. Approval is not valid."
                    )
                }
            }

            is SigningResult.AttemptFailed -> SigningOutcome.NonTerminal(result.message)
            is SigningResult.Cancelled -> SigningOutcome.Terminal(result.errorCode, result.message)
            is SigningResult.Error -> SigningOutcome.Terminal(result.errorCode, result.errorMessage)
        }
    }
}
