package com.ipguard.authenticator.ui.screens.request

import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.ipguard.authenticator.R
import com.ipguard.authenticator.security.qr.QrSessionType
import com.ipguard.authenticator.ui.components.AppPill
import com.ipguard.authenticator.ui.components.AuthenticatorScreen
import com.ipguard.authenticator.ui.components.InformationCard
import com.ipguard.authenticator.ui.components.KeyValueRow
import com.ipguard.authenticator.ui.components.NoticeCard
import com.ipguard.authenticator.ui.components.NoticeTone
import com.ipguard.authenticator.ui.components.PillTone
import com.ipguard.authenticator.ui.components.ScreenActions
import com.ipguard.authenticator.ui.components.SectionTitle
import com.ipguard.authenticator.ui.state.ActiveAuthSessionState
import com.ipguard.authenticator.ui.state.PreviewSignInRequest

@Composable
fun AuthenticationRequestScreen(
    request: PreviewSignInRequest,
    activeSession: ActiveAuthSessionState = ActiveAuthSessionState(),
    onBack: () -> Unit,
    onReview: () -> Unit,
    onReject: () -> Unit,
    onScan: () -> Unit,
    modifier: Modifier = Modifier
) {
    val isEnrollment = activeSession.payload?.type == QrSessionType.ENROLLMENT
    val hasLiveSession = activeSession.payload != null

    val eyebrow = if (isEnrollment) {
        "DEVICE ENROLLMENT"
    } else {
        stringResource(R.string.request_eyebrow)
    }

    val title = if (isEnrollment) {
        "Enroll this device?"
    } else {
        stringResource(R.string.request_title)
    }

    val subtitle = if (isEnrollment) {
        "A web session is requesting to register this device as your trusted authenticator."
    } else {
        stringResource(R.string.request_subtitle)
    }

    val badgeText = when {
        isEnrollment -> "DEVICE REGISTRATION"
        hasLiveSession -> "LIVE QR SESSION"
        else -> stringResource(R.string.request_sample_badge)
    }

    val badgeTone = if (hasLiveSession) PillTone.TEAL else PillTone.GOLD

    val purposeValue = if (isEnrollment) {
        "Register Device Key & Trust Relationship"
    } else {
        stringResource(R.string.request_purpose_value)
    }

    val primaryActionLabel = if (isEnrollment) {
        "Review enrollment"
    } else {
        stringResource(R.string.request_primary_action)
    }

    AuthenticatorScreen(
        eyebrow = eyebrow,
        title = title,
        subtitle = subtitle,
        modifier = modifier,
        onBack = onBack
    ) {
        AppPill(
            text = badgeText,
            tone = badgeTone
        )
        Spacer(Modifier.height(20.dp))

        InformationCard {
            SectionTitle(text = stringResource(R.string.request_context_title))
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = stringResource(R.string.request_service_label),
                value = request.service
            )
            KeyValueRow(
                label = stringResource(R.string.request_browser_label),
                value = request.browser
            )
            KeyValueRow(
                label = stringResource(R.string.request_origin_label),
                value = request.origin
            )
            KeyValueRow(
                label = stringResource(R.string.request_purpose_label),
                value = purposeValue
            )
            KeyValueRow(
                label = stringResource(R.string.request_received_label),
                value = if (hasLiveSession) "Just now (Live QR)" else stringResource(R.string.request_received_value),
                showDivider = false
            )
        }

        Spacer(Modifier.height(14.dp))
        NoticeCard(
            text = if (isEnrollment) {
                "Approving will register this phone's ECDSA public key with IPGuard. Only this phone will be able to approve sign-ins."
            } else {
                stringResource(R.string.request_notice)
            },
            tone = NoticeTone.INFO
        )
        Spacer(Modifier.height(10.dp))
        NoticeCard(
            text = stringResource(R.string.request_warning),
            tone = NoticeTone.WARNING
        )
        Spacer(Modifier.height(24.dp))
        ScreenActions(
            primaryLabel = primaryActionLabel,
            onPrimary = onReview,
            secondaryLabel = stringResource(R.string.request_secondary_action),
            onSecondary = onReject,
            tertiaryLabel = stringResource(R.string.request_scan_link),
            onTertiary = onScan
        )
    }
}
