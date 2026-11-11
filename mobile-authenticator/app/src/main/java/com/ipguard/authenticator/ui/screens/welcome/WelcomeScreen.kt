package com.ipguard.authenticator.ui.screens.welcome

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.ipguard.authenticator.R
import com.ipguard.authenticator.ui.components.AppPill
import com.ipguard.authenticator.ui.components.AuthenticatorScreen
import com.ipguard.authenticator.ui.components.CardDivider
import com.ipguard.authenticator.ui.components.ConnectionBadge
import com.ipguard.authenticator.ui.components.DashboardActionTile
import com.ipguard.authenticator.ui.components.InformationCard
import com.ipguard.authenticator.ui.components.InlineLink
import com.ipguard.authenticator.ui.components.KeyValueRow
import com.ipguard.authenticator.ui.components.NoticeCard
import com.ipguard.authenticator.ui.components.NoticeTone
import com.ipguard.authenticator.ui.components.PillTone
import com.ipguard.authenticator.ui.components.ScreenActions
import com.ipguard.authenticator.ui.components.SectionTitle
import com.ipguard.authenticator.ui.state.AuthenticatorUiState
import com.ipguard.authenticator.ui.state.BackendConnectionStatus
import com.ipguard.authenticator.ui.theme.IPGuardDanger
import com.ipguard.authenticator.ui.theme.IPGuardGold
import com.ipguard.authenticator.ui.theme.IPGuardGoldBright
import com.ipguard.authenticator.ui.theme.IPGuardHairline
import com.ipguard.authenticator.ui.theme.IPGuardPlatinum
import com.ipguard.authenticator.ui.theme.IPGuardSlate
import com.ipguard.authenticator.ui.theme.IPGuardSurfaceElevated
import com.ipguard.authenticator.ui.theme.IPGuardVerified

@Composable
fun WelcomeScreen(
    uiState: AuthenticatorUiState,
    onStartSetup: () -> Unit,
    onStartSignIn: () -> Unit = {},
    onReviewRequest: () -> Unit,
    onOpenAssetVault: () -> Unit = {},
    onOpenDeviceInformation: () -> Unit,
    onOpenSecuritySettings: () -> Unit,
    onRefreshSync: () -> Unit = {},
    modifier: Modifier = Modifier
) {
    val isRegistered = uiState.isRegistered
    val isRevoked = uiState.registrationStatus == "REVOKED"
    val hasKey = uiState.keyDiagnostic.hasKey
    val isOnline = uiState.connectionState.status == BackendConnectionStatus.CONNECTED

    val statusPillText = when {
        isRevoked -> "DEVICE REVOKED"
        isRegistered && hasKey -> "ACTIVE AUTHENTICATOR"
        isRegistered && !hasKey -> "KEY MISSING IN KEYSTORE"
        else -> "UNREGISTERED"
    }
    val statusPillTone = when {
        isRevoked || (isRegistered && !hasKey) -> PillTone.DANGER
        isRegistered -> PillTone.VERIFIED
        else -> PillTone.GOLD
    }

    val eyebrow = when {
        isRevoked -> "ACCESS REVOKED"
        isRegistered -> "PRIMARY AUTHENTICATOR"
        else -> "DEVICE ENROLLMENT"
    }
    val title = when {
        isRevoked -> "Device access revoked"
        isRegistered -> "IPGuard Authenticator"
        else -> "Enroll this device"
    }
    val subtitle = when {
        isRevoked -> "This device slot is suspended. Restore access in Web Console (Devices -> Restore Access) with your recovery key, or unregister it."
        isRegistered -> "Hardware Keystore ECDSA P-256 and native Android biometrics ready for QR verification."
        else -> "Bind this Android phone as your single trusted authenticator for Web Console access."
    }

    AuthenticatorScreen(
        eyebrow = eyebrow,
        title = title,
        subtitle = subtitle,
        headerTrailing = { ConnectionBadge(connectionState = uiState.connectionState) },
        modifier = modifier
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            AppPill(text = statusPillText, tone = statusPillTone)
            Surface(
                onClick = onRefreshSync,
                shape = RoundedCornerShape(100),
                color = IPGuardSurfaceElevated,
                border = BorderStroke(1.dp, IPGuardHairline)
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = Icons.Filled.Refresh,
                        contentDescription = "Sync backend status",
                        tint = IPGuardGoldBright,
                        modifier = Modifier.size(14.dp)
                    )
                    Spacer(Modifier.width(5.dp))
                    Text(
                        text = if (uiState.isSyncingBackend) "SYNCING" else "SYNC",
                        style = MaterialTheme.typography.labelSmall,
                        color = IPGuardGoldBright,
                        fontSize = 9.sp
                    )
                }
            }
        }

        Spacer(Modifier.height(18.dp))

        InformationCard(
            borderColor = if (isRegistered && hasKey && !isRevoked) {
                IPGuardGold.copy(alpha = 0.35f)
            } else {
                IPGuardHairline
            }
        ) {
            SectionTitle(text = "DEVICE TRUST POSTURE")
            Spacer(Modifier.height(12.dp))
            Text(
                text = uiState.deviceFacts.model,
                style = MaterialTheme.typography.titleLarge,
                color = IPGuardPlatinum
            )
            Text(
                text = "Android ${uiState.deviceFacts.androidVersion}",
                style = MaterialTheme.typography.bodySmall,
                color = IPGuardSlate
            )
            Spacer(Modifier.height(14.dp))
            CardDivider()
            KeyValueRow(
                label = "Registration status",
                value = uiState.registrationStatus,
                valueColor = when {
                    isRevoked -> IPGuardDanger
                    isRegistered -> IPGuardVerified
                    else -> IPGuardGoldBright
                },
                monospaceValue = true
            )
            KeyValueRow(
                label = "Keystore signing key",
                value = if (hasKey) "ECDSA P-256 (${uiState.keyDiagnostic.securityLevel})" else "Not created",
                valueColor = if (hasKey) IPGuardVerified else IPGuardGoldBright
            )
            KeyValueRow(
                label = "Native Face Gate",
                value = uiState.faceGate.availabilityLabel,
                valueColor = if (uiState.faceGate.isWeakBiometricAvailable) IPGuardVerified else IPGuardGoldBright
            )
            KeyValueRow(
                label = "Backend API",
                value = uiState.connectionState.statusLabel,
                valueColor = when (uiState.connectionState.status) {
                    BackendConnectionStatus.CONNECTED -> IPGuardVerified
                    BackendConnectionStatus.CHECKING -> IPGuardGoldBright
                    BackendConnectionStatus.UNAVAILABLE -> IPGuardDanger
                },
                showDivider = false
            )
        }

        Spacer(Modifier.height(12.dp))
        if (uiState.connectionState.status == BackendConnectionStatus.UNAVAILABLE &&
            uiState.connectionState.detailMessage != null
        ) {
            NoticeCard(
                text = "Backend unavailable (${uiState.connectionState.apiEndpoint}): ${uiState.connectionState.detailMessage}",
                tone = NoticeTone.WARNING
            )
            Spacer(Modifier.height(10.dp))
        }

        if (isRegistered && !hasKey) {
            NoticeCard(
                text = stringResource(R.string.welcome_key_missing_alert),
                tone = NoticeTone.DANGER
            )
            Spacer(Modifier.height(14.dp))
        }

        ScreenActions(
            primaryLabel = when {
                isRevoked -> "Sync Device Status"
                isRegistered -> "Sign In via QR Challenge"
                else -> "Enroll This Device"
            },
            onPrimary = when {
                isRevoked -> onRefreshSync
                isRegistered -> onStartSignIn
                else -> onStartSetup
            },
            primaryEnabled = !(isRegistered && !hasKey),
            primaryLoading = uiState.isSyncingBackend,
            secondaryLabel = if (isOnline) "Review Pending Request" else "Review Request / Preview",
            onSecondary = onReviewRequest
        )

        Spacer(Modifier.height(18.dp))
        SectionTitle(text = "SECURITY MODULES")
        Spacer(Modifier.height(10.dp))

        DashboardActionTile(
            tag = "ASSET PROTECTION",
            title = "Secure Asset Vault",
            subtitle = if (isRegistered && !isRevoked) {
                "XChaCha20-Poly1305 & Watermark access via Web Console"
            } else {
                "Enroll device to authorize encrypted asset sessions"
            },
            icon = Icons.Filled.Lock,
            accent = IPGuardGoldBright,
            onClick = onOpenAssetVault
        )
        Spacer(Modifier.height(10.dp))
        DashboardActionTile(
            tag = "HARDWARE & LIFECYCLE",
            title = "Device Security & Keystore",
            subtitle = "Inspect ECDSA key, sync status, revoke or unregister rules",
            icon = Icons.Filled.Info,
            accent = if (hasKey) IPGuardVerified else IPGuardGoldBright,
            onClick = onOpenDeviceInformation
        )
        Spacer(Modifier.height(10.dp))
        DashboardActionTile(
            tag = "POLICY & ABOUT",
            title = "Security, Biometrics & About",
            subtitle = "BiometricPrompt policy, privacy guarantees & build info",
            icon = Icons.Filled.Settings,
            accent = IPGuardGoldBright,
            onClick = onOpenSecuritySettings
        )

        Spacer(Modifier.height(16.dp))
        InformationCard {
            SectionTitle(text = "SESSION SECURITY ACTIVITY")
            Spacer(Modifier.height(10.dp))
            if (uiState.activityLog.isEmpty()) {
                Text(
                    text = "No authentication or signing events recorded in this session yet.",
                    style = MaterialTheme.typography.bodySmall,
                    color = IPGuardSlate
                )
            } else {
                uiState.activityLog.take(4).forEachIndexed { idx, entry ->
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 6.dp),
                        verticalAlignment = Alignment.Top
                    ) {
                        Text(
                            text = entry.timestampLabel,
                            style = MaterialTheme.typography.labelSmall,
                            color = if (entry.isPositive) IPGuardVerified else IPGuardDanger,
                            fontFamily = FontFamily.Monospace,
                            fontSize = 10.sp
                        )
                        Spacer(Modifier.width(10.dp))
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = entry.title,
                                style = MaterialTheme.typography.labelMedium,
                                color = IPGuardPlatinum
                            )
                            Text(
                                text = entry.detail,
                                style = MaterialTheme.typography.bodySmall,
                                color = IPGuardSlate
                            )
                        }
                    }
                    if (idx < uiState.activityLog.take(4).lastIndex) {
                        CardDivider()
                    }
                }
            }
        }

        Spacer(Modifier.height(14.dp))
        Box(
            modifier = Modifier.fillMaxWidth(),
            contentAlignment = Alignment.Center
        ) {
            InlineLink(
                label = "View Hardware Keystore Details",
                onClick = onOpenDeviceInformation
            )
        }
        Spacer(Modifier.height(6.dp))
        Text(
            text = stringResource(R.string.welcome_policy),
            modifier = Modifier.fillMaxWidth(),
            style = MaterialTheme.typography.labelSmall,
            color = IPGuardGold.copy(alpha = 0.85f),
            textAlign = TextAlign.Center,
            letterSpacing = 1.4.sp
        )
    }
}
