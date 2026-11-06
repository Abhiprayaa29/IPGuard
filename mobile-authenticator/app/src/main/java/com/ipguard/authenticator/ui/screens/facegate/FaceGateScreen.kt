package com.ipguard.authenticator.ui.screens.facegate

import androidx.camera.core.CameraSelector
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
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
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.ipguard.authenticator.R
import com.ipguard.authenticator.ui.camera.CameraPreview
import com.ipguard.authenticator.ui.camera.FacePresenceAnalyzer
import com.ipguard.authenticator.ui.camera.rememberCameraPermissionState
import com.ipguard.authenticator.ui.components.AuthenticatorScreen
import com.ipguard.authenticator.ui.components.CameraStage
import com.ipguard.authenticator.ui.components.InformationCard
import com.ipguard.authenticator.ui.components.KeyValueRow
import com.ipguard.authenticator.ui.components.NoticeCard
import com.ipguard.authenticator.ui.components.NoticeTone
import com.ipguard.authenticator.ui.components.ScreenActions
import com.ipguard.authenticator.ui.components.SectionTitle
import com.ipguard.authenticator.ui.theme.IPGuardDanger
import com.ipguard.authenticator.ui.theme.IPGuardMistMuted
import com.ipguard.authenticator.ui.theme.IPGuardTeal

@Composable
fun FaceGateScreen(
    onBack: () -> Unit,
    onContinue: () -> Unit,
    modifier: Modifier = Modifier
) {
    val permission = rememberCameraPermissionState()
    var faceDetected by remember { mutableStateOf(false) }
    var cameraError by remember { mutableStateOf(false) }
    var cameraAttempt by remember { mutableIntStateOf(0) }
    val analyzer = remember {
        FacePresenceAnalyzer { detected ->
            if (detected) {
                faceDetected = true
            }
        }
    }

    DisposableEffect(Unit) {
        onDispose {
            analyzer.close()
        }
    }

    val cameraStatus = when {
        !permission.granted -> stringResource(R.string.face_presence_camera_waiting)
        cameraError -> stringResource(R.string.camera_status_unavailable)
        else -> stringResource(R.string.face_presence_camera_ready)
    }
    val faceStatus = if (faceDetected) {
        stringResource(R.string.face_presence_detected)
    } else {
        stringResource(R.string.face_presence_searching)
    }
    val overlayText = when {
        !permission.granted -> stringResource(R.string.face_overlay_permission)
        cameraError -> stringResource(R.string.face_overlay_error)
        faceDetected -> stringResource(R.string.face_overlay_detected)
        else -> stringResource(R.string.face_overlay_searching)
    }

    AuthenticatorScreen(
        eyebrow = stringResource(R.string.face_eyebrow),
        title = stringResource(R.string.face_title),
        subtitle = stringResource(R.string.face_subtitle),
        modifier = modifier,
        onBack = onBack
    ) {
        if (permission.granted && !cameraError) {
            key(cameraAttempt) {
                CameraStage(
                    badge = stringResource(R.string.face_camera_badge),
                    label = stringResource(R.string.face_camera_label),
                    monogram = "FACE",
                    accent = IPGuardTeal,
                    overlayText = overlayText,
                    cameraContent = {
                        CameraPreview(
                            lensFacing = CameraSelector.LENS_FACING_FRONT,
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
                badge = stringResource(R.string.face_camera_badge),
                label = stringResource(R.string.face_camera_label),
                placeholder = if (permission.granted) {
                    stringResource(R.string.face_overlay_error)
                } else {
                    stringResource(R.string.face_camera_placeholder)
                },
                hint = if (permission.granted) {
                    stringResource(R.string.camera_unavailable_notice)
                } else {
                    stringResource(R.string.face_camera_hint)
                },
                monogram = "FACE",
                accent = IPGuardTeal
            )
        }

        Spacer(Modifier.height(14.dp))
        InformationCard {
            SectionTitle(text = stringResource(R.string.face_presence_title))
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = stringResource(R.string.face_presence_camera_label),
                value = cameraStatus,
                valueColor = when {
                    cameraError -> IPGuardDanger
                    permission.granted -> IPGuardTeal
                    else -> IPGuardMistMuted
                }
            )
            KeyValueRow(
                label = stringResource(R.string.face_presence_label),
                value = faceStatus,
                valueColor = if (faceDetected) IPGuardTeal else IPGuardMistMuted,
                showDivider = false
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
                    color = IPGuardMistMuted
                )
            }
            Spacer(Modifier.height(14.dp))
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
            SectionTitle(text = stringResource(R.string.face_distinction_title))
            Spacer(Modifier.height(10.dp))
            Text(
                text = stringResource(R.string.face_distinction_body),
                style = MaterialTheme.typography.bodyMedium,
                color = IPGuardMistMuted
            )
        }

        Spacer(Modifier.height(14.dp))
        InformationCard {
            SectionTitle(text = stringResource(R.string.face_privacy_title))
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = stringResource(R.string.face_privacy_frames_label),
                value = stringResource(R.string.face_privacy_frames_value),
                valueColor = IPGuardTeal
            )
            KeyValueRow(
                label = stringResource(R.string.face_privacy_upload_label),
                value = stringResource(R.string.face_privacy_upload_value),
                valueColor = IPGuardTeal,
                showDivider = false
            )
        }

        Spacer(Modifier.height(14.dp))
        NoticeCard(
            text = stringResource(R.string.face_notice),
            tone = NoticeTone.WARNING
        )
        Spacer(Modifier.height(24.dp))

        when {
            !permission.granted -> {
                ScreenActions(
                    primaryLabel = stringResource(R.string.camera_permission_allow),
                    onPrimary = permission.requestPermission,
                    secondaryLabel = stringResource(R.string.camera_permission_settings),
                    onSecondary = permission.openAppSettings,
                    tertiaryLabel = stringResource(R.string.face_secondary_action),
                    onTertiary = onBack
                )
            }

            cameraError -> {
                ScreenActions(
                    primaryLabel = stringResource(R.string.camera_retry),
                    onPrimary = {
                        cameraError = false
                        faceDetected = false
                        cameraAttempt += 1
                    },
                    secondaryLabel = stringResource(R.string.face_secondary_action),
                    onSecondary = onBack
                )
            }

            else -> {
                ScreenActions(
                    primaryLabel = stringResource(R.string.face_primary_action),
                    onPrimary = onContinue,
                    primaryEnabled = faceDetected,
                    secondaryLabel = stringResource(R.string.face_secondary_action),
                    onSecondary = onBack
                )
            }
        }
    }
}
