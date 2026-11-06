package com.ipguard.authenticator.ui.state

data class PreviewSignInRequest(
    val service: String = "IPGuard Console",
    val browser: String = "Chrome on Windows",
    val origin: String = "localhost:5173",
    val challenge: String = "ipguard_signin_challenge_m23b"
)

data class DeviceFacts(
    val model: String,
    val androidVersion: String,
    val appVersion: String
)

data class KeyDiagnosticState(
    val hasKey: Boolean = false,
    val alias: String = "",
    val algorithm: String = "",
    val curve: String = "",
    val securityLevel: String = "Not created",
    val userAuthentication: String = "Not created",
    val isNonExportable: Boolean = false,
    val fingerprint: String = "",
    val statusMessage: String? = null,
    val errorMessage: String? = null
)

data class AuthenticationPolicyState(
    val primaryAuthMethod: String = "Evaluating...",
    val biometricStatus: String = "Evaluating...",
    val credentialStatus: String = "Evaluating...",
    val policyExplanation: String = "",
    val isFingerprintMandatory: Boolean = false
)

data class SigningDiagnosticState(
    val hasSigned: Boolean = false,
    val challenge: String = "",
    val base64Signature: String = "",
    val authMethodLabel: String = "",
    val verifiedLocally: Boolean = false,
    val statusMessage: String? = null,
    val errorMessage: String? = null
)

data class AuthenticatorUiState(
    val deviceFacts: DeviceFacts,
    val previewRequest: PreviewSignInRequest = PreviewSignInRequest(),
    val trustedPhoneCount: Int = 0,
    val maximumTrustedPhones: Int = 1,
    val keyDiagnostic: KeyDiagnosticState = KeyDiagnosticState(),
    val authPolicy: AuthenticationPolicyState = AuthenticationPolicyState(),
    val signingDiagnostic: SigningDiagnosticState = SigningDiagnosticState()
)
