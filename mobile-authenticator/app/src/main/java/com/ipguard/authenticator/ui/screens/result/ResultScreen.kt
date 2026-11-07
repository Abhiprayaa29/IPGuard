package com.ipguard.authenticator.ui.screens.result

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
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
import com.ipguard.authenticator.ui.components.OutcomeSeal
import com.ipguard.authenticator.ui.components.PillTone
import com.ipguard.authenticator.ui.components.ScreenActions
import com.ipguard.authenticator.ui.components.SectionTitle
import com.ipguard.authenticator.ui.state.ActiveAuthSessionState
import com.ipguard.authenticator.ui.state.AuthFlowStep
import com.ipguard.authenticator.ui.state.PreviewResult
import com.ipguard.authenticator.ui.state.SigningDiagnosticState

@Composable
fun ResultScreen(
    outcome: PreviewResult,
    onHome: () -> Unit,
    onDeviceDetails: () -> Unit,
    onReviewAnother: () -> Unit,
    modifier: Modifier = Modifier,
    signingDiagnostic: SigningDiagnosticState = SigningDiagnosticState(),
    activeSession: ActiveAuthSessionState = ActiveAuthSessionState()
) {
    val isApproved = outcome == PreviewResult.APPROVED
    val hasVerifiedLocalSignature = isApproved &&
        signingDiagnostic.hasSigned &&
        signingDiagnostic.verifiedLocally

    val isBackendApproved = isApproved && activeSession.step == AuthFlowStep.COMPLETED_APPROVED
    val isEnrollment = activeSession.payload?.type == QrSessionType.ENROLLMENT

    val eyebrow = when (outcome) {
        PreviewResult.SCAN_COMPLETE -> stringResource(R.string.result_eyebrow_scan)
        PreviewResult.REJECTED -> stringResource(R.string.result_eyebrow_rejected)
        PreviewResult.APPROVED -> if (isBackendApproved) {
            if (isEnrollment) "DEVICE REGISTERED" else "AUTHENTICATION APPROVED"
        } else if (hasVerifiedLocalSignature) {
            stringResource(R.string.result_eyebrow_local_signed)
        } else {
            stringResource(R.string.result_eyebrow_approval_incomplete)
        }
    }
    val title = when (outcome) {
        PreviewResult.SCAN_COMPLETE -> stringResource(R.string.result_title_scan)
        PreviewResult.REJECTED -> stringResource(R.string.result_title_rejected)
        PreviewResult.APPROVED -> if (isBackendApproved) {
            if (isEnrollment) "Device enrolled successfully" else "Sign-in approved successfully"
        } else if (hasVerifiedLocalSignature) {
            stringResource(R.string.result_title_local_signed)
        } else {
            stringResource(R.string.result_title_approval_incomplete)
        }
    }
    val subtitle = when (outcome) {
        PreviewResult.SCAN_COMPLETE -> stringResource(R.string.result_subtitle_scan)
        PreviewResult.REJECTED -> stringResource(R.string.result_subtitle_rejected)
        PreviewResult.APPROVED -> if (isBackendApproved) {
            if (isEnrollment) {
                "This device is now trusted by IPGuard backend. Future web sign-in requests can be verified here."
            } else {
                "ECDSA signature verified by backend. Web console session has been authorized."
            }
        } else if (hasVerifiedLocalSignature) {
            stringResource(R.string.result_subtitle_local_signed)
        } else {
            stringResource(R.string.result_subtitle_approval_incomplete)
        }
    }
    val badge = when {
        outcome != PreviewResult.APPROVED -> stringResource(R.string.result_badge)
        hasVerifiedLocalSignature -> if (isBackendApproved) "BACKEND VERIFIED" else stringResource(R.string.result_badge_local_signed)
        else -> stringResource(R.string.result_badge_not_verified)
    }
    val badgeTone = when {
        outcome != PreviewResult.APPROVED -> PillTone.GOLD
        hasVerifiedLocalSignature -> PillTone.TEAL
        else -> PillTone.DANGER
    }
    val noticeText = when {
        isBackendApproved -> if (isEnrollment) {
            "Device key successfully registered in backend PostgreSQL database. This phone is now bound to your account."
        } else {
            "Single-use authentication challenge consumed and verified by backend. The browser session is active."
        }
        hasVerifiedLocalSignature -> stringResource(R.string.result_notice_local_signed)
        isApproved -> stringResource(R.string.result_notice_not_verified)
        else -> stringResource(R.string.result_notice)
    }
    val noticeTone = if (isApproved && !hasVerifiedLocalSignature) {
        NoticeTone.WARNING
    } else {
        NoticeTone.INFO
    }

    BackHandler(onBack = onHome)

    AuthenticatorScreen(
        eyebrow = eyebrow,
        title = title,
        subtitle = subtitle,
        modifier = modifier,
        onBack = onHome
    ) {
        AppPill(
            text = badge,
            tone = badgeTone
        )
        Spacer(Modifier.height(22.dp))
        Box(
            modifier = Modifier.fillMaxWidth(),
            contentAlignment = Alignment.Center
        ) {
            OutcomeSeal(
                positive = when (outcome) {
                    PreviewResult.SCAN_COMPLETE -> true
                    PreviewResult.REJECTED -> false
                    PreviewResult.APPROVED -> hasVerifiedLocalSignature
                }
            )
        }
        Spacer(Modifier.height(22.dp))

        InformationCard {
            SectionTitle(text = stringResource(R.string.result_state_title))
            Spacer(Modifier.height(8.dp))
            if (isApproved && hasVerifiedLocalSignature) {
                KeyValueRow(
                    label = stringResource(R.string.result_approval_decision_label),
                    value = stringResource(R.string.result_approval_decision_approved_local)
                )
                KeyValueRow(
                    label = stringResource(R.string.result_auth_label),
                    value = stringResource(R.string.result_yes_local_auth_value)
                )
                KeyValueRow(
                    label = stringResource(R.string.result_key_label),
                    value = stringResource(R.string.result_yes_keystore_value)
                )
                KeyValueRow(
                    label = stringResource(R.string.result_signature_created_label),
                    value = stringResource(R.string.result_signature_created_value)
                )
                KeyValueRow(
                    label = stringResource(R.string.result_local_verification_label),
                    value = stringResource(R.string.result_verified_value)
                )
                KeyValueRow(
                    label = stringResource(R.string.result_backend_label),
                    value = if (isBackendApproved) {
                        "Verified & Accepted (200 OK)"
                    } else {
                        stringResource(R.string.result_not_implemented_value)
                    }
                )
                KeyValueRow(
                    label = stringResource(R.string.result_session_creation_label),
                    value = if (isBackendApproved) {
                        if (isEnrollment) "Device Registered" else "Session Authorized"
                    } else {
                        stringResource(R.string.result_not_created_value)
                    },
                    showDivider = false
                )
            } else if (isApproved) {
                KeyValueRow(
                    label = stringResource(R.string.result_approval_decision_label),
                    value = stringResource(R.string.result_approval_decision_incomplete)
                )
                KeyValueRow(
                    label = stringResource(R.string.result_auth_label),
                    value = stringResource(R.string.result_no_value)
                )
                KeyValueRow(
                    label = stringResource(R.string.result_key_label),
                    value = stringResource(R.string.result_no_value)
                )
                KeyValueRow(
                    label = stringResource(R.string.result_signature_created_label),
                    value = stringResource(R.string.result_not_created_value)
                )
                KeyValueRow(
                    label = stringResource(R.string.result_local_verification_label),
                    value = stringResource(R.string.result_not_performed_value)
                )
                KeyValueRow(
                    label = stringResource(R.string.result_backend_label),
                    value = stringResource(R.string.result_no_value)
                )
                KeyValueRow(
                    label = stringResource(R.string.result_session_creation_label),
                    value = stringResource(R.string.result_no_value),
                    showDivider = false
                )
            } else {
                KeyValueRow(
                    label = stringResource(R.string.result_auth_label),
                    value = stringResource(R.string.result_no_value)
                )
                KeyValueRow(
                    label = stringResource(R.string.result_key_label),
                    value = stringResource(R.string.result_no_value)
                )
                KeyValueRow(
                    label = stringResource(R.string.result_session_label),
                    value = stringResource(R.string.result_no_value),
                    showDivider = false
                )
            }
        }

        if (activeSession.errorMessage != null) {
            Spacer(Modifier.height(14.dp))
            NoticeCard(
                text = activeSession.errorMessage,
                tone = NoticeTone.WARNING
            )
        }

        Spacer(Modifier.height(14.dp))
        NoticeCard(
            text = noticeText,
            tone = noticeTone
        )

        Spacer(Modifier.height(24.dp))
        ScreenActions(
            primaryLabel = stringResource(R.string.result_primary_action),
            onPrimary = onHome,
            secondaryLabel = stringResource(R.string.result_secondary_action),
            onSecondary = onDeviceDetails,
            tertiaryLabel = stringResource(R.string.result_tertiary_action),
            onTertiary = onReviewAnother
        )
    }
}
