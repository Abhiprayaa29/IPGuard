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
import com.ipguard.authenticator.ui.state.BackendConnectionStatus
import com.ipguard.authenticator.ui.theme.IPGuardDanger
import com.ipguard.authenticator.ui.theme.IPGuardGoldBright
import com.ipguard.authenticator.ui.theme.IPGuardPlatinum
import com.ipguard.authenticator.ui.theme.IPGuardSurface
import com.ipguard.authenticator.ui.theme.IPGuardVerified

private enum class PendingDeviceAction {
    REGENERATE_KEY,
    DELETE_KEY,
    REVOKE_ACCESS,
    UNREGISTER_DEVICE
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
    onSyncBackend: () -> Unit = {},
    onTestSign: () -> Unit = {}
) {
    val keyState = uiState.keyDiagnostic
    val authPolicy = uiState.authPolicy
    val signingDiag = uiState.signingDiagnostic
    val fallbackCurve = stringResource(R.string.device_fallback_curve)
    var pendingAction by remember { mutableStateOf<PendingDeviceAction?>(null) }

    val isActive = uiState.isRegistered && uiState.registrationStatus == "ACTIVE"
    val isRevoked = uiState.registrationStatus == "REVOKED"
    val maskedDeviceId = if (uiState.deviceId.length > 14) {
        "${uiState.deviceId.take(10)}...${uiState.deviceId.takeLast(4)}"
    } else {
        uiState.deviceId.ifBlank { "Pending" }
    }

    AuthenticatorScreen(
        eyebrow = "DEVICE SECURITY",
        title = "Device & key lifecycle",
        subtitle = "Inspect your registered hardware identity, authorization policy, and server-synced enrollment status.",
        modifier = modifier,
        onBack = onBack
    ) {
        AppPill(
            text = when {
                isRevoked -> "STATUS: REVOKED"
                isActive -> "STATUS: ACTIVE AUTHENTICATOR"
                else -> "STATUS: UNREGISTERED"
            },
            tone = when {
                isRevoked -> PillTone.DANGER
                isActive -> PillTone.VERIFIED
                else -> PillTone.GOLD
            }
        )
        Spacer(Modifier.height(16.dp))

        InformationCard {
            SectionTitle(text = "REGISTERED DEVICE")
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = "Device status",
                value = uiState.registrationStatus,
                valueColor = when {
                    isRevoked -> IPGuardDanger
                    isActive -> IPGuardVerified
                    else -> IPGuardGoldBright
                },
                monospaceValue = true
            )
            KeyValueRow(
                label = stringResource(R.string.device_model_label),
                value = uiState.deviceFacts.model
            )
            KeyValueRow(
                label = "Device identifier",
                value = maskedDeviceId,
                monospaceValue = true
            )
            KeyValueRow(
                label = stringResource(R.string.device_android_label),
                value = uiState.deviceFacts.androidVersion
            )
            KeyValueRow(
                label = "Backend connection",
                value = uiState.connectionState.statusLabel,
                valueColor = when (uiState.connectionState.status) {
                    BackendConnectionStatus.CONNECTED -> IPGuardVerified
                    BackendConnectionStatus.CHECKING -> IPGuardGoldBright
                    BackendConnectionStatus.UNAVAILABLE -> IPGuardDanger
                },
                showDivider = false
            )
        }

        Spacer(Modifier.height(14.dp))
        InformationCard {
            SectionTitle(text = "AUTHENTICATION METHOD")
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = stringResource(R.string.device_primary_auth_label),
                value = authPolicy.primaryAuthMethod,
                valueColor = IPGuardGoldBright
            )
            KeyValueRow(
                label = "Face Gate (Pre-check)",
                value = uiState.faceGate.availabilityLabel,
                valueColor = if (uiState.faceGate.isWeakBiometricAvailable) IPGuardVerified else IPGuardGoldBright
            )
            KeyValueRow(
                label = stringResource(R.string.device_biometric_route_label),
                value = authPolicy.biometricStatus
            )
            KeyValueRow(
                label = stringResource(R.string.device_lock_status_label),
                value = authPolicy.credentialStatus,
                valueColor = IPGuardVerified,
                showDivider = false
            )
        }

        Spacer(Modifier.height(14.dp))
        InformationCard {
            SectionTitle(text = "ANDROID KEYSTORE ECDSA P-256")
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = stringResource(R.string.device_key_label),
                value = if (keyState.hasKey) "Created (ECDSA P-256)" else "Not created",
                valueColor = if (keyState.hasKey) IPGuardVerified else IPGuardGoldBright
            )
            KeyValueRow(
                label = stringResource(R.string.device_hardware_label),
                value = if (keyState.hasKey) keyState.securityLevel else "Not checked",
                valueColor = if (keyState.hasKey) IPGuardVerified else IPGuardGoldBright
            )
            if (keyState.hasKey) {
                KeyValueRow(
                    label = stringResource(R.string.device_key_curve_label),
                    value = keyState.curve.ifEmpty { fallbackCurve },
                    monospaceValue = true
                )
                KeyValueRow(
                    label = stringResource(R.string.device_private_key_label),
                    value = stringResource(R.string.device_private_key_value),
                    valueColor = IPGuardVerified
                )
                KeyValueRow(
                    label = stringResource(R.string.device_user_auth_label),
                    value = keyState.userAuthentication
                )
                if (keyState.fingerprint.isNotEmpty()) {
                    KeyValueRow(
                        label = stringResource(R.string.device_public_key_sha_label),
                        value = "${keyState.fingerprint.take(20)}...",
                        monospaceValue = true,
                        showDivider = false
                    )
                }
            }
        }

        Spacer(Modifier.height(14.dp))
        InformationCard {
            SectionTitle(text = "DEVICE LIFECYCLE & ACCESS CONTROL")
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = "Enrollment policy",
                value = "One-Time Device Binding (M2)"
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
            Spacer(Modifier.height(12.dp))
            if (isRevoked) {
                NoticeCard(
                    text = "Device access is REVOKED while occupying your account's 1/1 slot. Restore access in Web Console (Devices -> Restore Access with Account Recovery Key) and then tap Sync Status.",
                    tone = NoticeTone.WARNING
                )
                Spacer(Modifier.height(10.dp))
            }
            ScreenActions(
                primaryLabel = if (uiState.isSyncingBackend) "Syncing Backend Status..." else "Sync Status from Backend",
                onPrimary = onSyncBackend,
                primaryEnabled = !uiState.isSyncingBackend,
                primaryLoading = uiState.isSyncingBackend,
                secondaryLabel = "Revoke Access",
                onSecondary = { pendingAction = PendingDeviceAction.REVOKE_ACCESS },
                tertiaryLabel = "Unregister Device",
                onTertiary = { pendingAction = PendingDeviceAction.UNREGISTER_DEVICE }
            )
        }

        Spacer(Modifier.height(14.dp))
        InformationCard {
            SectionTitle(text = stringResource(R.string.device_signing_test_title))
            Spacer(Modifier.height(8.dp))
            if (signingDiag.statusMessage != null) {
                NoticeCard(text = signingDiag.statusMessage, tone = NoticeTone.SUCCESS)
                Spacer(Modifier.height(8.dp))
            }
            if (signingDiag.errorMessage != null) {
                NoticeCard(text = signingDiag.errorMessage, tone = NoticeTone.WARNING)
                Spacer(Modifier.height(8.dp))
            }
            if (signingDiag.hasSigned) {
                KeyValueRow(
                    label = stringResource(R.string.device_auth_method_used_label),
                    value = signingDiag.authMethodLabel,
                    valueColor = IPGuardVerified
                )
                KeyValueRow(
                    label = stringResource(R.string.device_locally_verified_label),
                    value = if (signingDiag.verifiedLocally) "Yes (ECDSA valid)" else "Failed",
                    valueColor = if (signingDiag.verifiedLocally) IPGuardVerified else IPGuardDanger,
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
                NoticeCard(text = keyState.statusMessage, tone = NoticeTone.INFO)
                Spacer(Modifier.height(10.dp))
            }
            if (keyState.errorMessage != null) {
                NoticeCard(text = keyState.errorMessage, tone = NoticeTone.WARNING)
                Spacer(Modifier.height(10.dp))
            }
            ScreenActions(
                primaryLabel = if (keyState.hasKey) stringResource(R.string.key_action_regenerate) else stringResource(R.string.key_action_generate),
                onPrimary = {
                    if (keyState.hasKey) {
                        pendingAction = PendingDeviceAction.REGENERATE_KEY
                    } else {
                        onGenerateKey()
                    }
                },
                primaryEnabled = !uiState.isRegistered,
                secondaryLabel = if (keyState.hasKey) stringResource(R.string.key_action_delete) else null,
                onSecondary = if (keyState.hasKey) {
                    { pendingAction = PendingDeviceAction.DELETE_KEY }
                } else null,
                secondaryEnabled = !uiState.isRegistered,
                tertiaryLabel = stringResource(R.string.key_action_refresh),
                onTertiary = onRefreshKey
            )
            if (uiState.isRegistered) {
                Spacer(Modifier.height(8.dp))
                NoticeCard(
                    text = "M2 policy locks local key rotation/deletion while enrolled. Use Web Console Unregister Device before re-enrolling.",
                    tone = NoticeTone.INFO
                )
            }
        }

        Spacer(Modifier.height(14.dp))
        NoticeCard(text = authPolicy.policyExplanation, tone = NoticeTone.INFO)
        Spacer(Modifier.height(22.dp))
        ScreenActions(
            primaryLabel = "Security, Biometrics & About",
            onPrimary = onOpenSecuritySettings,
            secondaryLabel = "Back to Dashboard",
            onSecondary = onHome
        )
    }

    pendingAction?.let { action ->
        val (title, message, confirmLabel, onConfirm) = when (action) {
            PendingDeviceAction.REGENERATE_KEY -> Quad(
                stringResource(R.string.key_regenerate_confirm_title),
                stringResource(R.string.key_regenerate_confirm_message),
                stringResource(R.string.key_regenerate_confirm_action),
                onRegenerateKey
            )
            PendingDeviceAction.DELETE_KEY -> Quad(
                stringResource(R.string.key_delete_confirm_title),
                stringResource(R.string.key_delete_confirm_message),
                stringResource(R.string.key_delete_confirm_action),
                onDeleteKey
            )
            PendingDeviceAction.REVOKE_ACCESS -> Quad(
                "Revoke Device Access",
                if (isActive) {
                    "Under IPGuard M2 authorization policy, revoking an active authenticator must be confirmed from an authenticated Web Console session (Device Management -> Revoke Device). After revoking on the web, sync here to apply immediately."
                } else {
                    "This device is currently in ${uiState.registrationStatus} state. Tap Sync Status to refresh server records."
                },
                "Sync Status Now",
                onSyncBackend
            )
            PendingDeviceAction.UNREGISTER_DEVICE -> Quad(
                "Unregister Device",
                if (uiState.isRegistered) {
                    "One-Time Enrollment locks this phone until explicitly unregistered through an authorized Web Console session (Device Management -> Unregister Device). This prevents unauthorized key replacement. After unregistering on Web Console, tap Sync Status Now."
                } else {
                    "This device is already UNREGISTERED and eligible for fresh enrollment."
                },
                "Sync Status Now",
                onSyncBackend
            )
        }

        AlertDialog(
            onDismissRequest = { pendingAction = null },
            containerColor = IPGuardSurface,
            titleContentColor = IPGuardPlatinum,
            textContentColor = IPGuardPlatinum,
            title = { Text(title) },
            text = { Text(message) },
            confirmButton = {
                TextButton(
                    onClick = {
                        pendingAction = null
                        onConfirm()
                    }
                ) {
                    Text(confirmLabel, color = IPGuardGoldBright)
                }
            },
            dismissButton = {
                TextButton(onClick = { pendingAction = null }) {
                    Text(stringResource(R.string.key_action_cancel), color = IPGuardPlatinum)
                }
            }
        )
    }
}

private data class Quad<A, B, C, D>(
    val first: A,
    val second: B,
    val third: C,
    val fourth: D
)
