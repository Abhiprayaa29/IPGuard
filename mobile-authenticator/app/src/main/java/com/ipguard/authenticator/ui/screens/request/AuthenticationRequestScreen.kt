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
import com.ipguard.authenticator.ui.components.AuthPipelineStep
import com.ipguard.authenticator.ui.components.AuthPipelineStepper
import com.ipguard.authenticator.ui.components.AuthenticatorScreen
import com.ipguard.authenticator.ui.components.InformationCard
import com.ipguard.authenticator.ui.components.KeyValueRow
import com.ipguard.authenticator.ui.components.NoticeCard
import com.ipguard.authenticator.ui.components.NoticeTone
import com.ipguard.authenticator.ui.components.PillTone
import com.ipguard.authenticator.ui.components.ScreenActions
import com.ipguard.authenticator.ui.components.SectionTitle
import com.ipguard.authenticator.ui.components.StepStatus
import com.ipguard.authenticator.ui.state.ActiveAuthSessionState
import com.ipguard.authenticator.ui.state.PreviewSignInRequest
import com.ipguard.authenticator.ui.theme.IPGuardGoldBright
import com.ipguard.authenticator.ui.theme.IPGuardVerified

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

    val eyebrow = if (isEnrollment) "DEVICE ENROLLMENT" else "SIGN-IN REQUEST"
    val title = if (isEnrollment) "Enroll this device?" else "Verify sign-in request"
    val subtitle = if (isEnrollment) {
        "Confirm the browser origin before initializing hardware biometric authorization and ECDSA P-256 registration."
    } else {
        "Confirm that you initiated this Web Console request on this device before continuing to Face Authentication."
    }

    val badgeText = when {
        isEnrollment -> "LIVE ENROLLMENT CHALLENGE"
        hasLiveSession -> "LIVE QR CHALLENGE"
        else -> "PREVIEW MODE"
    }
    val badgeTone = if (hasLiveSession) PillTone.VERIFIED else PillTone.GOLD

    val steps = listOf(
        AuthPipelineStep(
            stepCode = "STEP 01",
            title = "QR Challenge Detected",
            detail = if (hasLiveSession) "Origin and single-use challenge verified" else "Sample preview challenge loaded",
            status = if (hasLiveSession) StepStatus.COMPLETED else StepStatus.ACTIVE
        ),
        AuthPipelineStep(
            stepCode = "STEP 02",
            title = "Face Authentication",
            detail = "Waiting for Device Biometric Authentication",
            status = StepStatus.PENDING
        ),
        AuthPipelineStep(
            stepCode = "STEP 03",
            title = "Keystore Authorization",
            detail = "BIOMETRIC_STRONG / DEVICE_CREDENTIAL CryptoObject",
            status = StepStatus.PENDING
        ),
        AuthPipelineStep(
            stepCode = "STEP 04",
            title = "Cryptographic Signing",
            detail = "ECDSA P-256 non-exportable hardware signature",
            status = StepStatus.PENDING
        ),
        AuthPipelineStep(
            stepCode = "STEP 05",
            title = "Authentication Verified",
            detail = if (isEnrollment) "Register device public key with backend" else "Authorize IPGuard browser session",
            status = StepStatus.PENDING
        )
    )

    AuthenticatorScreen(
        eyebrow = eyebrow,
        title = title,
        subtitle = subtitle,
        modifier = modifier,
        onBack = onBack
    ) {
        AppPill(text = badgeText, tone = badgeTone)
        Spacer(Modifier.height(16.dp))

        AuthPipelineStepper(steps = steps)
        Spacer(Modifier.height(14.dp))

        InformationCard {
            SectionTitle(text = stringResource(R.string.request_context_title))
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = stringResource(R.string.request_service_label),
                value = request.service,
                valueColor = IPGuardGoldBright
            )
            KeyValueRow(
                label = stringResource(R.string.request_browser_label),
                value = request.browser
            )
            KeyValueRow(
                label = stringResource(R.string.request_origin_label),
                value = request.origin,
                monospaceValue = true
            )
            KeyValueRow(
                label = stringResource(R.string.request_purpose_label),
                value = if (isEnrollment) "Register Device Key & Trust Relationship" else stringResource(R.string.request_purpose_value)
            )
            KeyValueRow(
                label = stringResource(R.string.request_received_label),
                value = if (hasLiveSession) "Just now (Live QR)" else stringResource(R.string.request_received_value),
                valueColor = if (hasLiveSession) IPGuardVerified else IPGuardGoldBright,
                showDivider = false
            )
        }

        Spacer(Modifier.height(14.dp))
        NoticeCard(
            text = if (isEnrollment) {
                "Approving will link this phone's ECDSA P-256 public key to IPGuard. Only this enrolled device can sign future logins."
            } else {
                "Next step invokes Android BiometricPrompt for Face Authentication prior to Keystore signing."
            },
            tone = NoticeTone.INFO
        )
        Spacer(Modifier.height(10.dp))
        NoticeCard(
            text = stringResource(R.string.request_warning),
            tone = NoticeTone.WARNING
        )
        Spacer(Modifier.height(22.dp))
        ScreenActions(
            primaryLabel = if (isEnrollment) "Continue to Face & Signing Gate" else "Continue to Face & Approval",
            onPrimary = onReview,
            secondaryLabel = stringResource(R.string.request_secondary_action),
            onSecondary = onReject,
            tertiaryLabel = stringResource(R.string.request_scan_link),
            onTertiary = onScan
        )
    }
}
