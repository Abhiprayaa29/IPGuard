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
import com.ipguard.authenticator.ui.components.AuthPipelineStep
import com.ipguard.authenticator.ui.components.AuthPipelineStepper
import com.ipguard.authenticator.ui.components.AuthenticatorScreen
import com.ipguard.authenticator.ui.components.InformationCard
import com.ipguard.authenticator.ui.components.KeyValueRow
import com.ipguard.authenticator.ui.components.NoticeCard
import com.ipguard.authenticator.ui.components.NoticeTone
import com.ipguard.authenticator.ui.components.OutcomeSeal
import com.ipguard.authenticator.ui.components.PillTone
import com.ipguard.authenticator.ui.components.ScreenActions
import com.ipguard.authenticator.ui.components.SectionTitle
import com.ipguard.authenticator.ui.components.StepStatus
import com.ipguard.authenticator.ui.state.ActiveAuthSessionState
import com.ipguard.authenticator.ui.state.AuthFlowStep
import com.ipguard.authenticator.ui.state.PreviewResult
import com.ipguard.authenticator.ui.state.SigningDiagnosticState
import com.ipguard.authenticator.ui.theme.IPGuardDanger
import com.ipguard.authenticator.ui.theme.IPGuardGoldBright
import com.ipguard.authenticator.ui.theme.IPGuardVerified

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
            if (isEnrollment) "STEP 05 · ENROLLED" else "STEP 05 · VERIFIED"
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
            if (isEnrollment) "Device enrolled" else "Authentication verified"
        } else if (hasVerifiedLocalSignature) {
            stringResource(R.string.result_title_local_signed)
        } else {
            stringResource(R.string.result_title_approval_incomplete)
        }
    }
    val subtitle = when (outcome) {
        PreviewResult.SCAN_COMPLETE -> stringResource(R.string.result_subtitle_scan)
        PreviewResult.REJECTED -> "The request did not complete authorization. No valid session token was issued."
        PreviewResult.APPROVED -> if (isBackendApproved) {
            if (isEnrollment) {
                "Face Gate passed and Keystore ECDSA P-256 key was registered with IPGuard backend."
            } else {
                "Face Gate passed, ECDSA P-256 signature was verified by backend, and your browser session is authorized."
            }
        } else if (hasVerifiedLocalSignature) {
            stringResource(R.string.result_subtitle_local_signed)
        } else {
            stringResource(R.string.result_subtitle_approval_incomplete)
        }
    }
    val badge = when {
        outcome != PreviewResult.APPROVED -> if (outcome == PreviewResult.REJECTED) "REJECTED / CLOSED" else stringResource(R.string.result_badge)
        hasVerifiedLocalSignature -> if (isBackendApproved) "BACKEND VERIFIED" else stringResource(R.string.result_badge_local_signed)
        else -> stringResource(R.string.result_badge_not_verified)
    }
    val badgeTone = when {
        outcome == PreviewResult.REJECTED -> PillTone.DANGER
        outcome != PreviewResult.APPROVED -> PillTone.GOLD
        isBackendApproved -> PillTone.VERIFIED
        hasVerifiedLocalSignature -> PillTone.GOLD
        else -> PillTone.DANGER
    }

    val pipelineSteps = listOf(
        AuthPipelineStep(
            stepCode = "STEP 01",
            title = "QR Challenge Detected",
            detail = if (outcome == PreviewResult.REJECTED && activeSession.payload == null) "Rejected or invalid QR payload" else "Challenge parsed and validated",
            status = if (outcome == PreviewResult.REJECTED && activeSession.payload == null) StepStatus.FAILED else StepStatus.COMPLETED
        ),
        AuthPipelineStep(
            stepCode = "STEP 02",
            title = "Face Authentication",
            detail = if (hasVerifiedLocalSignature) "Biometric Authentication Successful" else "Not completed or cancelled",
            status = if (hasVerifiedLocalSignature) StepStatus.COMPLETED else StepStatus.FAILED
        ),
        AuthPipelineStep(
            stepCode = "STEP 03",
            title = "Keystore Authorization",
            detail = if (hasVerifiedLocalSignature) signingDiagnostic.authMethodLabel else "Authorization withheld",
            status = if (hasVerifiedLocalSignature) StepStatus.COMPLETED else StepStatus.FAILED
        ),
        AuthPipelineStep(
            stepCode = "STEP 04",
            title = "Cryptographic Signing",
            detail = if (hasVerifiedLocalSignature) "ECDSA P-256 signature created" else "No signature generated",
            status = if (hasVerifiedLocalSignature) StepStatus.COMPLETED else StepStatus.FAILED
        ),
        AuthPipelineStep(
            stepCode = "STEP 05",
            title = "Authentication Verified",
            detail = when {
                isBackendApproved -> if (isEnrollment) "Device registered (201 Created)" else "Session approved (200 OK)"
                hasVerifiedLocalSignature -> "Local verification only"
                else -> "Session not authorized"
            },
            status = when {
                isBackendApproved -> StepStatus.COMPLETED
                hasVerifiedLocalSignature -> StepStatus.PENDING
                else -> StepStatus.FAILED
            }
        )
    )

    BackHandler(onBack = onHome)

    AuthenticatorScreen(
        eyebrow = eyebrow,
        title = title,
        subtitle = subtitle,
        modifier = modifier,
        onBack = onHome
    ) {
        AppPill(text = badge, tone = badgeTone)
        Spacer(Modifier.height(18.dp))

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
        Spacer(Modifier.height(18.dp))

        AuthPipelineStepper(steps = pipelineSteps)
        Spacer(Modifier.height(14.dp))

        InformationCard {
            SectionTitle(text = "CRYPTOGRAPHIC RECEIPT")
            Spacer(Modifier.height(8.dp))
            if (isApproved && hasVerifiedLocalSignature) {
                KeyValueRow(
                    label = "Authorization method",
                    value = signingDiagnostic.authMethodLabel.ifBlank { "Device Authentication" },
                    valueColor = IPGuardGoldBright
                )
                KeyValueRow(
                    label = stringResource(R.string.result_key_label),
                    value = "Android Keystore (ECDSA P-256)",
                    valueColor = IPGuardVerified
                )
                KeyValueRow(
                    label = stringResource(R.string.result_local_verification_label),
                    value = stringResource(R.string.result_verified_value),
                    valueColor = IPGuardVerified
                )
                KeyValueRow(
                    label = stringResource(R.string.result_backend_label),
                    value = if (isBackendApproved) {
                        if (isEnrollment) "Registered (HTTP 201)" else "Verified (HTTP 200)"
                    } else {
                        "Local Preview Only"
                    },
                    valueColor = if (isBackendApproved) IPGuardVerified else IPGuardGoldBright,
                    monospaceValue = true
                )
                KeyValueRow(
                    label = stringResource(R.string.result_session_creation_label),
                    value = if (isBackendApproved) {
                        if (isEnrollment) "Device Active" else "Browser Session Unlocked"
                    } else {
                        stringResource(R.string.result_not_created_value)
                    },
                    showDivider = false
                )
            } else {
                KeyValueRow(
                    label = stringResource(R.string.result_auth_label),
                    value = stringResource(R.string.result_no_value),
                    valueColor = IPGuardDanger
                )
                KeyValueRow(
                    label = stringResource(R.string.result_key_label),
                    value = stringResource(R.string.result_no_value)
                )
                KeyValueRow(
                    label = stringResource(R.string.result_session_creation_label),
                    value = stringResource(R.string.result_no_value),
                    showDivider = false
                )
            }
        }

        if (activeSession.errorMessage != null) {
            Spacer(Modifier.height(12.dp))
            NoticeCard(
                text = activeSession.errorMessage,
                tone = NoticeTone.DANGER
            )
        }

        Spacer(Modifier.height(12.dp))
        NoticeCard(
            text = when {
                isBackendApproved && isEnrollment ->
                    "One-time enrollment is complete. Future authentication requests use Sign-In mode only."
                isBackendApproved ->
                    "Single-use challenge consumed and verified by IPGuard backend."
                hasVerifiedLocalSignature ->
                    stringResource(R.string.result_notice_local_signed)
                isApproved ->
                    stringResource(R.string.result_notice_not_verified)
                else ->
                    "Fail-closed guarantee: cancelled or rejected attempts leave no active authorization."
            },
            tone = when {
                isBackendApproved -> NoticeTone.SUCCESS
                isApproved && !hasVerifiedLocalSignature -> NoticeTone.WARNING
                else -> NoticeTone.INFO
            }
        )

        Spacer(Modifier.height(22.dp))
        ScreenActions(
            primaryLabel = "Return to Dashboard",
            onPrimary = onHome,
            secondaryLabel = "Device Security Status",
            onSecondary = onDeviceDetails,
            tertiaryLabel = if (isApproved && isBackendApproved) null else stringResource(R.string.result_tertiary_action),
            onTertiary = if (isApproved && isBackendApproved) null else onReviewAnother
        )
    }
}
