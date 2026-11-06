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
import com.ipguard.authenticator.ui.theme.IPGuardGold
import com.ipguard.authenticator.ui.theme.IPGuardTeal

@Composable
fun SecuritySettingsScreen(
    onBack: () -> Unit,
    onDeviceInformation: () -> Unit,
    onHome: () -> Unit,
    modifier: Modifier = Modifier
) {
    AuthenticatorScreen(
        eyebrow = stringResource(R.string.settings_eyebrow),
        title = stringResource(R.string.settings_title),
        subtitle = stringResource(R.string.settings_subtitle),
        modifier = modifier,
        onBack = onBack
    ) {
        InformationCard {
            SectionTitle(text = "AUTHENTICATION TIERS (M2.3-B)")
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = "Tier 1: Strong Biometric",
                value = "Optional (Class 3 Hardware)",
                valueColor = IPGuardTeal
            )
            KeyValueRow(
                label = "Tier 2: Device Credential",
                value = "Primary (PIN / Pattern / Password)",
                valueColor = IPGuardTeal
            )
            KeyValueRow(
                label = "Tier 3: Weak Biometric",
                value = "Disallowed for Signing Keys",
                valueColor = IPGuardGold
            )
            KeyValueRow(
                label = "Tier 4: ML Kit Face Gate",
                value = "UX Presence Only (No Auth)",
                showDivider = false
            )
        }

        Spacer(Modifier.height(14.dp))
        InformationCard {
            SectionTitle(text = stringResource(R.string.settings_authorization_title))
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = stringResource(R.string.settings_method_label),
                value = "Strong Biometric OR Device PIN",
                valueColor = IPGuardTeal
            )
            KeyValueRow(
                label = stringResource(R.string.settings_key_label),
                value = "ECDSA P-256 (TEE-backed)",
                valueColor = IPGuardTeal
            )
            KeyValueRow(
                label = stringResource(R.string.settings_invalidation_label),
                value = "Enabled for biometric changes",
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
            text = "Fingerprint is NOT mandatory. The app uses your device lock screen PIN/pattern as the primary cryptographic authorizer.",
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
