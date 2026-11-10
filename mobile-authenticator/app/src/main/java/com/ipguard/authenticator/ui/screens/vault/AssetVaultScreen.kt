package com.ipguard.authenticator.ui.screens.vault

import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.ipguard.authenticator.ui.components.AppPill
import com.ipguard.authenticator.ui.components.AuthenticatorScreen
import com.ipguard.authenticator.ui.components.CardDivider
import com.ipguard.authenticator.ui.components.InformationCard
import com.ipguard.authenticator.ui.components.KeyValueRow
import com.ipguard.authenticator.ui.components.NoticeCard
import com.ipguard.authenticator.ui.components.NoticeTone
import com.ipguard.authenticator.ui.components.PillTone
import com.ipguard.authenticator.ui.components.PrincipleRow
import com.ipguard.authenticator.ui.components.ScreenActions
import com.ipguard.authenticator.ui.components.SectionTitle
import com.ipguard.authenticator.ui.state.AuthenticatorUiState
import com.ipguard.authenticator.ui.state.BackendConnectionStatus
import com.ipguard.authenticator.ui.theme.IPGuardDanger
import com.ipguard.authenticator.ui.theme.IPGuardGoldBright
import com.ipguard.authenticator.ui.theme.IPGuardSlate
import com.ipguard.authenticator.ui.theme.IPGuardVerified

@Composable
fun AssetVaultScreen(
    uiState: AuthenticatorUiState,
    onBack: () -> Unit,
    onUnlockWithQr: () -> Unit,
    onOpenDeviceSecurity: () -> Unit,
    onRefreshSync: () -> Unit,
    modifier: Modifier = Modifier
) {
    val isActive = uiState.isRegistered && uiState.registrationStatus == "ACTIVE"
    val isRevoked = uiState.registrationStatus == "REVOKED"
    val isOnline = uiState.connectionState.status == BackendConnectionStatus.CONNECTED

    AuthenticatorScreen(
        eyebrow = "ENCRYPTED VAULT",
        title = "Secure Asset Vault",
        subtitle = "Zero-knowledge encrypted digital assets protected by XChaCha20-Poly1305 and hardware-bound authorization.",
        modifier = modifier,
        onBack = onBack
    ) {
        AppPill(
            text = when {
                isRevoked -> "ACCESS REVOKED"
                isActive -> "VAULT AUTHORIZER READY"
                else -> "ENROLLMENT REQUIRED"
            },
            tone = when {
                isRevoked -> PillTone.DANGER
                isActive -> PillTone.VERIFIED
                else -> PillTone.GOLD
            }
        )
        Spacer(Modifier.height(18.dp))

        InformationCard {
            SectionTitle(text = "ENCRYPTED ASSETS OVERVIEW")
            Spacer(Modifier.height(10.dp))
            KeyValueRow(
                label = "Vault encryption",
                value = "XChaCha20-Poly1305 AEAD",
                valueColor = IPGuardGoldBright
            )
            KeyValueRow(
                label = "Key derivation",
                value = "HKDF-SHA256 (per-device)"
            )
            KeyValueRow(
                label = "Watermark integrity",
                value = "PNG LSB + Ed25519 Signature"
            )
            KeyValueRow(
                label = "Device binding",
                value = uiState.registrationStatus,
                valueColor = when {
                    isActive -> IPGuardVerified
                    isRevoked -> IPGuardDanger
                    else -> IPGuardGoldBright
                }
            )
            KeyValueRow(
                label = "Encrypted asset count",
                value = if (isActive) "Managed in Web Console" else "Unavailable before enrollment",
                valueColor = IPGuardSlate
            )
            KeyValueRow(
                label = "Backend connectivity",
                value = uiState.connectionState.statusLabel,
                valueColor = if (isOnline) IPGuardVerified else IPGuardGoldBright,
                showDivider = false
            )
        }

        Spacer(Modifier.height(14.dp))
        InformationCard {
            SectionTitle(text = "HOW VAULT ACCESS WORKS")
            Spacer(Modifier.height(14.dp))
            PrincipleRow(
                marker = "01",
                text = "Assets are uploaded, decrypted in memory, and inspected inside the authenticated IPGuard Web Console."
            )
            Spacer(Modifier.height(12.dp))
            PrincipleRow(
                marker = "02",
                text = "Each browser vault session requires a live QR challenge authorized by this phone's Face Gate and Keystore ECDSA P-256 key."
            )
            Spacer(Modifier.height(12.dp))
            CardDivider()
            Spacer(Modifier.height(12.dp))
            PrincipleRow(
                marker = "03",
                text = "Master encryption keys and plaintext assets are never stored inside this mobile authenticator."
            )
        }

        Spacer(Modifier.height(14.dp))
        NoticeCard(
            text = if (isActive) {
                "Your device is active. Scan the sign-in QR on IPGuard Web Console to unlock encrypted assets and steganographic watermarking."
            } else {
                "Complete one-time device enrollment before authorizing Web Console vault sessions."
            },
            tone = if (isRevoked) NoticeTone.WARNING else NoticeTone.INFO
        )

        Spacer(Modifier.height(22.dp))
        ScreenActions(
            primaryLabel = if (isActive) "Scan Web Vault Sign-In QR" else "Enroll Device First",
            onPrimary = onUnlockWithQr,
            primaryEnabled = !isRevoked,
            secondaryLabel = "Device Security Status",
            onSecondary = onOpenDeviceSecurity,
            tertiaryLabel = if (uiState.isSyncingBackend) "Syncing backend..." else "Refresh Backend Sync",
            onTertiary = onRefreshSync
        )
    }
}
