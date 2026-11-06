package com.ipguard.authenticator.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.outlined.Info
import androidx.compose.material.icons.outlined.Warning
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.ipguard.authenticator.ui.theme.IPGuardDanger
import com.ipguard.authenticator.ui.theme.IPGuardGold
import com.ipguard.authenticator.ui.theme.IPGuardMist
import com.ipguard.authenticator.ui.theme.IPGuardMistMuted
import com.ipguard.authenticator.ui.theme.IPGuardNavy800
import com.ipguard.authenticator.ui.theme.IPGuardNavy900
import com.ipguard.authenticator.ui.theme.IPGuardNavy950
import com.ipguard.authenticator.ui.theme.IPGuardOutline
import com.ipguard.authenticator.ui.theme.IPGuardSuccess
import com.ipguard.authenticator.ui.theme.IPGuardTeal

enum class PillTone {
    TEAL,
    GOLD,
    MUTED,
    DANGER
}

@Composable
fun AppPill(
    text: String,
    modifier: Modifier = Modifier,
    tone: PillTone = PillTone.TEAL
) {
    val tint = when (tone) {
        PillTone.TEAL -> IPGuardTeal
        PillTone.GOLD -> IPGuardGold
        PillTone.MUTED -> IPGuardMistMuted
        PillTone.DANGER -> IPGuardDanger
    }
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(100),
        color = tint.copy(alpha = 0.1f),
        border = BorderStroke(1.dp, tint.copy(alpha = 0.3f))
    ) {
        Text(
            text = text,
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 7.dp),
            style = MaterialTheme.typography.labelSmall,
            color = tint,
            letterSpacing = 1.3.sp
        )
    }
}

@Composable
fun SectionTitle(
    text: String,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .size(6.dp)
                .background(IPGuardGold, CircleShape)
        )
        Spacer(Modifier.width(8.dp))
        Text(
            text = text,
            style = MaterialTheme.typography.labelSmall,
            color = IPGuardGold,
            letterSpacing = 1.6.sp
        )
    }
}

@Composable
fun InformationCard(
    modifier: Modifier = Modifier,
    content: @Composable ColumnScope.() -> Unit
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(24.dp),
        color = IPGuardNavy900.copy(alpha = 0.94f),
        border = BorderStroke(1.dp, Color.White.copy(alpha = 0.08f))
    ) {
        Column(
            modifier = Modifier.padding(20.dp),
            content = content
        )
    }
}

@Composable
fun KeyValueRow(
    label: String,
    value: String,
    modifier: Modifier = Modifier,
    valueColor: Color = IPGuardMist,
    showDivider: Boolean = true
) {
    Column(modifier = modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 11.dp),
            verticalAlignment = Alignment.Top
        ) {
            Text(
                text = label,
                modifier = Modifier.weight(1f),
                style = MaterialTheme.typography.labelMedium,
                color = IPGuardMistMuted
            )
            Spacer(Modifier.width(14.dp))
            Text(
                text = value,
                modifier = Modifier.weight(1.15f),
                style = MaterialTheme.typography.bodyMedium,
                color = valueColor,
                textAlign = TextAlign.End
            )
        }
        if (showDivider) {
            HorizontalDivider(color = IPGuardOutline.copy(alpha = 0.5f))
        }
    }
}

@Composable
fun CardDivider(modifier: Modifier = Modifier) {
    HorizontalDivider(
        modifier = modifier,
        color = IPGuardOutline.copy(alpha = 0.5f)
    )
}

@Composable
fun PrincipleRow(
    marker: String,
    text: String,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        verticalAlignment = Alignment.Top
    ) {
        Surface(
            modifier = Modifier.size(28.dp),
            shape = CircleShape,
            color = IPGuardGold.copy(alpha = 0.1f),
            border = BorderStroke(1.dp, IPGuardGold.copy(alpha = 0.28f))
        ) {
            Box(contentAlignment = Alignment.Center) {
                Text(
                    text = marker,
                    style = MaterialTheme.typography.labelSmall,
                    color = IPGuardGold,
                    fontSize = 9.sp
                )
            }
        }
        Spacer(Modifier.width(12.dp))
        Text(
            text = text,
            modifier = Modifier
                .weight(1f)
                .padding(top = 3.dp),
            style = MaterialTheme.typography.bodyMedium,
            color = IPGuardMist
        )
    }
}

enum class NoticeTone {
    INFO,
    WARNING
}

@Composable
fun NoticeCard(
    text: String,
    modifier: Modifier = Modifier,
    tone: NoticeTone = NoticeTone.INFO
) {
    val tint = if (tone == NoticeTone.WARNING) IPGuardGold else IPGuardMistMuted
    val icon = if (tone == NoticeTone.WARNING) {
        Icons.Outlined.Warning
    } else {
        Icons.Outlined.Info
    }
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(18.dp),
        color = tint.copy(alpha = 0.07f),
        border = BorderStroke(1.dp, tint.copy(alpha = 0.22f))
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.Top
        ) {
            Box(
                modifier = Modifier
                    .size(28.dp)
                    .background(tint.copy(alpha = 0.12f), CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    modifier = Modifier.size(16.dp),
                    tint = tint
                )
            }
            Spacer(Modifier.width(12.dp))
            Text(
                text = text,
                modifier = Modifier.weight(1f),
                style = MaterialTheme.typography.bodySmall,
                color = if (tone == NoticeTone.WARNING) IPGuardMist else IPGuardMistMuted
            )
        }
    }
}

@Composable
fun MonogramSeal(
    label: String,
    modifier: Modifier = Modifier,
    accent: Color = IPGuardTeal,
    size: Dp = 84.dp
) {
    Surface(
        modifier = modifier.size(size),
        shape = CircleShape,
        color = accent.copy(alpha = 0.12f),
        border = BorderStroke(1.dp, accent.copy(alpha = 0.42f))
    ) {
        Box(contentAlignment = Alignment.Center) {
            Text(
                text = label,
                style = MaterialTheme.typography.labelLarge,
                color = accent,
                fontWeight = FontWeight.Bold,
                letterSpacing = 2.sp
            )
        }
    }
}

@Composable
fun CameraStage(
    badge: String,
    label: String,
    monogram: String,
    accent: Color,
    modifier: Modifier = Modifier,
    placeholder: String? = null,
    hint: String? = null,
    overlayText: String? = null,
    cameraContent: (@Composable BoxScope.() -> Unit)? = null
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(28.dp),
        color = IPGuardNavy950.copy(alpha = 0.76f),
        border = BorderStroke(1.dp, IPGuardOutline.copy(alpha = 0.8f))
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(252.dp)
        ) {
            cameraContent?.invoke(this)

            Canvas(modifier = Modifier.matchParentSize()) {
                val gridColor = Color.White.copy(alpha = 0.035f)
                val gridStroke = 1.dp.toPx()
                drawLine(
                    color = gridColor,
                    start = Offset(size.width / 3f, 0f),
                    end = Offset(size.width / 3f, size.height),
                    strokeWidth = gridStroke
                )
                drawLine(
                    color = gridColor,
                    start = Offset(size.width * 2f / 3f, 0f),
                    end = Offset(size.width * 2f / 3f, size.height),
                    strokeWidth = gridStroke
                )
                drawLine(
                    color = gridColor,
                    start = Offset(0f, size.height / 3f),
                    end = Offset(size.width, size.height / 3f),
                    strokeWidth = gridStroke
                )
                drawLine(
                    color = gridColor,
                    start = Offset(0f, size.height * 2f / 3f),
                    end = Offset(size.width, size.height * 2f / 3f),
                    strokeWidth = gridStroke
                )

                val frameInset = 18.dp.toPx()
                val cornerLength = 26.dp.toPx()
                val cornerColor = accent.copy(alpha = 0.62f)
                val cornerStroke = 1.5.dp.toPx()
                drawLine(
                    color = cornerColor,
                    start = Offset(frameInset, frameInset),
                    end = Offset(frameInset + cornerLength, frameInset),
                    strokeWidth = cornerStroke
                )
                drawLine(
                    color = cornerColor,
                    start = Offset(frameInset, frameInset),
                    end = Offset(frameInset, frameInset + cornerLength),
                    strokeWidth = cornerStroke
                )
                drawLine(
                    color = cornerColor,
                    start = Offset(size.width - frameInset, frameInset),
                    end = Offset(size.width - frameInset - cornerLength, frameInset),
                    strokeWidth = cornerStroke
                )
                drawLine(
                    color = cornerColor,
                    start = Offset(size.width - frameInset, frameInset),
                    end = Offset(size.width - frameInset, frameInset + cornerLength),
                    strokeWidth = cornerStroke
                )
                drawLine(
                    color = cornerColor,
                    start = Offset(frameInset, size.height - frameInset),
                    end = Offset(frameInset + cornerLength, size.height - frameInset),
                    strokeWidth = cornerStroke
                )
                drawLine(
                    color = cornerColor,
                    start = Offset(frameInset, size.height - frameInset),
                    end = Offset(frameInset, size.height - frameInset - cornerLength),
                    strokeWidth = cornerStroke
                )
                drawLine(
                    color = cornerColor,
                    start = Offset(size.width - frameInset, size.height - frameInset),
                    end = Offset(size.width - frameInset - cornerLength, size.height - frameInset),
                    strokeWidth = cornerStroke
                )
                drawLine(
                    color = cornerColor,
                    start = Offset(size.width - frameInset, size.height - frameInset),
                    end = Offset(size.width - frameInset, size.height - frameInset - cornerLength),
                    strokeWidth = cornerStroke
                )
            }

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Color.Black.copy(alpha = 0.32f))
                    .padding(horizontal = 26.dp, vertical = 16.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                AppPill(text = badge, tone = PillTone.GOLD)
                Text(
                    text = label,
                    style = MaterialTheme.typography.labelSmall,
                    color = IPGuardMistMuted,
                    letterSpacing = 1.4.sp
                )
            }

            if (cameraContent == null) {
                Column(
                    modifier = Modifier
                        .align(Alignment.Center)
                        .padding(horizontal = 24.dp, vertical = 24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    MonogramSeal(
                        label = monogram,
                        accent = accent,
                        size = 76.dp
                    )
                    if (placeholder != null) {
                        Spacer(Modifier.height(16.dp))
                        Text(
                            text = placeholder,
                            style = MaterialTheme.typography.titleMedium,
                            color = IPGuardMist,
                            textAlign = TextAlign.Center
                        )
                    }
                    if (hint != null) {
                        Spacer(Modifier.height(6.dp))
                        Text(
                            text = hint,
                            style = MaterialTheme.typography.bodySmall,
                            color = IPGuardMistMuted,
                            textAlign = TextAlign.Center
                        )
                    }
                }
            }

            if (overlayText != null) {
                Surface(
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .padding(24.dp),
                    shape = RoundedCornerShape(100),
                    color = IPGuardNavy950.copy(alpha = 0.82f),
                    border = BorderStroke(1.dp, IPGuardOutline.copy(alpha = 0.8f))
                ) {
                    Text(
                        text = overlayText,
                        modifier = Modifier.padding(horizontal = 16.dp, vertical = 9.dp),
                        style = MaterialTheme.typography.bodySmall,
                        color = IPGuardMist,
                        textAlign = TextAlign.Center
                    )
                }
            }
        }
    }
}

@Composable
fun OutcomeSeal(
    positive: Boolean,
    modifier: Modifier = Modifier
) {
    val tint = if (positive) IPGuardSuccess else IPGuardDanger
    Surface(
        modifier = modifier.size(104.dp),
        shape = CircleShape,
        color = tint.copy(alpha = 0.1f),
        border = BorderStroke(1.dp, tint.copy(alpha = 0.36f))
    ) {
        Box(contentAlignment = Alignment.Center) {
            Icon(
                imageVector = if (positive) Icons.Filled.Check else Icons.Filled.Close,
                contentDescription = null,
                modifier = Modifier.size(46.dp),
                tint = tint
            )
        }
    }
}
