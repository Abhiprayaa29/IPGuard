package com.ipguard.authenticator.ui.screens.approval

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.togetherWith
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
import com.ipguard.authenticator.ui.components.AppPill
import com.ipguard.authenticator.ui.components.AuthPipelineStep
import com.ipguard.authenticator.ui.components.AuthPipelineStepper
import com.ipguard.authenticator.ui.components.AuthenticatorScreen
import com.ipguard.authenticator.ui.components.CardDivider
import com.ipguard.authenticator.ui.components.InformationCard
import com.ipguard.authenticator.ui.components.KeyValueRow
import com.ipguard.authenticator.ui.components.NoticeCard
import com.ipguard.authenticator.ui.components.NoticeTone
import com.ipguard.authenticator.ui.components.PillTone
import com.ipguard.authenticator.ui.components.ScreenActions
import com.ipguard.authenticator.ui.components.SectionTitle
import com.ipguard.authenticator.ui.components.StepStatus
import com.ipguard.authenticator.ui.state.ActiveAuthSessionState
import com.ipguard.authenticator.ui.state.AuthFlowStep
import com.ipguard.authenticator.ui.state.AuthenticationPolicyState
import com.ipguard.authenticator.ui.state.FaceGateState
import com.ipguard.authenticator.ui.state.FaceGateStatus
import com.ipguard.authenticator.ui.state.PreviewSignInRequest
import com.ipguard.authenticator.ui.state.SigningDiagnosticState
import com.ipguard.authenticator.ui.theme.IPGuardDanger
import com.ipguard.authenticator.ui.theme.IPGuardGold
import com.ipguard.authenticator.ui.theme.IPGuardGoldBright
import com.ipguard.authenticator.ui.theme.IPGuardHairline
import com.ipguard.authenticator.ui.theme.IPGuardPlatinum
import com.ipguard.authenticator.ui.theme.IPGuardSlate
import com.ipguard.authenticator.ui.theme.IPGuardVerified

@Composable
fun ApprovalScreen(
    request: PreviewSignInRequest,
    activeSession: ActiveAuthSessionState = ActiveAuthSessionState(),
    authPolicy: AuthenticationPolicyState = AuthenticationPolicyState(),
    signingDiagnostic: SigningDiagnosticState = SigningDiagnosticState(),
    faceGate: FaceGateState = FaceGateState(),
    onBack: () -> Unit,
    onApprove: () -> Unit,
    onContinueFallback: () -> Unit = {},
    onReject: () -> Unit,
    modifier: Modifier = Modifier
) {
    val isEnrollment = activeSession.payload?.type == QrSessionType.ENROLLMENT
    val hasLiveSession = activeSession.payload != null
    val isProcessing = faceGate.status == FaceGateStatus.AUTHENTICATING ||
        activeSession.step == AuthFlowStep.SUBMITTING_BACKEND

    val eyebrow = if (isEnrollment) "ENROLLMENT APPROVAL" else "SECURITY AUTHORIZATION"
    val title = if (isEnrollment) "Authorize device registration" else "Approve sign-in request"
    val subtitle = if (isEnrollment) {
        "Complete native device biometrics and Keystore authorization to bind this hardware key."
    } else {
        "Verify with native Face Authentication, then authorize your hardware ECDSA P-256 signing key."
    }

    val gateStatusText = when (faceGate.status) {
        FaceGateStatus.READY -> "Waiting for Device Biometric Authentication"
        FaceGateStatus.AUTHENTICATING -> "Complete Face Recognition on your device"
        FaceGateStatus.PASSED -> "Biometric Authentication Successful"
        FaceGateStatus.FAILED -> "Face Authentication Failed — Please Retry"
        FaceGateStatus.LOCKED_OUT -> "Biometric Lockout — Wait or Unlock Device"
        FaceGateStatus.UNAVAILABLE -> "Not supported / Not enrolled"
    }
    val gateNextCue = when (faceGate.status) {
        FaceGateStatus.PASSED -> "Authorize Cryptographic Signing"
        FaceGateStatus.AUTHENTICATING -> "OS BiometricPrompt dialog active"
        FaceGateStatus.FAILED -> "Tap Retry Face Authentication below"
        FaceGateStatus.LOCKED_OUT -> "OS cooldown required before retry"
        FaceGateStatus.UNAVAILABLE -> "Fallback requires explicit confirmation"
        FaceGateStatus.READY -> "Launches native BIOMETRIC_WEAK gate first"
    }
    val gateStatusColor = when (faceGate.status) {
        FaceGateStatus.PASSED -> IPGuardVerified
        FaceGateStatus.FAILED, FaceGateStatus.LOCKED_OUT -> IPGuardDanger
        FaceGateStatus.AUTHENTICATING, FaceGateStatus.UNAVAILABLE -> IPGuardGoldBright
        FaceGateStatus.READY -> IPGuardPlatinum
    }

    val faceStepStatus = when (faceGate.status) {
        FaceGateStatus.PASSED -> StepStatus.COMPLETED
        FaceGateStatus.AUTHENTICATING -> StepStatus.ACTIVE
        FaceGateStatus.FAILED, FaceGateStatus.LOCKED_OUT -> StepStatus.FAILED
        FaceGateStatus.UNAVAILABLE -> if (faceGate.fallbackAuthorized) StepStatus.COMPLETED else StepStatus.ACTIVE
        FaceGateStatus.READY -> StepStatus.ACTIVE
    }
    val keystoreStepStatus = when {
        signingDiagnostic.hasSigned -> StepStatus.COMPLETED
        faceGate.status == FaceGateStatus.PASSED && activeSession.step == AuthFlowStep.AWAITING_DEVICE_AUTHENTICATION -> StepStatus.ACTIVE
        faceGate.status == FaceGateStatus.PASSED -> StepStatus.ACTIVE
        else -> StepStatus.PENDING
    }
    val signingStepStatus = when {
        signingDiagnostic.hasSigned -> StepStatus.COMPLETED
        activeSession.step == AuthFlowStep.SIGNING -> StepStatus.ACTIVE
        else -> StepStatus.PENDING
    }
    val backendStepStatus = when {
        activeSession.step == AuthFlowStep.COMPLETED_APPROVED -> StepStatus.COMPLETED
        activeSession.step == AuthFlowStep.SUBMITTING_BACKEND -> StepStatus.ACTIVE
        activeSession.step == AuthFlowStep.FAILED -> StepStatus.FAILED
        else -> StepStatus.PENDING
    }

    val pipelineSteps = listOf(
        AuthPipelineStep(
            stepCode = "STEP 01",
            title = "QR Challenge Detected",
            detail = if (hasLiveSession) "${request.origin} (live session)" else "${request.origin} (preview)",
            status = StepStatus.COMPLETED
        ),
        AuthPipelineStep(
            stepCode = "STEP 02",
            title = "Face Authentication",
            detail = gateStatusText,
            status = faceStepStatus
        ),
        AuthPipelineStep(
            stepCode = "STEP 03",
            title = "Keystore Authorization",
            detail = if (faceGate.status == FaceGateStatus.PASSED) "Authorize Cryptographic Signing" else authPolicy.primaryAuthMethod,
            status = keystoreStepStatus
        ),
        AuthPipelineStep(
            stepCode = "STEP 04",
            title = "Cryptographic Signing",
            detail = if (signingDiagnostic.hasSigned) "ECDSA P-256 signature generated" else "Non-exportable TEE / StrongBox signature",
            status = signingStepStatus
        ),
        AuthPipelineStep(
            stepCode = "STEP 05",
            title = "Authentication Verified",
            detail = if (activeSession.step == AuthFlowStep.SUBMITTING_BACKEND) "Submitting challenge signature..." else "Verify challenge signature on backend",
            status = backendStepStatus
        )
    )

    AuthenticatorScreen(
        eyebrow = eyebrow,
        title = title,
        subtitle = subtitle,
        modifier = modifier,
        onBack = onBack
    ) {
        AppPill(
            text = when (faceGate.status) {
                FaceGateStatus.PASSED -> "BIOMETRIC GATE PASSED"
                FaceGateStatus.AUTHENTICATING -> "BIOMETRIC PROMPT ACTIVE"
                FaceGateStatus.FAILED, FaceGateStatus.LOCKED_OUT -> "BIOMETRIC RETRY REQUIRED"
                else -> if (isEnrollment) "ENROLLMENT APPROVAL" else "TWO-STAGE AUTHORIZATION"
            },
            tone = when (faceGate.status) {
                FaceGateStatus.PASSED -> PillTone.VERIFIED
                FaceGateStatus.FAILED, FaceGateStatus.LOCKED_OUT -> PillTone.DANGER
                else -> PillTone.GOLD
            }
        )
        Spacer(Modifier.height(16.dp))

        AuthPipelineStepper(steps = pipelineSteps)
        Spacer(Modifier.height(14.dp))

        InformationCard(
            borderColor = when (faceGate.status) {
                FaceGateStatus.PASSED -> IPGuardVerified.copy(alpha = 0.4f)
                FaceGateStatus.FAILED, FaceGateStatus.LOCKED_OUT -> IPGuardDanger.copy(alpha = 0.4f)
                FaceGateStatus.AUTHENTICATING -> IPGuardGold.copy(alpha = 0.5f)
                else -> IPGuardHairline
            }
        ) {
            SectionTitle(text = "NATIVE FACE AUTHENTICATION GATE")
            Spacer(Modifier.height(10.dp))
            AnimatedContent(
                targetState = gateStatusText,
                transitionSpec = { fadeIn() togetherWith fadeOut() },
                label = "faceGateStatusText"
            ) { text ->
                Text(
                    text = text,
                    style = MaterialTheme.typography.titleMedium,
                    color = gateStatusColor
                )
            }
            Spacer(Modifier.height(4.dp))
            Text(
                text = gateNextCue,
                style = MaterialTheme.typography.bodySmall,
                color = IPGuardSlate
            )
            Spacer(Modifier.height(12.dp))
            CardDivider()
            KeyValueRow(
                label = "Gate authenticator",
                value = "Android BiometricPrompt (BIOMETRIC_WEAK)",
                monospaceValue = true
            )
            KeyValueRow(
                label = "Hardware availability",
                value = faceGate.availabilityLabel,
                valueColor = if (faceGate.isWeakBiometricAvailable) IPGuardVerified else IPGuardGoldBright,
                showDivider = false
            )
        }

        Spacer(Modifier.height(14.dp))
        InformationCard {
            SectionTitle(text = stringResource(R.string.approval_summary_title))
            Spacer(Modifier.height(10.dp))
            KeyValueRow(
                label = "Service",
                value = "${request.service} (${request.browser})"
            )
            KeyValueRow(
                label = stringResource(R.string.request_origin_label),
                value = request.origin,
                monospaceValue = true
            )
            KeyValueRow(
                label = stringResource(R.string.approval_method_label),
                value = authPolicy.primaryAuthMethod,
                valueColor = IPGuardGoldBright
            )
            KeyValueRow(
                label = stringResource(R.string.approval_signing_operation_label),
                value = if (isEnrollment) "ECDSA P-256 (Enrollment)" else "ECDSA P-256 (CryptoObject)",
                showDivider = false
            )
        }

        if (faceGate.errorMessage != null) {
            Spacer(Modifier.height(12.dp))
            NoticeCard(
                text = faceGate.errorMessage,
                tone = NoticeTone.DANGER
            )
        } else if (faceGate.statusMessage != null) {
            Spacer(Modifier.height(12.dp))
            NoticeCard(
                text = faceGate.statusMessage,
                tone = if (faceGate.status == FaceGateStatus.PASSED) NoticeTone.SUCCESS else NoticeTone.INFO
            )
        }

        if (signingDiagnostic.errorMessage != null) {
            Spacer(Modifier.height(12.dp))
            NoticeCard(
                text = signingDiagnostic.errorMessage,
                tone = NoticeTone.WARNING
            )
        }

        Spacer(Modifier.height(12.dp))
        NoticeCard(
            text = stringResource(R.string.approval_warning),
            tone = NoticeTone.WARNING
        )
        Spacer(Modifier.height(22.dp))

        val effectivePrimaryLabel = when {
            activeSession.step == AuthFlowStep.SUBMITTING_BACKEND -> "Verifying signature on backend..."
            faceGate.status == FaceGateStatus.AUTHENTICATING -> "Complete Face Recognition on your device..."
            !faceGate.isWeakBiometricAvailable && faceGate.status == FaceGateStatus.UNAVAILABLE ->
                "Continue with existing authentication"
            faceGate.status == FaceGateStatus.FAILED ->
                "Retry Face Authentication"
            faceGate.status == FaceGateStatus.LOCKED_OUT ->
                "Retry Face Gate (Locked)"
            faceGate.status == FaceGateStatus.PASSED ->
                "Authorize Cryptographic Signing"
            isEnrollment ->
                "Verify Face & Register Device"
            else ->
                "Verify Face & Approve Sign-In"
        }
        val effectivePrimaryAction = if (!faceGate.isWeakBiometricAvailable && faceGate.status == FaceGateStatus.UNAVAILABLE) {
            onContinueFallback
        } else {
            onApprove
        }

        ScreenActions(
            primaryLabel = effectivePrimaryLabel,
            onPrimary = effectivePrimaryAction,
            primaryEnabled = !isProcessing,
            primaryLoading = isProcessing,
            secondaryLabel = stringResource(R.string.approval_secondary_action),
            onSecondary = onReject,
            secondaryEnabled = !isProcessing
        )
    }
}
