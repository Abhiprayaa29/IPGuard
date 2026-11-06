package com.ipguard.authenticator.ui.screens.approval

import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.ipguard.authenticator.R
import com.ipguard.authenticator.ui.components.AuthenticatorScreen
import com.ipguard.authenticator.ui.components.CardDivider
import com.ipguard.authenticator.ui.components.InformationCard
import com.ipguard.authenticator.ui.components.KeyValueRow
import com.ipguard.authenticator.ui.components.NoticeCard
import com.ipguard.authenticator.ui.components.NoticeTone
import com.ipguard.authenticator.ui.components.ScreenActions
import com.ipguard.authenticator.ui.components.SectionTitle
import com.ipguard.authenticator.ui.state.AuthenticationPolicyState
import com.ipguard.authenticator.ui.state.PreviewSignInRequest
import com.ipguard.authenticator.ui.state.SigningDiagnosticState
import com.ipguard.authenticator.ui.theme.IPGuardGold
import com.ipguard.authenticator.ui.theme.IPGuardMist
import com.ipguard.authenticator.ui.theme.IPGuardMistMuted
import com.ipguard.authenticator.ui.theme.IPGuardTeal

@Composable
fun ApprovalScreen(
    request: PreviewSignInRequest,
    authPolicy: AuthenticationPolicyState = AuthenticationPolicyState(),
    signingDiagnostic: SigningDiagnosticState = SigningDiagnosticState(),
    onBack: () -> Unit,
    onApprove: () -> Unit,
    onReject: () -> Unit,
    modifier: Modifier = Modifier
) {
    AuthenticatorScreen(
        eyebrow = stringResource(R.string.approval_eyebrow),
        title = stringResource(R.string.approval_title),
        subtitle = stringResource(R.string.approval_subtitle),
        modifier = modifier,
        onBack = onBack
    ) {
        InformationCard {
            SectionTitle(text = stringResource(R.string.approval_summary_title))
            Spacer(Modifier.height(12.dp))
            Text(
                text = request.service,
                style = MaterialTheme.typography.titleLarge,
                color = IPGuardMist
            )
            Spacer(Modifier.height(4.dp))
            Text(
                text = request.browser,
                style = MaterialTheme.typography.bodyMedium,
                color = IPGuardMistMuted
            )
            Spacer(Modifier.height(16.dp))
            CardDivider()
            KeyValueRow(
                label = stringResource(R.string.request_origin_label),
                value = request.origin
            )
            KeyValueRow(
                label = stringResource(R.string.request_purpose_label),
                value = stringResource(R.string.request_purpose_value),
                showDivider = false
            )
        }

        Spacer(Modifier.height(14.dp))
        InformationCard {
            SectionTitle(text = "AUTHORIZATION & SIGNING")
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = "Approval method",
                value = authPolicy.primaryAuthMethod,
                valueColor = IPGuardTeal
            )
            KeyValueRow(
                label = "Biometric route",
                value = authPolicy.biometricStatus,
                valueColor = IPGuardGold
            )
            KeyValueRow(
                label = "Signing operation",
                value = "ECDSA P-256 (Keystore CryptoObject)",
                showDivider = false
            )
        }

        if (signingDiagnostic.errorMessage != null) {
            Spacer(Modifier.height(14.dp))
            NoticeCard(
                text = signingDiagnostic.errorMessage,
                tone = NoticeTone.WARNING
            )
        }

        if (signingDiagnostic.statusMessage != null) {
            Spacer(Modifier.height(14.dp))
            NoticeCard(
                text = signingDiagnostic.statusMessage,
                tone = NoticeTone.INFO
            )
        }

        Spacer(Modifier.height(14.dp))
        NoticeCard(
            text = "Approving will launch your device PIN or biometric prompt. Upon authentication, your private key will sign the session challenge.",
            tone = NoticeTone.INFO
        )
        Spacer(Modifier.height(10.dp))
        NoticeCard(
            text = stringResource(R.string.approval_warning),
            tone = NoticeTone.WARNING
        )
        Spacer(Modifier.height(24.dp))
        ScreenActions(
            primaryLabel = "Approve & Sign",
            onPrimary = onApprove,
            secondaryLabel = stringResource(R.string.approval_secondary_action),
            onSecondary = onReject
        )
    }
}
