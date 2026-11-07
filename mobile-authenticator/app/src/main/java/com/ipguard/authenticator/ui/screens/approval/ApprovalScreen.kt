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
import com.ipguard.authenticator.security.qr.QrSessionType
import com.ipguard.authenticator.ui.components.AuthenticatorScreen
import com.ipguard.authenticator.ui.components.CardDivider
import com.ipguard.authenticator.ui.components.InformationCard
import com.ipguard.authenticator.ui.components.KeyValueRow
import com.ipguard.authenticator.ui.components.NoticeCard
import com.ipguard.authenticator.ui.components.NoticeTone
import com.ipguard.authenticator.ui.components.ScreenActions
import com.ipguard.authenticator.ui.components.SectionTitle
import com.ipguard.authenticator.ui.state.ActiveAuthSessionState
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
    activeSession: ActiveAuthSessionState = ActiveAuthSessionState(),
    authPolicy: AuthenticationPolicyState = AuthenticationPolicyState(),
    signingDiagnostic: SigningDiagnosticState = SigningDiagnosticState(),
    onBack: () -> Unit,
    onApprove: () -> Unit,
    onReject: () -> Unit,
    modifier: Modifier = Modifier
) {
    val isEnrollment = activeSession.payload?.type == QrSessionType.ENROLLMENT
    val hasLiveSession = activeSession.payload != null

    val eyebrow = if (isEnrollment) {
        "ENROLLMENT APPROVAL"
    } else {
        stringResource(R.string.approval_eyebrow)
    }

    val title = if (isEnrollment) {
        "Authorize device registration"
    } else {
        stringResource(R.string.approval_title)
    }

    val subtitle = if (isEnrollment) {
        "Confirm registration of this device's public key with IPGuard backend."
    } else {
        stringResource(R.string.approval_subtitle)
    }

    val primaryActionLabel = if (isEnrollment) {
        "Approve & Register Device"
    } else {
        stringResource(R.string.approval_primary_action)
    }

    val signingOpValue = if (isEnrollment) {
        "ECDSA P-256 (Enrollment Registration)"
    } else {
        stringResource(R.string.approval_signing_operation_value)
    }

    AuthenticatorScreen(
        eyebrow = eyebrow,
        title = title,
        subtitle = subtitle,
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
                value = if (isEnrollment) "Register Device Key & Trust Relationship" else stringResource(R.string.request_purpose_value),
                showDivider = false
            )
        }

        Spacer(Modifier.height(14.dp))
        InformationCard {
            SectionTitle(text = stringResource(R.string.approval_shape_title))
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = stringResource(R.string.approval_method_label),
                value = authPolicy.primaryAuthMethod,
                valueColor = IPGuardTeal
            )
            KeyValueRow(
                label = stringResource(R.string.approval_biometric_label),
                value = authPolicy.biometricStatus,
                valueColor = IPGuardGold
            )
            KeyValueRow(
                label = stringResource(R.string.approval_signing_operation_label),
                value = signingOpValue,
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
            text = if (isEnrollment) {
                "Approving will prompt for your device PIN or biometric to authorize signing the enrollment challenge."
            } else {
                stringResource(R.string.approval_signing_note)
            },
            tone = NoticeTone.INFO
        )
        Spacer(Modifier.height(10.dp))
        NoticeCard(
            text = stringResource(R.string.approval_warning),
            tone = NoticeTone.WARNING
        )
        Spacer(Modifier.height(24.dp))
        ScreenActions(
            primaryLabel = primaryActionLabel,
            onPrimary = onApprove,
            secondaryLabel = stringResource(R.string.approval_secondary_action),
            onSecondary = onReject
        )
    }
}
