package com.ipguard.authenticator.ui.screens.settings

import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.ipguard.authenticator.R
import com.ipguard.authenticator.ui.components.AppPill
import com.ipguard.authenticator.ui.components.AuthenticatorScreen
import com.ipguard.authenticator.ui.components.InformationCard
import com.ipguard.authenticator.ui.components.KeyValueRow
import com.ipguard.authenticator.ui.components.NoticeCard
import com.ipguard.authenticator.ui.components.NoticeTone
import com.ipguard.authenticator.ui.components.PillTone
import com.ipguard.authenticator.ui.components.ScreenActions
import com.ipguard.authenticator.ui.components.SectionTitle
import com.ipguard.authenticator.ui.state.AuthenticatorUiState
import com.ipguard.authenticator.ui.theme.IPGuardGoldBright
import com.ipguard.authenticator.ui.theme.IPGuardVerified

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
        eyebrow = "SECURITY & ABOUT",
        title = "Security & about IPGuard",
        subtitle = "Review hardware authorization policies, native biometric integration, privacy guarantees, and build metadata.",
        modifier = modifier,
        onBack = onBack
    ) {
        AppPill(
            text = "HARDENED KEYSTORE ARCHITECTURE",
            tone = PillTone.GOLD
        )
        Spacer(Modifier.height(16.dp))

        InformationCard {
            SectionTitle(text = stringResource(R.string.settings_policy_title))
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = stringResource(R.string.settings_primary_auth_label),
                value = authPolicy.primaryAuthMethod,
                valueColor = IPGuardGoldBright
            )
            KeyValueRow(
                label = "Native Face Gate",
                value = "AndroidX BiometricPrompt (BIOMETRIC_WEAK)",
                valueColor = IPGuardVerified
            )
            KeyValueRow(
                label = "Face Gate status",
                value = uiState.faceGate.availabilityLabel,
                valueColor = if (uiState.faceGate.isWeakBiometricAvailable) IPGuardVerified else IPGuardGoldBright
            )
            KeyValueRow(
                label = stringResource(R.string.settings_biometric_route_label),
                value = authPolicy.biometricStatus
            )
            KeyValueRow(
                label = stringResource(R.string.settings_credential_route_label),
                value = authPolicy.credentialStatus,
                valueColor = IPGuardVerified,
                showDivider = false
            )
        }

        Spacer(Modifier.height(14.dp))
        InformationCard {
            SectionTitle(text = stringResource(R.string.settings_authorization_title))
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = "Signing algorithm",
                value = "ECDSA P-256 (secp256r1)",
                monospaceValue = true
            )
            KeyValueRow(
                label = stringResource(R.string.settings_key_label),
                value = if (keyState.hasKey) "Created (Non-Exportable)" else "Not created",
                valueColor = if (keyState.hasKey) IPGuardVerified else IPGuardGoldBright
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
            SectionTitle(text = stringResource(R.string.settings_privacy_title))
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = "Camera & face frames stored",
                value = "Never",
                valueColor = IPGuardVerified
            )
            KeyValueRow(
                label = stringResource(R.string.settings_qr_label),
                value = "Never",
                valueColor = IPGuardVerified
            )
            KeyValueRow(
                label = "Private keys or tokens shown/logged",
                value = "Never",
                valueColor = IPGuardVerified,
                showDivider = false
            )
        }

        Spacer(Modifier.height(14.dp))
        InformationCard {
            SectionTitle(text = "ABOUT IPGUARD")
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = "Application",
                value = "IPGuard Authenticator"
            )
            KeyValueRow(
                label = "Application ID",
                value = uiState.deviceFacts.applicationId,
                monospaceValue = true
            )
            KeyValueRow(
                label = "Version & Build",
                value = "v${uiState.deviceFacts.appVersion}",
                monospaceValue = true
            )
            KeyValueRow(
                label = "Device hardware",
                value = uiState.deviceFacts.model
            )
            KeyValueRow(
                label = "Operating system",
                value = "Android ${uiState.deviceFacts.androidVersion}",
                showDivider = false
            )
        }

        Spacer(Modifier.height(14.dp))
        NoticeCard(
            text = "Security notice: Android BiometricPrompt BIOMETRIC_WEAK enforces OS-level face/weak biometrics where enrolled, while cryptographic signing remains bound to Android Keystore CryptoObject (BIOMETRIC_STRONG or DEVICE_CREDENTIAL).",
            tone = NoticeTone.INFO
        )
        Spacer(Modifier.height(22.dp))
        ScreenActions(
            primaryLabel = "Device & Key Lifecycle",
            onPrimary = onDeviceInformation,
            secondaryLabel = "Back to Dashboard",
            onSecondary = onHome
        )
    }
}
