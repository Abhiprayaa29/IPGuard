package com.ipguard.authenticator.ui.screens.scanner

import androidx.camera.core.CameraSelector
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.ipguard.authenticator.R
import com.ipguard.authenticator.ui.camera.CameraPreview
import com.ipguard.authenticator.ui.camera.QrCodeAnalyzer
import com.ipguard.authenticator.ui.camera.rememberCameraPermissionState
import com.ipguard.authenticator.ui.components.AppPill
import com.ipguard.authenticator.ui.components.AuthenticatorScreen
import com.ipguard.authenticator.ui.components.CameraStage
import com.ipguard.authenticator.ui.components.InformationCard
import com.ipguard.authenticator.ui.components.InlineLink
import com.ipguard.authenticator.ui.components.NoticeCard
import com.ipguard.authenticator.ui.components.NoticeTone
import com.ipguard.authenticator.ui.components.PillTone
import com.ipguard.authenticator.ui.components.PrincipleRow
import com.ipguard.authenticator.ui.components.ScreenActions
import com.ipguard.authenticator.ui.components.SectionTitle
import com.ipguard.authenticator.ui.theme.IPGuardGoldBright
import com.ipguard.authenticator.ui.theme.IPGuardSlate

@Composable
fun QrScannerScreen(
    onBack: () -> Unit,
    onScanComplete: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    val permission = rememberCameraPermissionState()
    var cameraError by remember { mutableStateOf(false) }
    var cameraAttempt by remember { mutableIntStateOf(0) }
    val analyzer = remember {
        QrCodeAnalyzer { rawBarcode ->
            onScanComplete(rawBarcode)
        }
    }

    DisposableEffect(Unit) {
        onDispose {
            analyzer.close()
        }
    }

    val overlayText = when {
        !permission.granted -> stringResource(R.string.scanner_overlay_permission)
        cameraError -> stringResource(R.string.scanner_overlay_error)
        else -> "Align Web Console QR challenge inside frame"
    }

    AuthenticatorScreen(
        eyebrow = "STEP 01 · QR CHALLENGE",
        title = "Scan challenge QR",
        subtitle = "Point the rear camera at the IPGuard Web Console challenge QR code to validate session origin and nonce.",
        modifier = modifier,
        onBack = onBack
    ) {
        AppPill(
            text = if (permission.granted && !cameraError) "ON-DEVICE ML KIT SCANNER" else "CAMERA REQUIRED",
            tone = if (permission.granted && !cameraError) PillTone.GOLD else PillTone.DANGER
        )
        Spacer(Modifier.height(16.dp))

        if (permission.granted && !cameraError) {
            key(cameraAttempt) {
                CameraStage(
                    badge = stringResource(R.string.scanner_camera_badge),
                    label = stringResource(R.string.scanner_camera_label),
                    monogram = "QR",
                    accent = IPGuardGoldBright,
                    overlayText = overlayText,
                    cameraContent = {
                        CameraPreview(
                            lensFacing = CameraSelector.LENS_FACING_BACK,
                            analyzer = analyzer,
                            modifier = Modifier.fillMaxSize(),
                            onCameraError = {
                                cameraError = true
                            }
                        )
                    }
                )
            }
        } else {
            CameraStage(
                badge = stringResource(R.string.scanner_camera_badge),
                label = stringResource(R.string.scanner_camera_label),
                placeholder = if (permission.granted) {
                    stringResource(R.string.scanner_overlay_error)
                } else {
                    stringResource(R.string.scanner_camera_placeholder)
                },
                hint = if (permission.granted) {
                    stringResource(R.string.camera_unavailable_notice)
                } else {
                    stringResource(R.string.scanner_camera_hint)
                },
                monogram = "QR",
                accent = IPGuardGoldBright
            )
        }

        if (!permission.granted) {
            Spacer(Modifier.height(14.dp))
            InformationCard {
                SectionTitle(text = stringResource(R.string.camera_permission_title))
                Spacer(Modifier.height(10.dp))
                Text(
                    text = stringResource(R.string.camera_permission_body),
                    style = MaterialTheme.typography.bodyMedium,
                    color = IPGuardSlate
                )
            }
            Spacer(Modifier.height(12.dp))
            NoticeCard(
                text = stringResource(R.string.camera_permission_denied_notice),
                tone = NoticeTone.WARNING
            )
        }

        if (cameraError) {
            Spacer(Modifier.height(14.dp))
            NoticeCard(
                text = stringResource(R.string.camera_unavailable_notice),
                tone = NoticeTone.WARNING
            )
        }

        Spacer(Modifier.height(14.dp))
        InformationCard {
            SectionTitle(text = "CHALLENGE VALIDATION SAFETY")
            Spacer(Modifier.height(14.dp))
            PrincipleRow(
                marker = "01",
                text = stringResource(R.string.scanner_safety_one)
            )
            Spacer(Modifier.height(12.dp))
            PrincipleRow(
                marker = "02",
                text = stringResource(R.string.scanner_safety_two)
            )
            Spacer(Modifier.height(12.dp))
            PrincipleRow(
                marker = "03",
                text = stringResource(R.string.scanner_safety_three)
            )
        }

        Spacer(Modifier.height(12.dp))
        NoticeCard(
            text = "Challenges are validated strictly on-device before biometric prompts appear. No QR image frames are stored.",
            tone = NoticeTone.INFO
        )
        Spacer(Modifier.height(22.dp))

        when {
            !permission.granted -> {
                ScreenActions(
                    primaryLabel = stringResource(R.string.camera_permission_allow),
                    onPrimary = permission.requestPermission,
                    secondaryLabel = stringResource(R.string.camera_permission_settings),
                    onSecondary = permission.openAppSettings,
                    tertiaryLabel = stringResource(R.string.scanner_secondary_action),
                    onTertiary = onBack
                )
            }

            cameraError -> {
                ScreenActions(
                    primaryLabel = stringResource(R.string.camera_retry),
                    onPrimary = {
                        cameraError = false
                        cameraAttempt += 1
                    },
                    secondaryLabel = stringResource(R.string.scanner_secondary_action),
                    onSecondary = onBack
                )
            }

            else -> {
                Box(
                    modifier = Modifier.fillMaxWidth(),
                    contentAlignment = Alignment.Center
                ) {
                    InlineLink(
                        label = stringResource(R.string.scanner_secondary_action),
                        onClick = onBack
                    )
                }
            }
        }
    }
}
