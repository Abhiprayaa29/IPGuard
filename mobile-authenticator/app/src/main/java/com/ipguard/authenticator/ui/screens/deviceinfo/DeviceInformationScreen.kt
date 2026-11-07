package com.ipguard.authenticator.ui.screens.deviceinfo

import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.ipguard.authenticator.R
import com.ipguard.authenticator.ui.components.AuthenticatorScreen
import com.ipguard.authenticator.ui.components.InformationCard
import com.ipguard.authenticator.ui.components.KeyValueRow
import com.ipguard.authenticator.ui.components.NoticeCard
import com.ipguard.authenticator.ui.components.NoticeTone
import com.ipguard.authenticator.ui.components.ScreenActions
import com.ipguard.authenticator.ui.components.SectionTitle
import com.ipguard.authenticator.ui.state.AuthenticatorUiState
import com.ipguard.authenticator.ui.theme.IPGuardGold
import com.ipguard.authenticator.ui.theme.IPGuardTeal

private enum class PendingKeyAction {
    REGENERATE,
    DELETE
}

@Composable
fun DeviceInformationScreen(
    uiState: AuthenticatorUiState,
    onBack: () -> Unit,
    onOpenSecuritySettings: () -> Unit,
    onHome: () -> Unit,
    modifier: Modifier = Modifier,
    onGenerateKey: () -> Unit = {},
    onRegenerateKey: () -> Unit = {},
    onDeleteKey: () -> Unit = {},
    onRefreshKey: () -> Unit = {},
    onTestSign: () -> Unit = {}
) {
    val keyState = uiState.keyDiagnostic
    val authPolicy = uiState.authPolicy
    val signingDiag = uiState.signingDiagnostic
    val fallbackCurve = stringResource(R.string.device_fallback_curve)
    var pendingKeyAction by remember { mutableStateOf<PendingKeyAction?>(null) }

    AuthenticatorScreen(
        eyebrow = stringResource(R.string.device_eyebrow),
        title = stringResource(R.string.device_title),
        subtitle = stringResource(R.string.device_subtitle),
        modifier = modifier,
        onBack = onBack
    ) {
        InformationCard {
            SectionTitle(text = stringResource(R.string.device_identity_title))
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = stringResource(R.string.device_model_label),
                value = uiState.deviceFacts.model
            )
            KeyValueRow(
                label = stringResource(R.string.device_android_label),
                value = uiState.deviceFacts.androidVersion
            )
            KeyValueRow(
                label = stringResource(R.string.device_app_label),
                value = uiState.deviceFacts.appVersion
            )
            KeyValueRow(
                label = stringResource(R.string.device_account_label),
                value = stringResource(R.string.device_not_linked_value),
                showDivider = false
            )
        }

        Spacer(Modifier.height(14.dp))
        InformationCard {
            SectionTitle(text = stringResource(R.string.device_policy_title))
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = stringResource(R.string.device_primary_auth_label),
                value = authPolicy.primaryAuthMethod,
                valueColor = IPGuardTeal
            )
            KeyValueRow(
                label = stringResource(R.string.device_biometric_route_label),
                value = authPolicy.biometricStatus,
                valueColor = IPGuardGold
            )
            KeyValueRow(
                label = stringResource(R.string.device_lock_status_label),
                value = authPolicy.credentialStatus,
                valueColor = IPGuardTeal
            )
            KeyValueRow(
                label = stringResource(R.string.device_fingerprint_required_label),
                value = stringResource(R.string.device_fingerprint_required_value),
                valueColor = IPGuardTeal,
                showDivider = false
            )
        }

        Spacer(Modifier.height(14.dp))
        InformationCard {
            SectionTitle(text = stringResource(R.string.device_security_title))
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = stringResource(R.string.device_binding_label),
                value = stringResource(R.string.device_binding_value)
            )
            KeyValueRow(
                label = stringResource(R.string.device_key_label),
                value = if (keyState.hasKey) stringResource(R.string.device_key_available_value) else stringResource(R.string.device_key_value),
                valueColor = if (keyState.hasKey) IPGuardTeal else IPGuardGold
            )
            KeyValueRow(
                label = stringResource(R.string.device_hardware_label),
                value = if (keyState.hasKey) keyState.securityLevel else stringResource(R.string.device_hardware_value),
                valueColor = if (keyState.hasKey) IPGuardTeal else IPGuardGold
            )
            if (keyState.hasKey) {
                KeyValueRow(
                    label = stringResource(R.string.device_key_curve_label),
                    value = keyState.curve.ifEmpty { fallbackCurve }
                )
                KeyValueRow(
                    label = stringResource(R.string.device_private_key_label),
                    value = stringResource(R.string.device_private_key_value),
                    valueColor = IPGuardTeal
                )
                KeyValueRow(
                    label = stringResource(R.string.device_user_auth_label),
                    value = keyState.userAuthentication
                )
                if (keyState.fingerprint.isNotEmpty()) {
                    KeyValueRow(
                        label = stringResource(R.string.device_public_key_sha_label),
                        value = keyState.fingerprint
                    )
                }
            }
            KeyValueRow(
                label = stringResource(R.string.device_attestation_label),
                value = if (keyState.hasKey) {
                    stringResource(R.string.device_attestation_keyinfo_value)
                } else {
                    stringResource(R.string.device_attestation_value)
                }
            )
            KeyValueRow(
                label = stringResource(R.string.device_face_label),
                value = stringResource(R.string.device_face_value)
            )
            KeyValueRow(
                label = stringResource(R.string.device_app_auth_label),
                value = stringResource(R.string.device_app_auth_biometric_value),
                valueColor = IPGuardTeal,
                showDivider = false
            )
        }

        Spacer(Modifier.height(14.dp))
        InformationCard {
            SectionTitle(text = stringResource(R.string.device_signing_test_title))
            Spacer(Modifier.height(8.dp))
            if (signingDiag.statusMessage != null) {
                NoticeCard(
                    text = signingDiag.statusMessage,
                    tone = NoticeTone.INFO
                )
                Spacer(Modifier.height(8.dp))
            }
            if (signingDiag.errorMessage != null) {
                NoticeCard(
                    text = signingDiag.errorMessage,
                    tone = NoticeTone.WARNING
                )
                Spacer(Modifier.height(8.dp))
            }
            if (signingDiag.hasSigned) {
                KeyValueRow(
                    label = stringResource(R.string.device_auth_method_used_label),
                    value = signingDiag.authMethodLabel,
                    valueColor = IPGuardTeal
                )
                KeyValueRow(
                    label = stringResource(R.string.device_locally_verified_label),
                    value = if (signingDiag.verifiedLocally) {
                        stringResource(R.string.device_verified_value)
                    } else {
                        stringResource(R.string.device_failed_verification_value)
                    },
                    valueColor = if (signingDiag.verifiedLocally) IPGuardTeal else IPGuardGold
                )
                KeyValueRow(
                    label = stringResource(R.string.device_signature_label),
                    value = if (signingDiag.base64Signature.length > 24) {
                        "${signingDiag.base64Signature.take(12)}...${signingDiag.base64Signature.takeLast(12)}"
                    } else {
                        signingDiag.base64Signature
                    },
                    showDivider = false
                )
                Spacer(Modifier.height(8.dp))
            }
            ScreenActions(
                primaryLabel = stringResource(R.string.device_test_primary_action),
                onPrimary = onTestSign
            )
        }

        Spacer(Modifier.height(14.dp))
        InformationCard {
            SectionTitle(text = stringResource(R.string.device_key_operations_title))
            Spacer(Modifier.height(8.dp))
            if (keyState.statusMessage != null) {
                NoticeCard(
                    text = keyState.statusMessage,
                    tone = NoticeTone.INFO
                )
                Spacer(Modifier.height(10.dp))
            }
            if (keyState.errorMessage != null) {
                NoticeCard(
                    text = keyState.errorMessage,
                    tone = NoticeTone.WARNING
                )
                Spacer(Modifier.height(10.dp))
            }
            ScreenActions(
                primaryLabel = if (keyState.hasKey) {
                    stringResource(R.string.key_action_regenerate)
                } else {
                    stringResource(R.string.key_action_generate)
                },
                onPrimary = if (keyState.hasKey) {
                    { pendingKeyAction = PendingKeyAction.REGENERATE }
                } else {
                    onGenerateKey
                },
                secondaryLabel = if (keyState.hasKey) {
                    stringResource(R.string.key_action_delete)
                } else {
                    null
                },
                onSecondary = if (keyState.hasKey) {
                    { pendingKeyAction = PendingKeyAction.DELETE }
                } else {
                    null
                },
                tertiaryLabel = stringResource(R.string.key_action_refresh),
                onTertiary = onRefreshKey
            )
        }

        Spacer(Modifier.height(14.dp))
        InformationCard {
            SectionTitle(text = stringResource(R.string.device_connection_title))
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = stringResource(R.string.device_api_label),
                value = stringResource(R.string.device_api_value)
            )
            KeyValueRow(
                label = stringResource(R.string.device_enrollment_label),
                value = stringResource(R.string.device_enrollment_value)
            )
            KeyValueRow(
                label = stringResource(R.string.device_trusted_label),
                value = stringResource(
                    R.string.device_trusted_value,
                    uiState.trustedPhoneCount,
                    uiState.maximumTrustedPhones
                ),
                showDivider = false
            )
        }

        Spacer(Modifier.height(14.dp))
        NoticeCard(
            text = authPolicy.policyExplanation,
            tone = NoticeTone.INFO
        )
        Spacer(Modifier.height(24.dp))
        ScreenActions(
            primaryLabel = stringResource(R.string.device_primary_action),
            onPrimary = onOpenSecuritySettings,
            secondaryLabel = stringResource(R.string.device_secondary_action),
            onSecondary = onHome
        )
    }

    pendingKeyAction?.let { action ->
        val title = when (action) {
            PendingKeyAction.REGENERATE -> stringResource(R.string.key_regenerate_confirm_title)
            PendingKeyAction.DELETE -> stringResource(R.string.key_delete_confirm_title)
        }
        val message = when (action) {
            PendingKeyAction.REGENERATE -> stringResource(R.string.key_regenerate_confirm_message)
            PendingKeyAction.DELETE -> stringResource(R.string.key_delete_confirm_message)
        }
        val confirmLabel = when (action) {
            PendingKeyAction.REGENERATE -> stringResource(R.string.key_regenerate_confirm_action)
            PendingKeyAction.DELETE -> stringResource(R.string.key_delete_confirm_action)
        }

        AlertDialog(
            onDismissRequest = { pendingKeyAction = null },
            title = { Text(title) },
            text = { Text(message) },
            confirmButton = {
                TextButton(
                    onClick = {
                        pendingKeyAction = null
                        when (action) {
                            PendingKeyAction.REGENERATE -> onRegenerateKey()
                            PendingKeyAction.DELETE -> onDeleteKey()
                        }
                    }
                ) {
                    Text(confirmLabel)
                }
            },
            dismissButton = {
                TextButton(onClick = { pendingKeyAction = null }) {
                    Text(stringResource(R.string.key_action_cancel))
                }
            }
        )
    }
}
