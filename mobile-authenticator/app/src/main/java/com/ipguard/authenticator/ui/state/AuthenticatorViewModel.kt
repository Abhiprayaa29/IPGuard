package com.ipguard.authenticator.ui.state

import android.app.Application
import android.os.Build
import androidx.fragment.app.FragmentActivity
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.ipguard.authenticator.BuildConfig
import com.ipguard.authenticator.R
import com.ipguard.authenticator.network.ApiResult
import com.ipguard.authenticator.network.AuthApiService
import com.ipguard.authenticator.network.OkHttpAuthApiService
import com.ipguard.authenticator.network.RegisterDeviceRequest
import com.ipguard.authenticator.network.VerifySessionRequest
import com.ipguard.authenticator.security.AndroidKeystoreDeviceKeyManager
import com.ipguard.authenticator.security.DeviceAuthenticationPolicy
import com.ipguard.authenticator.security.DeviceIdManager
import com.ipguard.authenticator.security.DeviceKeyManager
import com.ipguard.authenticator.security.DeviceKeyVerificationRunner
import com.ipguard.authenticator.security.DeviceKeyException
import com.ipguard.authenticator.security.DeviceLockScreenRequiredException
import com.ipguard.authenticator.security.DeviceSigningAuthenticator
import com.ipguard.authenticator.security.FullVerificationSuiteResult
import com.ipguard.authenticator.security.SigningKeyPolicyViolationException
import com.ipguard.authenticator.security.SigningOutcome
import com.ipguard.authenticator.security.SigningResult
import com.ipguard.authenticator.security.SigningResultPolicy
import com.ipguard.authenticator.security.qr.QrAuthPayload
import com.ipguard.authenticator.security.qr.QrAuthPayloadParser
import com.ipguard.authenticator.security.qr.QrPayloadValidationResult
import com.ipguard.authenticator.security.qr.QrSessionType
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

class AuthenticatorViewModel @JvmOverloads constructor(
    application: Application,
    private val keyManager: DeviceKeyManager = AndroidKeystoreDeviceKeyManager(),
    private val authenticator: DeviceSigningAuthenticator = DeviceSigningAuthenticator(keyManager),
    private val apiService: AuthApiService = OkHttpAuthApiService(),
    private val qrParser: QrAuthPayloadParser = QrAuthPayloadParser()
) : AndroidViewModel(application) {

    private val deviceIdManager = DeviceIdManager(application)

    private val _uiState = MutableStateFlow(
        AuthenticatorUiState(
            deviceFacts = DeviceFacts(
                model = deviceModel(),
                androidVersion = "${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})",
                appVersion = "${BuildConfig.VERSION_NAME} (${BuildConfig.VERSION_CODE})"
            )
        )
    )

    val uiState = _uiState.asStateFlow()

    init {
        refreshAll()
    }

    fun refreshAll() {
        refreshAuthPolicy()
        refreshKeyDiagnostic()
    }

    fun refreshAuthPolicy() {
        try {
            val policy = DeviceAuthenticationPolicy.evaluate(getApplication())
            _uiState.update { current ->
                current.copy(
                    authPolicy = AuthenticationPolicyState(
                        primaryAuthMethod = getString(policy.primaryAuthMethod.labelRes),
                        biometricStatus = policy.biometricStrongLabel,
                        credentialStatus = policy.deviceCredentialLabel,
                        policyExplanation = policy.explanation,
                        isFingerprintMandatory = false
                    )
                )
            }
        } catch (e: Throwable) {
            _uiState.update { current ->
                current.copy(
                    authPolicy = current.authPolicy.copy(
                        policyExplanation = getString(
                            R.string.device_policy_evaluation_error,
                            e.message ?: e.javaClass.simpleName
                        )
                    )
                )
            }
        }
    }

    fun refreshKeyDiagnostic() {
        try {
            if (keyManager.hasSigningKey()) {
                val metadata = keyManager.getKeySecurityMetadata()
                val exported = keyManager.getExportedPublicKey()
                _uiState.update { current ->
                    current.copy(
                        keyDiagnostic = KeyDiagnosticState(
                            hasKey = true,
                            alias = metadata.alias,
                            algorithm = "${metadata.algorithm} (${metadata.keySize}-bit)",
                            curve = metadata.curve,
                            securityLevel = metadata.securityLevel.label,
                            userAuthentication = if (metadata.userAuthenticationRequired) {
                                getString(R.string.device_user_auth_required_value)
                            } else {
                                getString(R.string.device_user_auth_none_value)
                            },
                            isNonExportable = metadata.isNonExportable,
                            fingerprint = exported.sha256Fingerprint,
                            statusMessage = getString(R.string.device_key_active_status),
                            errorMessage = null
                        )
                    )
                }
            } else {
                _uiState.update { current ->
                    current.copy(
                        keyDiagnostic = KeyDiagnosticState(
                            hasKey = false,
                            statusMessage = getString(R.string.device_key_missing_status),
                            errorMessage = null
                        )
                    )
                }
            }
        } catch (e: Throwable) {
            _uiState.update { current ->
                current.copy(
                    keyDiagnostic = current.keyDiagnostic.copy(
                        statusMessage = null,
                        errorMessage = "${e.javaClass.simpleName}: ${e.message}"
                    )
                )
            }
        }
    }

    fun generateSigningKey(requireUserAuth: Boolean = true) {
        try {
            if (keyManager.hasSigningKey()) {
                throw SigningKeyPolicyViolationException(
                    getString(R.string.key_generate_requires_rotation)
                )
            }
            keyManager.generateSigningKey(requireUserAuth)
            refreshAll()
        } catch (e: Throwable) {
            _uiState.update { current ->
                current.copy(
                    keyDiagnostic = current.keyDiagnostic.copy(
                        errorMessage = "${e.javaClass.simpleName}: ${e.message}"
                    )
                )
            }
        }
    }

    fun regenerateSigningKey(requireUserAuth: Boolean = true) {
        try {
            keyManager.rotateSigningKey(requireUserAuth)
            refreshAll()
        } catch (e: Throwable) {
            _uiState.update { current ->
                current.copy(
                    keyDiagnostic = current.keyDiagnostic.copy(
                        errorMessage = "${e.javaClass.simpleName}: ${e.message}"
                    )
                )
            }
        }
    }

    fun deleteSigningKey() {
        try {
            keyManager.deleteSigningKey()
            refreshAll()
        } catch (e: Throwable) {
            _uiState.update { current ->
                current.copy(
                    keyDiagnostic = current.keyDiagnostic.copy(
                        errorMessage = "${e.javaClass.simpleName}: ${e.message}"
                    )
                )
            }
        }
    }

    fun onQrCodeScanned(
        rawBarcode: String,
        onValid: (QrAuthPayload) -> Unit,
        onInvalid: (String) -> Unit
    ) {
        when (val result = qrParser.parse(rawBarcode)) {
            is QrPayloadValidationResult.Valid -> {
                val payload = result.payload
                val request = PreviewSignInRequest(
                    service = "IPGuard Console",
                    browser = "Web Client",
                    origin = payload.origin,
                    challenge = payload.buildCanonicalPayload()
                )
                _uiState.update { current ->
                    current.copy(
                        previewRequest = request,
                        activeSession = ActiveAuthSessionState(
                            step = AuthFlowStep.AWAITING_USER_CONSENT,
                            payload = payload,
                            statusMessage = getString(R.string.scanner_qr_validated),
                            errorMessage = null
                        )
                    )
                }

                // Fire non-blocking scan notification to backend
                viewModelScope.launch {
                    val deviceId = deviceIdManager.getOrCreateDeviceId()
                    apiService.scanSession(payload.sessionToken, deviceId)
                }

                onValid(payload)
            }
            is QrPayloadValidationResult.Invalid -> {
                _uiState.update { current ->
                    current.copy(
                        activeSession = ActiveAuthSessionState(
                            step = AuthFlowStep.FAILED,
                            errorMessage = result.reason
                        )
                    )
                }
                onInvalid(result.reason)
            }
        }
    }

    fun approveAndExecuteAuth(
        activity: FragmentActivity,
        onCompleted: (Boolean) -> Unit
    ) {
        val payload = _uiState.value.activeSession.payload
        if (payload == null) {
            _uiState.update { current ->
                current.copy(
                    activeSession = current.activeSession.copy(
                        step = AuthFlowStep.FAILED,
                        errorMessage = "No active QR session found to approve."
                    )
                )
            }
            onCompleted(false)
            return
        }

        // Fork handling: ENROLLMENT vs AUTHENTICATION
        when (payload.type) {
            QrSessionType.ENROLLMENT -> {
                if (!keyManager.hasSigningKey()) {
                    try {
                        keyManager.ensureSigningKey(requireUserAuthentication = true)
                        refreshKeyDiagnostic()
                    } catch (e: DeviceLockScreenRequiredException) {
                        _uiState.update { current ->
                            current.copy(
                                activeSession = current.activeSession.copy(
                                    step = AuthFlowStep.FAILED,
                                    errorMessage = e.message ?: getString(R.string.policy_explanation_no_lock)
                                )
                            )
                        }
                        onCompleted(false)
                        return
                    } catch (e: Throwable) {
                        _uiState.update { current ->
                            current.copy(
                                activeSession = current.activeSession.copy(
                                    step = AuthFlowStep.FAILED,
                                    errorMessage = "Failed to initialize device signing key: ${e.message ?: e.javaClass.simpleName}"
                                )
                            )
                        }
                        onCompleted(false)
                        return
                    }
                }

                if (!keyManager.hasSigningKey()) {
                    _uiState.update { current ->
                        current.copy(
                            activeSession = current.activeSession.copy(
                                step = AuthFlowStep.FAILED,
                                errorMessage = "Device signing key initialization failed verification."
                            )
                        )
                    }
                    onCompleted(false)
                    return
                }
            }
            QrSessionType.AUTHENTICATION -> {
                if (!keyManager.hasSigningKey()) {
                    _uiState.update { current ->
                        current.copy(
                            activeSession = current.activeSession.copy(
                                step = AuthFlowStep.FAILED,
                                errorMessage = "Device signing key is not initialized. Please enroll this device first."
                            )
                        )
                    }
                    onCompleted(false)
                    return
                }
            }
        }

        val canonicalPayload = payload.buildCanonicalPayload()
        val challengeBytes = payload.getCanonicalBytes()

        _uiState.update { current ->
            current.copy(
                activeSession = current.activeSession.copy(
                    step = AuthFlowStep.AWAITING_DEVICE_AUTHENTICATION,
                    statusMessage = getString(R.string.signing_awaiting_auth)
                )
            )
        }

        val promptTitle = when (payload.type) {
            QrSessionType.AUTHENTICATION -> getString(R.string.signing_prompt_title)
            QrSessionType.ENROLLMENT -> getString(R.string.auth_request_enrollment_title)
        }
        val promptSubtitle = "Approve for ${payload.origin}"

        authenticator.authenticateAndSign(
            activity = activity,
            challenge = challengeBytes,
            promptTitle = promptTitle,
            promptSubtitle = promptSubtitle,
            onResult = { result ->
                when (val outcome = SigningResultPolicy.classify(result)) {
                    is SigningOutcome.Verified -> {
                        val success = outcome.result
                        _uiState.update { current ->
                            current.copy(
                                activeSession = current.activeSession.copy(
                                    step = AuthFlowStep.SUBMITTING_BACKEND,
                                    statusMessage = "Submitting signature to backend..."
                                ),
                                signingDiagnostic = SigningDiagnosticState(
                                    hasSigned = true,
                                    challenge = canonicalPayload,
                                    base64Signature = success.base64Signature,
                                    authMethodLabel = success.authMethodLabel,
                                    verifiedLocally = true,
                                    statusMessage = getString(
                                        R.string.signing_verified,
                                        success.authMethodLabel
                                    ),
                                    errorMessage = null
                                )
                            )
                        }

                        // Submit to backend asynchronously
                        viewModelScope.launch {
                            val deviceId = deviceIdManager.getOrCreateDeviceId()
                            when (payload.type) {
                                QrSessionType.AUTHENTICATION -> {
                                    try {
                                        val apiResult = apiService.verifySession(
                                            sessionToken = payload.sessionToken,
                                            request = VerifySessionRequest(
                                                deviceId = deviceId,
                                                canonicalPayload = canonicalPayload,
                                                signature = success.base64Signature
                                            )
                                        )
                                        when (apiResult) {
                                            is ApiResult.Success -> {
                                                _uiState.update { current ->
                                                    current.copy(
                                                        activeSession = current.activeSession.copy(
                                                            step = AuthFlowStep.COMPLETED_APPROVED,
                                                            statusMessage = "Authentication approved by backend.",
                                                            errorMessage = null
                                                        )
                                                    )
                                                }
                                                onCompleted(true)
                                            }
                                            is ApiResult.HttpError -> {
                                                _uiState.update { current ->
                                                    current.copy(
                                                        activeSession = current.activeSession.copy(
                                                            step = AuthFlowStep.FAILED,
                                                            errorMessage = "Backend rejected signature: ${apiResult.message}"
                                                        )
                                                    )
                                                }
                                                onCompleted(false)
                                            }
                                            is ApiResult.NetworkError -> {
                                                _uiState.update { current ->
                                                    current.copy(
                                                        activeSession = current.activeSession.copy(
                                                            step = AuthFlowStep.FAILED,
                                                            errorMessage = "Network connection failed: ${apiResult.message}"
                                                        )
                                                    )
                                                }
                                                onCompleted(false)
                                            }
                                        }
                                    } catch (e: Throwable) {
                                        _uiState.update { current ->
                                            current.copy(
                                                activeSession = current.activeSession.copy(
                                                    step = AuthFlowStep.FAILED,
                                                    errorMessage = "Authentication failed: ${e.message ?: e.javaClass.simpleName}"
                                                )
                                            )
                                        }
                                        onCompleted(false)
                                    }
                                }
                                QrSessionType.ENROLLMENT -> {
                                    try {
                                        val exportedKey = keyManager.getExportedPublicKey()
                                        val metadata = keyManager.getKeySecurityMetadata()
                                        val apiResult = apiService.registerDevice(
                                            RegisterDeviceRequest(
                                                sessionToken = payload.sessionToken,
                                                deviceId = deviceId,
                                                deviceName = deviceModel(),
                                                model = Build.MODEL,
                                                androidVersion = Build.VERSION.RELEASE,
                                                publicKeyX509 = exportedKey.base64Encoded,
                                                securityLevel = metadata.securityLevel.name,
                                                canonicalPayload = canonicalPayload,
                                                signature = success.base64Signature
                                            )
                                        )
                                        when (apiResult) {
                                            is ApiResult.Success -> {
                                                _uiState.update { current ->
                                                    current.copy(
                                                        trustedPhoneCount = 1,
                                                        activeSession = current.activeSession.copy(
                                                            step = AuthFlowStep.COMPLETED_APPROVED,
                                                            statusMessage = "Device successfully enrolled in backend.",
                                                            errorMessage = null
                                                        )
                                                    )
                                                }
                                                onCompleted(true)
                                            }
                                            is ApiResult.HttpError -> {
                                                _uiState.update { current ->
                                                    current.copy(
                                                        activeSession = current.activeSession.copy(
                                                            step = AuthFlowStep.FAILED,
                                                            errorMessage = "Registration rejected: ${apiResult.message}"
                                                        )
                                                    )
                                                }
                                                onCompleted(false)
                                            }
                                            is ApiResult.NetworkError -> {
                                                _uiState.update { current ->
                                                    current.copy(
                                                        activeSession = current.activeSession.copy(
                                                            step = AuthFlowStep.FAILED,
                                                            errorMessage = "Network error: ${apiResult.message}"
                                                        )
                                                    )
                                                }
                                                onCompleted(false)
                                            }
                                        }
                                    } catch (e: Throwable) {
                                        _uiState.update { current ->
                                            current.copy(
                                                activeSession = current.activeSession.copy(
                                                    step = AuthFlowStep.FAILED,
                                                    errorMessage = "Registration failed: ${e.message ?: e.javaClass.simpleName}"
                                                )
                                            )
                                        }
                                        onCompleted(false)
                                    }
                                }
                            }
                        }
                    }
                    is SigningOutcome.NonTerminal -> {
                        _uiState.update { current ->
                            current.copy(
                                activeSession = current.activeSession.copy(
                                    statusMessage = if (result is SigningResult.AttemptFailed) {
                                        getString(R.string.signing_attempt_failed)
                                    } else {
                                        outcome.message
                                    }
                                )
                            )
                        }
                    }
                    is SigningOutcome.Terminal -> {
                        val message = if (result is SigningResult.Cancelled) {
                            getString(R.string.signing_cancelled)
                        } else {
                            getString(R.string.signing_failed, outcome.message, outcome.errorCode)
                        }
                        _uiState.update { current ->
                            current.copy(
                                activeSession = current.activeSession.copy(
                                    step = AuthFlowStep.COMPLETED_REJECTED,
                                    errorMessage = message
                                )
                            )
                        }
                        onCompleted(false)
                    }
                }
            }
        )
    }

    fun cancelActiveSession() {
        _uiState.update { current ->
            current.copy(
                activeSession = ActiveAuthSessionState(step = AuthFlowStep.IDLE)
            )
        }
    }

    fun authenticateAndSign(
        activity: FragmentActivity,
        challenge: ByteArray,
        onSuccess: (SigningResult.Success) -> Unit = {}
    ) {
        _uiState.update { current ->
            current.copy(
                signingDiagnostic = SigningDiagnosticState(
                    statusMessage = getString(R.string.signing_awaiting_auth)
                )
            )
        }

        authenticator.authenticateAndSign(
            activity = activity,
            challenge = challenge,
            promptTitle = getString(R.string.signing_prompt_title),
            promptSubtitle = getString(R.string.signing_prompt_subtitle),
            onResult = { result ->
                when (val outcome = SigningResultPolicy.classify(result)) {
                    is SigningOutcome.Verified -> {
                        val success = outcome.result
                        _uiState.update { current ->
                            current.copy(
                                signingDiagnostic = SigningDiagnosticState(
                                    hasSigned = true,
                                    challenge = challenge.decodeToString(),
                                    base64Signature = success.base64Signature,
                                    authMethodLabel = success.authMethodLabel,
                                    verifiedLocally = true,
                                    statusMessage = getString(
                                        R.string.signing_verified,
                                        success.authMethodLabel
                                    ),
                                    errorMessage = null
                                )
                            )
                        }
                        onSuccess(success)
                    }

                    is SigningOutcome.NonTerminal -> {
                        _uiState.update { current ->
                            current.copy(
                                signingDiagnostic = current.signingDiagnostic.copy(
                                    statusMessage = if (result is SigningResult.AttemptFailed) {
                                        getString(R.string.signing_attempt_failed)
                                    } else {
                                        outcome.message
                                    },
                                    errorMessage = null
                                )
                            )
                        }
                    }

                    is SigningOutcome.Terminal -> {
                        val message = if (result is SigningResult.Cancelled) {
                            getString(R.string.signing_cancelled)
                        } else {
                            getString(R.string.signing_failed, outcome.message, outcome.errorCode)
                        }
                        _uiState.update { current ->
                            current.copy(
                                signingDiagnostic = current.signingDiagnostic.copy(
                                    statusMessage = null,
                                    errorMessage = message
                                )
                            )
                        }
                    }
                }
            }
        )
    }

    fun reportApprovalHostUnavailable() {
        _uiState.update { current ->
            current.copy(
                signingDiagnostic = SigningDiagnosticState(
                    errorMessage = getString(R.string.approval_host_unavailable)
                )
            )
        }
    }

    private fun getString(resId: Int, vararg formatArgs: Any): String {
        return getApplication<Application>().getString(resId, *formatArgs)
    }

    fun runVerificationSuite(requireUserAuth: Boolean = true): FullVerificationSuiteResult {
        val result = DeviceKeyVerificationRunner.runAll(
            requireUserAuthentication = requireUserAuth
        )
        refreshAll()
        return result
    }

    private fun deviceModel(): String {
        val manufacturer = Build.MANUFACTURER
            .replaceFirstChar { if (it.isLowerCase()) it.titlecase() else it.toString() }
        return "$manufacturer ${Build.MODEL}"
    }
}
