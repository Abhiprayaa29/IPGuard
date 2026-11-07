package com.ipguard.authenticator.ui.screens.settings

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
fun SecuritySettingsScreen(
    uiState: AuthenticatorUiState,
    onBack: () -> Unit,
    onDeviceInformation: () -> Unit,
    onHome: () -> Unit,
    modifier: Modifier = Modifier
) {
    val authPolicy = uiState.authPolicy
    val keyState = uiState.keyDiagnostic

    AuthenticatorScreen(
        eyebrow = stringResource(R.string.settings_eyebrow),
        title = stringResource(R.string.settings_title),
        subtitle = stringResource(R.string.settings_subtitle),
        modifier = modifier,
        onBack = onBack
    ) {
        InformationCard {
            SectionTitle(text = stringResource(R.string.settings_policy_title))
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = stringResource(R.string.settings_primary_auth_label),
                value = authPolicy.primaryAuthMethod,
                valueColor = IPGuardTeal
            )
            KeyValueRow(
                label = stringResource(R.string.settings_biometric_route_label),
                value = authPolicy.biometricStatus,
                valueColor = IPGuardGold
            )
            KeyValueRow(
                label = stringResource(R.string.settings_credential_route_label),
                value = authPolicy.credentialStatus,
                valueColor = IPGuardTeal
            )
            KeyValueRow(
                label = stringResource(R.string.settings_face_gate_label),
                value = stringResource(R.string.settings_face_gate_value),
                showDivider = false
            )
        }

        Spacer(Modifier.height(14.dp))
        InformationCard {
            SectionTitle(text = stringResource(R.string.settings_authorization_title))
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = stringResource(R.string.settings_method_label),
                value = authPolicy.primaryAuthMethod,
                valueColor = IPGuardTeal
            )
            KeyValueRow(
                label = stringResource(R.string.settings_key_label),
                value = if (keyState.hasKey) {
                    stringResource(R.string.settings_key_available_value)
                } else {
                    stringResource(R.string.settings_key_value)
                },
                valueColor = IPGuardTeal
            )
            KeyValueRow(
                label = stringResource(R.string.settings_invalidation_label),
                value = if (keyState.hasKey) {
                    stringResource(R.string.settings_invalidation_enabled_value)
                } else {
                    stringResource(R.string.settings_invalidation_value)
                },
                showDivider = false
            )
        }

        Spacer(Modifier.height(14.dp))
        InformationCard {
            SectionTitle(text = stringResource(R.string.settings_recovery_title))
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = stringResource(R.string.settings_codes_label),
                value = stringResource(R.string.settings_codes_value)
            )
            KeyValueRow(
                label = stringResource(R.string.settings_replacement_label),
                value = stringResource(R.string.settings_replacement_value)
            )
            KeyValueRow(
                label = stringResource(R.string.settings_revoke_label),
                value = stringResource(R.string.settings_revoke_value),
                showDivider = false
            )
        }

        Spacer(Modifier.height(14.dp))
        InformationCard {
            SectionTitle(text = stringResource(R.string.settings_privacy_title))
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = stringResource(R.string.settings_frames_label),
                value = stringResource(R.string.settings_frames_value)
            )
            KeyValueRow(
                label = stringResource(R.string.settings_qr_label),
                value = stringResource(R.string.settings_qr_value)
            )
            KeyValueRow(
                label = stringResource(R.string.settings_logs_label),
                value = stringResource(R.string.settings_logs_value),
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
            primaryLabel = stringResource(R.string.settings_primary_action),
            onPrimary = onDeviceInformation,
            secondaryLabel = stringResource(R.string.settings_secondary_action),
            onSecondary = onHome
        )
    }
}
