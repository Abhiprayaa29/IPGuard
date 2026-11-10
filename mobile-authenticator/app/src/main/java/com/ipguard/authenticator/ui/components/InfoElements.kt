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
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
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

enum class PillTone {
    TEAL, // Kept for backward compatibility; renders Emerald Verified or Gold accent cleanly
    VERIFIED,
    GOLD,
    MUTED,
    DANGER
}

@Composable
fun AppPill(
    text: String,
    modifier: Modifier = Modifier,
    tone: PillTone = PillTone.GOLD
) {
    val tint = when (tone) {
        PillTone.TEAL, PillTone.VERIFIED -> IPGuardVerified
        PillTone.GOLD -> IPGuardGoldBright
        PillTone.MUTED -> IPGuardSlate
        PillTone.DANGER -> IPGuardDanger
    }
    Surface(
        modifier = modifier.semantics { contentDescription = text },
        shape = RoundedCornerShape(100),
        color = tint.copy(alpha = 0.10f),
        border = BorderStroke(1.dp, tint.copy(alpha = 0.34f))
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(6.dp)
                    .background(tint, CircleShape)
            )
            Spacer(Modifier.width(7.dp))
            Text(
                text = text,
                style = MaterialTheme.typography.labelSmall,
                color = tint,
                letterSpacing = 1.1.sp
            )
        }
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
                .width(12.dp)
                .height(2.dp)
                .background(IPGuardGold, RoundedCornerShape(1.dp))
        )
        Spacer(Modifier.width(8.dp))
        Text(
            text = text,
            style = MaterialTheme.typography.labelSmall,
            color = IPGuardGoldBright,
            letterSpacing = 1.5.sp
        )
    }
}

@Composable
fun InformationCard(
    modifier: Modifier = Modifier,
    borderColor: Color = IPGuardHairline,
    containerColor: Color = IPGuardSurface,
    content: @Composable ColumnScope.() -> Unit
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(18.dp),
        color = containerColor,
        border = BorderStroke(1.dp, borderColor)
    ) {
        Column(
            modifier = Modifier.padding(18.dp),
            content = content
        )
    }
}

@Composable
fun KeyValueRow(
    label: String,
    value: String,
    modifier: Modifier = Modifier,
    valueColor: Color = IPGuardPlatinum,
    monospaceValue: Boolean = false,
    showDivider: Boolean = true
) {
    Column(modifier = modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 10.dp),
            verticalAlignment = Alignment.Top
        ) {
            Text(
                text = label,
                modifier = Modifier.weight(0.95f),
                style = MaterialTheme.typography.labelMedium,
                color = IPGuardSlate
            )
            Spacer(Modifier.width(12.dp))
            Text(
                text = value,
                modifier = Modifier.weight(1.25f),
                style = MaterialTheme.typography.bodyMedium.copy(
                    fontFamily = if (monospaceValue) FontFamily.Monospace else FontFamily.SansSerif
                ),
                color = valueColor,
                textAlign = TextAlign.End
            )
        }
        if (showDivider) {
            HorizontalDivider(color = IPGuardHairline.copy(alpha = 0.7f))
        }
    }
}

@Composable
fun CardDivider(modifier: Modifier = Modifier) {
    HorizontalDivider(
        modifier = modifier,
        color = IPGuardHairline.copy(alpha = 0.75f)
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
            shape = RoundedCornerShape(8.dp),
            color = IPGuardGold.copy(alpha = 0.12f),
            border = BorderStroke(1.dp, IPGuardGold.copy(alpha = 0.32f))
        ) {
            Box(contentAlignment = Alignment.Center) {
                Text(
                    text = marker,
                    style = MaterialTheme.typography.labelSmall,
                    color = IPGuardGoldBright,
                    fontFamily = FontFamily.Monospace,
                    fontSize = 10.sp
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
            color = IPGuardPlatinum
        )
    }
}

enum class NoticeTone {
    INFO,
    WARNING,
    SUCCESS,
    DANGER
}

@Composable
fun NoticeCard(
    text: String,
    modifier: Modifier = Modifier,
    tone: NoticeTone = NoticeTone.INFO
) {
    val tint = when (tone) {
        NoticeTone.INFO -> IPGuardSlate
        NoticeTone.WARNING -> IPGuardGoldBright
        NoticeTone.SUCCESS -> IPGuardVerified
        NoticeTone.DANGER -> IPGuardDanger
    }
    val icon = when (tone) {
        NoticeTone.INFO -> Icons.Outlined.Info
        NoticeTone.WARNING -> Icons.Outlined.Warning
        NoticeTone.SUCCESS -> Icons.Filled.Check
        NoticeTone.DANGER -> Icons.Filled.Close
    }
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(14.dp),
        color = tint.copy(alpha = 0.08f),
        border = BorderStroke(1.dp, tint.copy(alpha = 0.25f))
    ) {
        Row(
            modifier = Modifier.padding(14.dp),
            verticalAlignment = Alignment.Top
        ) {
            Box(
                modifier = Modifier
                    .size(26.dp)
                    .background(tint.copy(alpha = 0.14f), CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = icon,
                    contentDescription = tone.name,
                    modifier = Modifier.size(15.dp),
                    tint = tint
                )
            }
            Spacer(Modifier.width(12.dp))
            Text(
                text = text,
                modifier = Modifier.weight(1f),
                style = MaterialTheme.typography.bodySmall,
                color = if (tone == NoticeTone.INFO) IPGuardSlate else IPGuardPlatinum
            )
        }
    }
}

@Composable
fun MonogramSeal(
    label: String,
    modifier: Modifier = Modifier,
    accent: Color = IPGuardGoldBright,
    size: Dp = 80.dp
) {
    Surface(
        modifier = modifier.size(size),
        shape = CircleShape,
        color = accent.copy(alpha = 0.10f),
        border = BorderStroke(1.dp, accent.copy(alpha = 0.42f))
    ) {
        Box(contentAlignment = Alignment.Center) {
            Text(
                text = label,
                style = MaterialTheme.typography.labelLarge,
                color = accent,
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.8.sp
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
        shape = RoundedCornerShape(22.dp),
        color = IPGuardObsidian,
        border = BorderStroke(1.dp, IPGuardHairline)
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(256.dp)
        ) {
            cameraContent?.invoke(this)

            Canvas(modifier = Modifier.matchParentSize()) {
                val frameInset = 18.dp.toPx()
                val cornerLength = 26.dp.toPx()
                val cornerColor = accent.copy(alpha = 0.78f)
                val cornerStroke = 2.dp.toPx()
                drawLine(cornerColor, Offset(frameInset, frameInset), Offset(frameInset + cornerLength, frameInset), cornerStroke)
                drawLine(cornerColor, Offset(frameInset, frameInset), Offset(frameInset, frameInset + cornerLength), cornerStroke)
                drawLine(cornerColor, Offset(size.width - frameInset, frameInset), Offset(size.width - frameInset - cornerLength, frameInset), cornerStroke)
                drawLine(cornerColor, Offset(size.width - frameInset, frameInset), Offset(size.width - frameInset, frameInset + cornerLength), cornerStroke)
                drawLine(cornerColor, Offset(frameInset, size.height - frameInset), Offset(frameInset + cornerLength, size.height - frameInset), cornerStroke)
                drawLine(cornerColor, Offset(frameInset, size.height - frameInset), Offset(frameInset, size.height - frameInset - cornerLength), cornerStroke)
                drawLine(cornerColor, Offset(size.width - frameInset, size.height - frameInset), Offset(size.width - frameInset - cornerLength, size.height - frameInset), cornerStroke)
                drawLine(cornerColor, Offset(size.width - frameInset, size.height - frameInset), Offset(size.width - frameInset, size.height - frameInset - cornerLength), cornerStroke)
            }

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Color.Black.copy(alpha = 0.48f))
                    .padding(horizontal = 24.dp, vertical = 14.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                AppPill(text = badge, tone = PillTone.GOLD)
                Text(
                    text = label,
                    style = MaterialTheme.typography.labelSmall,
                    color = IPGuardPlatinum,
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
                        size = 72.dp
                    )
                    if (placeholder != null) {
                        Spacer(Modifier.height(14.dp))
                        Text(
                            text = placeholder,
                            style = MaterialTheme.typography.titleMedium,
                            color = IPGuardPlatinum,
                            textAlign = TextAlign.Center
                        )
                    }
                    if (hint != null) {
                        Spacer(Modifier.height(6.dp))
                        Text(
                            text = hint,
                            style = MaterialTheme.typography.bodySmall,
                            color = IPGuardSlate,
                            textAlign = TextAlign.Center
                        )
                    }
                }
            }

            if (overlayText != null) {
                Surface(
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .padding(20.dp),
                    shape = RoundedCornerShape(100),
                    color = IPGuardObsidian.copy(alpha = 0.88f),
                    border = BorderStroke(1.dp, IPGuardHairline)
                ) {
                    Text(
                        text = overlayText,
                        modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
                        style = MaterialTheme.typography.bodySmall,
                        color = IPGuardPlatinum,
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
    val tint = if (positive) IPGuardVerified else IPGuardDanger
    Surface(
        modifier = modifier.size(96.dp),
        shape = CircleShape,
        color = tint.copy(alpha = 0.12f),
        border = BorderStroke(1.5.dp, tint.copy(alpha = 0.45f))
    ) {
        Box(contentAlignment = Alignment.Center) {
            Icon(
                imageVector = if (positive) Icons.Filled.Check else Icons.Filled.Close,
                contentDescription = if (positive) "Verified" else "Rejected or failed",
                modifier = Modifier.size(44.dp),
                tint = tint
            )
        }
    }
}
