package com.ipguard.authenticator.ui.state

import android.app.Application
import android.os.Build
import androidx.fragment.app.FragmentActivity
import androidx.lifecycle.AndroidViewModel
import com.ipguard.authenticator.BuildConfig
import com.ipguard.authenticator.R
import com.ipguard.authenticator.security.AndroidKeystoreDeviceKeyManager
import com.ipguard.authenticator.security.DeviceAuthenticationPolicy
import com.ipguard.authenticator.security.DeviceKeyManager
import com.ipguard.authenticator.security.DeviceKeyVerificationRunner
import com.ipguard.authenticator.security.DeviceSigningAuthenticator
import com.ipguard.authenticator.security.FullVerificationSuiteResult
import com.ipguard.authenticator.security.SigningKeyPolicyViolationException
import com.ipguard.authenticator.security.SigningOutcome
import com.ipguard.authenticator.security.SigningResult
import com.ipguard.authenticator.security.SigningResultPolicy
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update

class AuthenticatorViewModel @JvmOverloads constructor(
    application: Application,
    private val keyManager: DeviceKeyManager = AndroidKeystoreDeviceKeyManager(),
    private val authenticator: DeviceSigningAuthenticator = DeviceSigningAuthenticator(keyManager)
) : AndroidViewModel(application) {

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
