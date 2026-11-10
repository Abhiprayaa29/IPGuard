package com.ipguard.authenticator.ui.state

import com.ipguard.authenticator.BuildConfig
import com.ipguard.authenticator.security.qr.QrAuthPayload

data class PreviewSignInRequest(
    val service: String = "IPGuard Console",
    val browser: String = "Web Client",
    val origin: String = "http://localhost:5173",
    val challenge: String = "ipguard_signin_challenge_m23b"
)

data class DeviceFacts(
    val model: String,
    val androidVersion: String,
    val appVersion: String,
    val versionCode: Int = BuildConfig.VERSION_CODE,
    val applicationId: String = BuildConfig.APPLICATION_ID
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

enum class BackendConnectionStatus {
    CHECKING,
    CONNECTED,
    UNAVAILABLE
}

data class BackendConnectionState(
    val status: BackendConnectionStatus = BackendConnectionStatus.CHECKING,
    val apiEndpoint: String = BuildConfig.API_BASE_URL,
    val statusLabel: String = "Checking connection...",
    val detailMessage: String? = null,
    val lastSyncedLabel: String? = null
)

data class SecurityActivityEntry(
    val timestampLabel: String,
    val title: String,
    val detail: String,
    val isPositive: Boolean = true
)

enum class FaceGateStatus {
    READY,
    AUTHENTICATING,
    PASSED,
    FAILED,
    LOCKED_OUT,
    UNAVAILABLE
}

data class FaceGateState(
    val availabilityLabel: String = "Evaluating...",
    val isWeakBiometricAvailable: Boolean = false,
    val isNotEnrolled: Boolean = false,
    val status: FaceGateStatus = FaceGateStatus.READY,
    val statusMessage: String? = null,
    val errorMessage: String? = null,
    val fallbackAuthorized: Boolean = false
)

enum class AuthFlowStep {
    IDLE,
    PAYLOAD_VALIDATED,
    AWAITING_USER_CONSENT,
    AWAITING_DEVICE_AUTHENTICATION,
    SIGNING,
    SUBMITTING_BACKEND,
    COMPLETED_APPROVED,
    COMPLETED_REJECTED,
    FAILED
}

data class ActiveAuthSessionState(
    val step: AuthFlowStep = AuthFlowStep.IDLE,
    val payload: QrAuthPayload? = null,
    val statusMessage: String? = null,
    val errorMessage: String? = null
)

data class AuthenticatorUiState(
    val deviceFacts: DeviceFacts,
    val previewRequest: PreviewSignInRequest = PreviewSignInRequest(),
    val trustedPhoneCount: Int = 0,
    val maximumTrustedPhones: Int = 1,
    val isRegistered: Boolean = false,
    val registrationStatus: String = "UNREGISTERED",
    val deviceId: String = "",
    val isSyncingBackend: Boolean = false,
    val connectionState: BackendConnectionState = BackendConnectionState(),
    val activityLog: List<SecurityActivityEntry> = emptyList(),
    val keyDiagnostic: KeyDiagnosticState = KeyDiagnosticState(),
    val authPolicy: AuthenticationPolicyState = AuthenticationPolicyState(),
    val signingDiagnostic: SigningDiagnosticState = SigningDiagnosticState(),
    val faceGate: FaceGateState = FaceGateState(),
    val activeSession: ActiveAuthSessionState = ActiveAuthSessionState()
)
