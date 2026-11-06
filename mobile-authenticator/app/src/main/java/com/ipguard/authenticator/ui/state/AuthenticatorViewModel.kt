package com.ipguard.authenticator.ui.state

import android.app.Application
import android.os.Build
import androidx.fragment.app.FragmentActivity
import androidx.lifecycle.AndroidViewModel
import com.ipguard.authenticator.BuildConfig
import com.ipguard.authenticator.security.AndroidKeystoreDeviceKeyManager
import com.ipguard.authenticator.security.DeviceAuthenticationPolicy
import com.ipguard.authenticator.security.DeviceKeyManager
import com.ipguard.authenticator.security.DeviceKeyVerificationRunner
import com.ipguard.authenticator.security.DeviceSigningAuthenticator
import com.ipguard.authenticator.security.FullVerificationSuiteResult
import com.ipguard.authenticator.security.SigningResult
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
                        primaryAuthMethod = policy.primaryAuthMethod.label,
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
                        policyExplanation = "Policy evaluation error: ${e.message}"
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
                                "Required (Strong Biometric or Device PIN)"
                            } else {
                                "None (Direct Access)"
                            },
                            isNonExportable = metadata.isNonExportable,
                            fingerprint = exported.sha256Fingerprint,
                            statusMessage = "Keystore key is active and ready",
                            errorMessage = null
                        )
                    )
                }
            } else {
                _uiState.update { current ->
                    current.copy(
                        keyDiagnostic = KeyDiagnosticState(
                            hasKey = false,
                            statusMessage = "No key generated yet",
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
                signingDiagnostic = current.signingDiagnostic.copy(
                    statusMessage = "Awaiting user authentication...",
                    errorMessage = null
                )
            )
        }

        authenticator.authenticateAndSign(
            activity = activity,
            challenge = challenge,
            promptTitle = "Approve IPGuard Sign-In",
            promptSubtitle = "Authenticate with your device PIN or biometric",
            onResult = { result ->
                when (result) {
                    is SigningResult.Success -> {
                        _uiState.update { current ->
                            current.copy(
                                signingDiagnostic = SigningDiagnosticState(
                                    hasSigned = true,
                                    challenge = challenge.decodeToString(),
                                    base64Signature = result.base64Signature,
                                    authMethodLabel = result.authMethodLabel,
                                    verifiedLocally = result.verifiedLocally,
                                    statusMessage = "Signed & verified successfully with ${result.authMethodLabel}",
                                    errorMessage = null
                                )
                            )
                        }
                        onSuccess(result)
                    }
                    is SigningResult.Failed -> {
                        _uiState.update { current ->
                            current.copy(
                                signingDiagnostic = current.signingDiagnostic.copy(
                                    errorMessage = "Authentication failed. Incorrect credential."
                                )
                            )
                        }
                    }
                    is SigningResult.Error -> {
                        _uiState.update { current ->
                            current.copy(
                                signingDiagnostic = current.signingDiagnostic.copy(
                                    errorMessage = "Authentication canceled or error: ${result.errorMessage} (code ${result.errorCode})"
                                )
                            )
                        }
                    }
                }
            }
        )
    }

    fun runVerificationSuite(requireUserAuth: Boolean = true): FullVerificationSuiteResult {
        val result = DeviceKeyVerificationRunner.runAll(keyManager, requireUserAuth)
        refreshAll()
        return result
    }

    private fun deviceModel(): String {
        val manufacturer = Build.MANUFACTURER
            .replaceFirstChar { if (it.isLowerCase()) it.titlecase() else it.toString() }
        return "$manufacturer ${Build.MODEL}"
    }
}
