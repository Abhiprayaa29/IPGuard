package com.ipguard.authenticator.ui.components

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.ipguard.authenticator.ui.state.BackendConnectionState
import com.ipguard.authenticator.ui.state.BackendConnectionStatus
import com.ipguard.authenticator.ui.theme.IPGuardDanger
import com.ipguard.authenticator.ui.theme.IPGuardGold
import com.ipguard.authenticator.ui.theme.IPGuardGoldBright
import com.ipguard.authenticator.ui.theme.IPGuardHairline
import com.ipguard.authenticator.ui.theme.IPGuardObsidian
import com.ipguard.authenticator.ui.theme.IPGuardPlatinum
import com.ipguard.authenticator.ui.theme.IPGuardSlate
import com.ipguard.authenticator.ui.theme.IPGuardSurface
import com.ipguard.authenticator.ui.theme.IPGuardSurfaceElevated
import com.ipguard.authenticator.ui.theme.IPGuardVerified

enum class StepStatus {
    COMPLETED,
    ACTIVE,
    PENDING,
    FAILED
}

data class AuthPipelineStep(
    val stepCode: String,
    val title: String,
    val detail: String,
    val status: StepStatus
)

@Composable
fun AuthPipelineStepper(
    steps: List<AuthPipelineStep>,
    modifier: Modifier = Modifier
) {
    val completedCount = steps.count { it.status == StepStatus.COMPLETED }
    val hasActive = steps.any { it.status == StepStatus.ACTIVE }
    val targetProgress = if (steps.isEmpty()) 0f else {
        ((completedCount + if (hasActive) 0.5f else 0f) / steps.size.toFloat()).coerceIn(0f, 1f)
    }
    val animatedProgress by animateFloatAsState(
        targetValue = targetProgress,
        animationSpec = tween(durationMillis = 320),
        label = "authPipelineProgress"
    )

    InformationCard(modifier = modifier) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            SectionTitle(text = "AUTHENTICATION PIPELINE")
            Text(
                text = "${completedCount}/${steps.size}",
                style = MaterialTheme.typography.labelSmall,
                color = IPGuardGoldBright,
                fontFamily = FontFamily.Monospace
            )
        }
        Spacer(Modifier.height(10.dp))
        LinearProgressIndicator(
            progress = { animatedProgress },
            modifier = Modifier
                .fillMaxWidth()
                .height(4.dp)
                .clip(RoundedCornerShape(100)),
            color = IPGuardGold,
            trackColor = IPGuardSurfaceElevated
        )
        Spacer(Modifier.height(14.dp))
        steps.forEachIndexed { index, step ->
            val accent by animateColorAsState(
                targetValue = when (step.status) {
                    StepStatus.COMPLETED -> IPGuardVerified
                    StepStatus.ACTIVE -> IPGuardGoldBright
                    StepStatus.FAILED -> IPGuardDanger
                    StepStatus.PENDING -> IPGuardSlate
                },
                animationSpec = tween(250),
                label = "stepColor_$index"
            )
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 6.dp),
                verticalAlignment = Alignment.Top
            ) {
                Surface(
                    modifier = Modifier.size(26.dp),
                    shape = CircleShape,
                    color = accent.copy(alpha = if (step.status == StepStatus.PENDING) 0.08f else 0.16f),
                    border = BorderStroke(1.dp, accent.copy(alpha = 0.45f))
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        when (step.status) {
                            StepStatus.COMPLETED -> Icon(
                                imageVector = Icons.Filled.Check,
                                contentDescription = "Completed",
                                tint = accent,
                                modifier = Modifier.size(14.dp)
                            )
                            StepStatus.FAILED -> Icon(
                                imageVector = Icons.Filled.Close,
                                contentDescription = "Failed",
                                tint = accent,
                                modifier = Modifier.size(14.dp)
                            )
                            else -> Text(
                                text = (index + 1).toString().padStart(2, '0'),
                                style = MaterialTheme.typography.labelSmall,
                                color = accent,
                                fontFamily = FontFamily.Monospace,
                                fontSize = 9.sp
                            )
                        }
                    }
                }
                Spacer(Modifier.width(12.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = step.stepCode,
                            style = MaterialTheme.typography.labelSmall,
                            color = accent,
                            fontFamily = FontFamily.Monospace,
                            fontSize = 10.sp
                        )
                        Text(
                            text = when (step.status) {
                                StepStatus.COMPLETED -> "DONE"
                                StepStatus.ACTIVE -> "IN PROGRESS"
                                StepStatus.FAILED -> "ATTENTION"
                                StepStatus.PENDING -> "QUEUED"
                            },
                            style = MaterialTheme.typography.labelSmall,
                            color = accent,
                            fontSize = 9.sp
                        )
                    }
                    Spacer(Modifier.height(2.dp))
                    Text(
                        text = step.title,
                        style = MaterialTheme.typography.labelLarge,
                        color = if (step.status == StepStatus.PENDING) IPGuardSlate else IPGuardPlatinum
                    )
                    Text(
                        text = step.detail,
                        style = MaterialTheme.typography.bodySmall,
                        color = IPGuardSlate
                    )
                }
            }
        }
    }
}

@Composable
fun ConnectionBadge(
    connectionState: BackendConnectionState,
    modifier: Modifier = Modifier
) {
    val tint = when (connectionState.status) {
        BackendConnectionStatus.CONNECTED -> IPGuardVerified
        BackendConnectionStatus.CHECKING -> IPGuardGoldBright
        BackendConnectionStatus.UNAVAILABLE -> IPGuardDanger
    }
    val text = when (connectionState.status) {
        BackendConnectionStatus.CONNECTED -> "ONLINE"
        BackendConnectionStatus.CHECKING -> "SYNCING"
        BackendConnectionStatus.UNAVAILABLE -> "OFFLINE"
    }
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(100),
        color = IPGuardSurfaceElevated,
        border = BorderStroke(1.dp, tint.copy(alpha = 0.4f))
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 5.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(7.dp)
                    .background(tint, CircleShape)
            )
            Spacer(Modifier.width(6.dp))
            Text(
                text = text,
                style = MaterialTheme.typography.labelSmall,
                color = tint,
                fontSize = 9.sp,
                letterSpacing = 1.sp
            )
        }
    }
}

@Composable
fun DashboardActionTile(
    title: String,
    subtitle: String,
    tag: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    icon: ImageVector = Icons.Filled.Lock,
    accent: Color = IPGuardGoldBright
) {
    Surface(
        onClick = onClick,
        modifier = modifier
            .fillMaxWidth()
            .heightIn(min = 68.dp),
        shape = RoundedCornerShape(16.dp),
        color = IPGuardSurface,
        border = BorderStroke(1.dp, IPGuardHairline)
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Surface(
                modifier = Modifier.size(40.dp),
                shape = RoundedCornerShape(12.dp),
                color = accent.copy(alpha = 0.12f),
                border = BorderStroke(1.dp, accent.copy(alpha = 0.3f))
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Icon(
                        imageVector = icon,
                        contentDescription = title,
                        tint = accent,
                        modifier = Modifier.size(20.dp)
                    )
                }
            }
            Spacer(Modifier.width(14.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = tag,
                    style = MaterialTheme.typography.labelSmall,
                    color = accent,
                    fontSize = 9.sp,
                    letterSpacing = 1.1.sp
                )
                Spacer(Modifier.height(2.dp))
                Text(
                    text = title,
                    style = MaterialTheme.typography.titleMedium,
                    color = IPGuardPlatinum,
                    fontWeight = FontWeight.SemiBold
                )
                Text(
                    text = subtitle,
                    style = MaterialTheme.typography.bodySmall,
                    color = IPGuardSlate
                )
            }
            Spacer(Modifier.width(8.dp))
            Icon(
                imageVector = Icons.AutoMirrored.Filled.KeyboardArrowRight,
                contentDescription = "Open $title",
                tint = IPGuardSlate,
                modifier = Modifier.size(20.dp)
            )
        }
    }
}
