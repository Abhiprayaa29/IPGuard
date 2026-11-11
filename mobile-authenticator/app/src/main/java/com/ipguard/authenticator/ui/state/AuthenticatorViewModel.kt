package com.ipguard.authenticator.ui.state

import android.app.Application
import android.os.Build
import android.util.Log
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
import com.ipguard.authenticator.security.BiometricFaceGateManager
import com.ipguard.authenticator.security.DeviceAuthenticationPolicy
import com.ipguard.authenticator.security.DeviceIdManager
import com.ipguard.authenticator.security.DeviceKeyManager
import com.ipguard.authenticator.security.DeviceKeyVerificationRunner
import com.ipguard.authenticator.security.DeviceKeyException
import com.ipguard.authenticator.security.DeviceLockScreenRequiredException
import com.ipguard.authenticator.security.DeviceRegistrationManager
import com.ipguard.authenticator.security.DeviceRegistrationStatus
import com.ipguard.authenticator.security.DeviceSigningAuthenticator
import com.ipguard.authenticator.security.FaceGateAvailability
import com.ipguard.authenticator.security.FaceGateResult
import com.ipguard.authenticator.security.FullVerificationSuiteResult
import com.ipguard.authenticator.security.SigningKeyPolicyViolationException
import com.ipguard.authenticator.security.SigningOutcome
import com.ipguard.authenticator.security.SigningResult
import com.ipguard.authenticator.security.SigningResultPolicy
import com.ipguard.authenticator.security.qr.QrAuthPayload
import com.ipguard.authenticator.security.qr.QrAuthPayloadParser
import com.ipguard.authenticator.security.qr.QrPayloadValidationResult
import com.ipguard.authenticator.security.qr.QrSessionType
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

class AuthenticatorViewModel @JvmOverloads constructor(
    application: Application,
    private val keyManager: DeviceKeyManager = AndroidKeystoreDeviceKeyManager(),
    private val authenticator: DeviceSigningAuthenticator = DeviceSigningAuthenticator(keyManager),
    private val apiService: AuthApiService = OkHttpAuthApiService(),
    private val qrParser: QrAuthPayloadParser = QrAuthPayloadParser(),
    private val registrationManager: DeviceRegistrationManager = DeviceRegistrationManager(application),
    private val faceGateManager: BiometricFaceGateManager = BiometricFaceGateManager()
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
        syncRegistrationWithBackend()
    }

    fun refreshAll() {
        val devId = deviceIdManager.getOrCreateDeviceId()
        val isReg = registrationManager.isRegistered()
        val regStatus = registrationManager.getRegistrationStatus()
        _uiState.update { current ->
            current.copy(
                deviceId = devId,
                isRegistered = isReg,
                registrationStatus = regStatus.name,
                trustedPhoneCount = if (isReg) 1 else 0
            )
        }
        refreshAuthPolicy()
        refreshKeyDiagnostic()
    }

    fun syncRegistrationWithBackend() {
        viewModelScope.launch {
            _uiState.update { current ->
                current.copy(
                    isSyncingBackend = true,
                    connectionState = current.connectionState.copy(
                        status = BackendConnectionStatus.CHECKING,
                        statusLabel = "Verifying backend..."
                    )
                )
            }
            val nowLabel = currentTimeLabel()
            try {
                val healthResult = apiService.checkHealth()
                if (healthResult is ApiResult.NetworkError || healthResult is ApiResult.HttpError) {
                    val reason = when (healthResult) {
                        is ApiResult.NetworkError -> healthResult.message
                        is ApiResult.HttpError -> "HTTP ${healthResult.code}: ${healthResult.message}"
                        else -> "Backend unreachable"
                    }
                    _uiState.update { current ->
                        current.copy(
                            isSyncingBackend = false,
                            connectionState = current.connectionState.copy(
                                status = BackendConnectionStatus.UNAVAILABLE,
                                statusLabel = "Offline / Unreachable",
                                detailMessage = reason,
                                lastSyncedLabel = nowLabel
                            )
                        )
                    }
                    return@launch
                }

                val deviceId = deviceIdManager.getOrCreateDeviceId()
                when (val result = apiService.checkDeviceStatus(deviceId)) {
                    is ApiResult.Success -> {
                        val effectiveStatus = when {
                            result.data.registrationStatus.equals("UNREGISTERED", ignoreCase = true) -> "UNREGISTERED"
                            result.data.status.equals("REVOKED", ignoreCase = true) -> "REVOKED"
                            result.data.status.equals("ACTIVE", ignoreCase = true) -> "ACTIVE"
                            else -> result.data.registrationStatus
                        }
                        if (effectiveStatus == "UNREGISTERED") {
                            registrationManager.clearRegistration()
                            _uiState.update { current ->
                                current.copy(
                                    isRegistered = false,
                                    registrationStatus = "UNREGISTERED",
                                    trustedPhoneCount = 0,
                                    isSyncingBackend = false,
                                    connectionState = current.connectionState.copy(
                                        status = BackendConnectionStatus.CONNECTED,
                                        statusLabel = "Connected (TLS / Localhost)",
                                        detailMessage = null,
                                        lastSyncedLabel = nowLabel
                                    )
                                )
                            }
                        } else if (effectiveStatus == "ACTIVE" || effectiveStatus == "REVOKED") {
                            val regStatus = if (effectiveStatus == "ACTIVE") {
                                DeviceRegistrationStatus.ACTIVE
                            } else {
                                DeviceRegistrationStatus.REVOKED
                            }
                            registrationManager.setRegistrationStatus(regStatus)
                            _uiState.update { current ->
                                current.copy(
                                    isRegistered = true,
                                    registrationStatus = regStatus.name,
                                    trustedPhoneCount = 1,
                                    isSyncingBackend = false,
                                    connectionState = current.connectionState.copy(
                                        status = BackendConnectionStatus.CONNECTED,
                                        statusLabel = "Connected (TLS / Localhost)",
                                        detailMessage = null,
                                        lastSyncedLabel = nowLabel
                                    )
                                )
                            }
                        } else {
                            _uiState.update { current ->
                                current.copy(
                                    isSyncingBackend = false,
                                    connectionState = current.connectionState.copy(
                                        status = BackendConnectionStatus.CONNECTED,
                                        statusLabel = "Connected",
                                        detailMessage = null,
                                        lastSyncedLabel = nowLabel
                                    )
                                )
                            }
                        }
                        appendActivity("Backend Status Sync", "Status confirmed: $effectiveStatus", effectiveStatus == "ACTIVE")
                    }
                    is ApiResult.HttpError -> {
                        _uiState.update { current ->
                            current.copy(
                                isSyncingBackend = false,
                                connectionState = current.connectionState.copy(
                                    status = BackendConnectionStatus.UNAVAILABLE,
                                    statusLabel = "Backend Error (${result.code})",
                                    detailMessage = result.message,
                                    lastSyncedLabel = nowLabel
                                )
                            )
                        }
                    }
                    is ApiResult.NetworkError -> {
                        _uiState.update { current ->
                            current.copy(
                                isSyncingBackend = false,
                                connectionState = current.connectionState.copy(
                                    status = BackendConnectionStatus.UNAVAILABLE,
                                    statusLabel = "Offline / Timeout",
                                    detailMessage = result.message,
                                    lastSyncedLabel = nowLabel
                                )
                            )
                        }
                    }
                }
            } catch (e: Throwable) {
                _uiState.update { current ->
                    current.copy(
                        isSyncingBackend = false,
                        connectionState = current.connectionState.copy(
                            status = BackendConnectionStatus.UNAVAILABLE,
                            statusLabel = "Offline",
                            detailMessage = e.message ?: e.javaClass.simpleName,
                            lastSyncedLabel = nowLabel
                        )
                    )
                }
            }
        }
    }

    private fun evaluateFaceGateState(preserveProgress: Boolean = false): FaceGateState {
        val current = _uiState.value.faceGate
        return when (val availability = faceGateManager.evaluateAvailability(getApplication())) {
            is FaceGateAvailability.Available -> {
                val keepStatus = preserveProgress && (
                    current.status == FaceGateStatus.PASSED ||
                        current.status == FaceGateStatus.AUTHENTICATING
                    )
                FaceGateState(
                    availabilityLabel = "BIOMETRIC_WEAK Available",
                    isWeakBiometricAvailable = true,
                    isNotEnrolled = false,
                    status = if (keepStatus) current.status else FaceGateStatus.READY,
                    statusMessage = if (keepStatus) current.statusMessage else null,
                    errorMessage = if (keepStatus) current.errorMessage else null,
                    fallbackAuthorized = false
                )
            }
            is FaceGateAvailability.NotEnrolled -> FaceGateState(
                availabilityLabel = "Not Enrolled",
                isWeakBiometricAvailable = false,
                isNotEnrolled = true,
                status = FaceGateStatus.UNAVAILABLE,
                statusMessage = null,
                errorMessage = availability.reason,
                fallbackAuthorized = current.fallbackAuthorized
            )
            is FaceGateAvailability.Unavailable -> FaceGateState(
                availabilityLabel = "Not Supported",
                isWeakBiometricAvailable = false,
                isNotEnrolled = false,
                status = FaceGateStatus.UNAVAILABLE,
                statusMessage = null,
                errorMessage = availability.reason,
                fallbackAuthorized = current.fallbackAuthorized
            )
        }
    }

    fun refreshAuthPolicy() {
        try {
            val policy = DeviceAuthenticationPolicy.evaluate(getApplication())
            val nextFaceGate = evaluateFaceGateState(preserveProgress = true)
            _uiState.update { current ->
                current.copy(
                    authPolicy = AuthenticationPolicyState(
                        primaryAuthMethod = getString(policy.primaryAuthMethod.labelRes),
                        biometricStatus = policy.biometricStrongLabel,
                        credentialStatus = policy.deviceCredentialLabel,
                        policyExplanation = policy.explanation,
                        isFingerprintMandatory = false
                    ),
                    faceGate = nextFaceGate
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
            val isReg = registrationManager.isRegistered()
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
                            statusMessage = if (isReg) {
                                "Signing key missing from Keystore while device is registered. Unregister from Web Console to re-enroll."
                            } else {
                                getString(R.string.device_key_missing_status)
                            },
                            errorMessage = if (isReg) {
                                "Signing key is missing from Android Keystore. This device must be unregistered from the web console before you can set it up again."
                            } else null
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
            if (registrationManager.isRegistered()) {
                throw SigningKeyPolicyViolationException(
                    "Device is already registered. To change the signing key, unregister the device from the web console first."
                )
            }
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
            if (registrationManager.isRegistered()) {
                throw SigningKeyPolicyViolationException(
                    "Device is already registered. Regenerating the key will break sign-in. Unregister first from the web console."
                )
            }
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
            if (registrationManager.isRegistered()) {
                throw SigningKeyPolicyViolationException(
                    "Device is already registered. Deleting the key will break sign-in. Unregister first from the web console."
                )
            }
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
                if (payload.type == QrSessionType.ENROLLMENT && registrationManager.isRegistered()) {
                    val errMsg = "Device Already Registered. This device is already linked to IPGuard. Please use Sign In."
                    _uiState.update { current ->
                        current.copy(
                            activeSession = ActiveAuthSessionState(
                                step = AuthFlowStep.FAILED,
                                errorMessage = errMsg
                            )
                        )
                    }
                    onInvalid(errMsg)
                    return
                }

                val request = PreviewSignInRequest(
                    service = "IPGuard Console",
                    browser = "Web Client",
                    origin = payload.origin,
                    challenge = payload.buildCanonicalPayload()
                )
                val resetFaceGate = evaluateFaceGateState(preserveProgress = false)
                _uiState.update { current ->
                    current.copy(
                        previewRequest = request,
                        faceGate = resetFaceGate,
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
                appendActivity(
                    "QR Challenge Detected",
                    "${payload.type.name} for ${payload.origin}",
                    true
                )
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
        val snapshot = _uiState.value
        if (snapshot.faceGate.status == FaceGateStatus.AUTHENTICATING ||
            snapshot.activeSession.step == AuthFlowStep.AWAITING_DEVICE_AUTHENTICATION ||
            snapshot.activeSession.step == AuthFlowStep.SUBMITTING_BACKEND
        ) {
            return
        }

        val payload = snapshot.activeSession.payload
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
                if (registrationManager.isRegistered()) {
                    _uiState.update { current ->
                        current.copy(
                            activeSession = current.activeSession.copy(
                                step = AuthFlowStep.FAILED,
                                errorMessage = "Perangkat ini sudah terdaftar di IPGuard. Silakan gunakan Sign In untuk melanjutkan."
                            )
                        )
                    }
                    onCompleted(false)
                    return
                }

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

        val faceGateState = evaluateFaceGateState(preserveProgress = true)
        _uiState.update { current -> current.copy(faceGate = faceGateState) }

        if (faceGateState.isWeakBiometricAvailable) {
            if (faceGateState.status == FaceGateStatus.PASSED) {
                executeCryptoSigningAndSubmit(activity, payload, onCompleted)
                return
            }

            _uiState.update { current ->
                current.copy(
                    faceGate = current.faceGate.copy(
                        status = FaceGateStatus.AUTHENTICATING,
                        statusMessage = "Complete Face Recognition on your device",
                        errorMessage = null
                    )
                )
            }

            faceGateManager.authenticate(
                activity = activity,
                title = "Verify Your Identity",
                subtitle = "Authenticate using your device biometrics",
                negativeButtonText = getString(R.string.action_cancel),
                onResult = { faceResult ->
                    when (faceResult) {
                        is FaceGateResult.Success -> {
                            appendActivity(
                                "Face Authentication",
                                "Biometric Authentication Successful (BIOMETRIC_WEAK)",
                                true
                            )
                            _uiState.update { current ->
                                current.copy(
                                    faceGate = current.faceGate.copy(
                                        status = FaceGateStatus.PASSED,
                                        statusMessage = "Biometric Authentication Successful — Authorize Cryptographic Signing",
                                        errorMessage = null
                                    )
                                )
                            }
                            executeCryptoSigningAndSubmit(activity, payload, onCompleted)
                        }
                        is FaceGateResult.AttemptFailed -> {
                            appendActivity(
                                "Face Authentication",
                                "Attempt did not match — retry required",
                                false
                            )
                            _uiState.update { current ->
                                current.copy(
                                    faceGate = current.faceGate.copy(
                                        status = FaceGateStatus.FAILED,
                                        statusMessage = null,
                                        errorMessage = "Face Authentication Failed — Please Retry"
                                    )
                                )
                            }
                        }
                        is FaceGateResult.Cancelled -> {
                            appendActivity(
                                "Face Authentication",
                                "Biometric prompt cancelled",
                                false
                            )
                            _uiState.update { current ->
                                current.copy(
                                    faceGate = current.faceGate.copy(
                                        status = FaceGateStatus.FAILED,
                                        statusMessage = null,
                                        errorMessage = "Face Authentication Failed — Please Retry (${faceResult.message})"
                                    )
                                )
                            }
                        }
                        is FaceGateResult.Lockout -> {
                            appendActivity(
                                "Face Authentication",
                                "Biometric lockout active",
                                false
                            )
                            _uiState.update { current ->
                                current.copy(
                                    faceGate = current.faceGate.copy(
                                        status = FaceGateStatus.LOCKED_OUT,
                                        statusMessage = null,
                                        errorMessage = faceResult.message
                                    )
                                )
                            }
                        }
                        is FaceGateResult.NotEnrolled -> {
                            _uiState.update { current ->
                                current.copy(
                                    faceGate = current.faceGate.copy(
                                        isWeakBiometricAvailable = false,
                                        isNotEnrolled = true,
                                        availabilityLabel = "Not Enrolled",
                                        status = FaceGateStatus.UNAVAILABLE,
                                        statusMessage = null,
                                        errorMessage = faceResult.message
                                    )
                                )
                            }
                        }
                        is FaceGateResult.Error -> {
                            _uiState.update { current ->
                                current.copy(
                                    faceGate = current.faceGate.copy(
                                        status = FaceGateStatus.FAILED,
                                        statusMessage = null,
                                        errorMessage = faceResult.message
                                    )
                                )
                            }
                        }
                    }
                }
            )
            return
        }

        if (faceGateState.fallbackAuthorized) {
            executeCryptoSigningAndSubmit(activity, payload, onCompleted)
            return
        }

        _uiState.update { current ->
            current.copy(
                faceGate = faceGateState.copy(
                    status = FaceGateStatus.UNAVAILABLE,
                    statusMessage = "Face / Weak Biometric unavailable. Confirm fallback below to proceed with existing M2 authentication."
                )
            )
        }
    }

    fun continueWithExistingAuthFallback(
        activity: FragmentActivity,
        onCompleted: (Boolean) -> Unit
    ) {
        val currentFaceGate = evaluateFaceGateState(preserveProgress = true)
        if (currentFaceGate.isWeakBiometricAvailable) {
            // Security guard: never allow fallback bypass when BIOMETRIC_WEAK gate is active
            approveAndExecuteAuth(activity, onCompleted)
            return
        }
        _uiState.update { current ->
            current.copy(
                faceGate = currentFaceGate.copy(
                    fallbackAuthorized = true,
                    statusMessage = "Proceeding with existing M2 Keystore CryptoObject authentication.",
                    errorMessage = null
                )
            )
        }
        approveAndExecuteAuth(activity, onCompleted)
    }

    private fun executeCryptoSigningAndSubmit(
        activity: FragmentActivity,
        payload: QrAuthPayload,
        onCompleted: (Boolean) -> Unit
    ) {
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

        Log.i(BiometricFaceGateManager.TAG, "KEYSTORE_SIGNING_STARTED sessionType=${payload.type.name}")
        authenticator.authenticateAndSign(
            activity = activity,
            challenge = challengeBytes,
            promptTitle = promptTitle,
            promptSubtitle = promptSubtitle,
            onResult = { result ->
                when (val outcome = SigningResultPolicy.classify(result)) {
                    is SigningOutcome.Verified -> {
                        val success = outcome.result
                        Log.i(BiometricFaceGateManager.TAG, "KEYSTORE_SIGNING_SUCCEEDED authMethod=${success.authMethodLabel}")
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
                                                Log.i(BiometricFaceGateManager.TAG, "BACKEND_VERIFICATION_SUCCEEDED flow=AUTHENTICATION")
                                                appendActivity(
                                                    "Sign-In Approved",
                                                    "ECDSA P-256 verified by backend (${success.authMethodLabel})",
                                                    true
                                                )
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
                                                Log.i(BiometricFaceGateManager.TAG, "BACKEND_VERIFICATION_SUCCEEDED flow=ENROLLMENT")
                                                appendActivity(
                                                    "Device Enrolled",
                                                    "Hardware public key registered (${success.authMethodLabel})",
                                                    true
                                                )
                                                registrationManager.setRegistrationStatus(DeviceRegistrationStatus.ACTIVE)
                                                registrationManager.setRegisteredFingerprint(exportedKey.sha256Fingerprint)
                                                _uiState.update { current ->
                                                    current.copy(
                                                        isRegistered = true,
                                                        registrationStatus = DeviceRegistrationStatus.ACTIVE.name,
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
                                                if (apiResult.code == 409 || apiResult.message.contains("DEVICE_ALREADY_REGISTERED", ignoreCase = true)) {
                                                    registrationManager.setRegistrationStatus(DeviceRegistrationStatus.ACTIVE)
                                                    _uiState.update { current ->
                                                        current.copy(
                                                            isRegistered = true,
                                                            registrationStatus = DeviceRegistrationStatus.ACTIVE.name,
                                                            trustedPhoneCount = 1,
                                                            activeSession = current.activeSession.copy(
                                                                step = AuthFlowStep.FAILED,
                                                                errorMessage = "Perangkat ini sudah terdaftar di IPGuard. Silakan gunakan Sign In untuk melanjutkan."
                                                            )
                                                        )
                                                    }
                                                } else {
                                                    _uiState.update { current ->
                                                        current.copy(
                                                            activeSession = current.activeSession.copy(
                                                                step = AuthFlowStep.FAILED,
                                                                errorMessage = "Registration rejected: ${apiResult.message}"
                                                            )
                                                        )
                                                    }
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
        val resetFaceGate = evaluateFaceGateState(preserveProgress = false)
        _uiState.update { current ->
            current.copy(
                faceGate = resetFaceGate,
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

    private fun appendActivity(title: String, detail: String, isPositive: Boolean) {
        val entry = SecurityActivityEntry(
            timestampLabel = currentTimeLabel(),
            title = title,
            detail = detail,
            isPositive = isPositive
        )
        _uiState.update { current ->
            current.copy(activityLog = (listOf(entry) + current.activityLog).take(6))
        }
    }

    private fun currentTimeLabel(): String {
        return SimpleDateFormat("HH:mm:ss", Locale.US).format(Date())
    }

    private fun deviceModel(): String {
        val manufacturer = Build.MANUFACTURER
            .replaceFirstChar { if (it.isLowerCase()) it.titlecase() else it.toString() }
        return "$manufacturer ${Build.MODEL}"
    }
}
