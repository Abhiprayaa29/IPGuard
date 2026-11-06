package com.ipguard.authenticator.ui.screens.deviceinfo

import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
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

@Composable
fun DeviceInformationScreen(
    uiState: AuthenticatorUiState,
    onBack: () -> Unit,
    onOpenSecuritySettings: () -> Unit,
    onHome: () -> Unit,
    modifier: Modifier = Modifier,
    onGenerateKey: () -> Unit = {},
    onDeleteKey: () -> Unit = {},
    onRefreshKey: () -> Unit = {},
    onTestSign: () -> Unit = {}
) {
    val keyState = uiState.keyDiagnostic
    val authPolicy = uiState.authPolicy
    val signingDiag = uiState.signingDiagnostic

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
            SectionTitle(text = "AUTHENTICATION POLICY (M2.3-B)")
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = "Primary authorization",
                value = authPolicy.primaryAuthMethod,
                valueColor = IPGuardTeal
            )
            KeyValueRow(
                label = "Biometric route",
                value = authPolicy.biometricStatus,
                valueColor = IPGuardGold
            )
            KeyValueRow(
                label = "Device lock status",
                value = authPolicy.credentialStatus,
                valueColor = IPGuardTeal
            )
            KeyValueRow(
                label = "Fingerprint required?",
                value = "No (Optional fallback active)",
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
                value = if (keyState.hasKey) "Available (ECDSA P-256)" else stringResource(R.string.device_key_value),
                valueColor = if (keyState.hasKey) IPGuardTeal else IPGuardGold
            )
            KeyValueRow(
                label = stringResource(R.string.device_hardware_label),
                value = if (keyState.hasKey) keyState.securityLevel else stringResource(R.string.device_hardware_value),
                valueColor = if (keyState.hasKey) IPGuardTeal else IPGuardGold
            )
            if (keyState.hasKey) {
                KeyValueRow(
                    label = "Key curve",
                    value = keyState.curve.ifEmpty { "secp256r1" }
                )
                KeyValueRow(
                    label = "Private key",
                    value = "Non-exportable (Keystore)",
                    valueColor = IPGuardTeal
                )
                KeyValueRow(
                    label = "User authentication",
                    value = keyState.userAuthentication
                )
                if (keyState.fingerprint.isNotEmpty()) {
                    KeyValueRow(
                        label = "Public key SHA-256",
                        value = keyState.fingerprint
                    )
                }
            }
            KeyValueRow(
                label = stringResource(R.string.device_attestation_label),
                value = if (keyState.hasKey) "Local platform KeyInfo" else stringResource(R.string.device_attestation_value)
            )
            KeyValueRow(
                label = stringResource(R.string.device_face_label),
                value = stringResource(R.string.device_face_value)
            )
            KeyValueRow(
                label = stringResource(R.string.device_app_auth_label),
                value = "BiometricPrompt (PIN / Biometric)",
                valueColor = IPGuardTeal,
                showDivider = false
            )
        }

        Spacer(Modifier.height(14.dp))
        InformationCard {
            SectionTitle(text = "LIVE SIGNING TEST (AUTH-04 / 05 / 10)")
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
                    label = "Auth method used",
                    value = signingDiag.authMethodLabel,
                    valueColor = IPGuardTeal
                )
                KeyValueRow(
                    label = "Locally verified",
                    value = if (signingDiag.verifiedLocally) "Yes (Valid ECDSA Signature)" else "Failed verification",
                    valueColor = if (signingDiag.verifiedLocally) IPGuardTeal else IPGuardGold
                )
                KeyValueRow(
                    label = "Signature (Base64)",
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
                primaryLabel = "Test PIN/Biometric Sign",
                onPrimary = onTestSign
            )
        }

        Spacer(Modifier.height(14.dp))
        InformationCard {
            SectionTitle(text = "Keystore Key Operations")
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
                primaryLabel = if (keyState.hasKey) "Regenerate Signing Key" else "Generate Signing Key",
                onPrimary = onGenerateKey,
                secondaryLabel = if (keyState.hasKey) "Delete Signing Key" else null,
                onSecondary = if (keyState.hasKey) onDeleteKey else null,
                tertiaryLabel = "Refresh All",
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
}
