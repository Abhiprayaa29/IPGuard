package com.ipguard.authenticator.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.systemBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.ipguard.authenticator.R
import com.ipguard.authenticator.ui.theme.IPGuardCharcoal
import com.ipguard.authenticator.ui.theme.IPGuardGold
import com.ipguard.authenticator.ui.theme.IPGuardGoldBright
import com.ipguard.authenticator.ui.theme.IPGuardHairline
import com.ipguard.authenticator.ui.theme.IPGuardObsidian
import com.ipguard.authenticator.ui.theme.IPGuardPlatinum
import com.ipguard.authenticator.ui.theme.IPGuardSlate
import com.ipguard.authenticator.ui.theme.IPGuardSurfaceElevated

@Composable
fun AuthenticatorScreen(
    eyebrow: String,
    title: String,
    subtitle: String,
    modifier: Modifier = Modifier,
    onBack: (() -> Unit)? = null,
    headerTrailing: (@Composable () -> Unit)? = null,
    content: @Composable ColumnScope.() -> Unit
) {
    Box(modifier = modifier.fillMaxSize()) {
        AppBackground()
        Column(
            modifier = Modifier
                .fillMaxSize()
                .systemBarsPadding()
        ) {
            AppTopBar(
                onBack = onBack,
                headerTrailing = headerTrailing,
                modifier = Modifier.padding(horizontal = 20.dp, vertical = 14.dp)
            )
            Column(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth()
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 20.dp)
                    .padding(bottom = 32.dp)
            ) {
                Spacer(Modifier.height(4.dp))
                Text(
                    text = eyebrow,
                    style = MaterialTheme.typography.labelSmall,
                    color = IPGuardGoldBright,
                    letterSpacing = 1.6.sp
                )
                Spacer(Modifier.height(8.dp))
                Text(
                    text = title,
                    modifier = Modifier.semantics { heading() },
                    style = MaterialTheme.typography.displaySmall,
                    color = IPGuardPlatinum
                )
                Spacer(Modifier.height(8.dp))
                Text(
                    text = subtitle,
                    style = MaterialTheme.typography.bodyLarge,
                    color = IPGuardSlate
                )
                Spacer(Modifier.height(24.dp))
                content()
            }
        }
    }
}

@Composable
private fun AppBackground() {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.verticalGradient(
                    listOf(IPGuardObsidian, IPGuardCharcoal, IPGuardObsidian)
                )
            )
    ) {
        // Subtle radial ambient gold glint at top-right corner
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(240.dp)
                .background(
                    Brush.radialGradient(
                        colors = listOf(IPGuardGold.copy(alpha = 0.06f), Color.Transparent),
                        center = Offset(720f, 0f),
                        radius = 700f
                    )
                )
        )
    }
}

@Composable
private fun AppTopBar(
    onBack: (() -> Unit)?,
    headerTrailing: (@Composable () -> Unit)?,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically
    ) {
        if (onBack != null) {
            Surface(
                onClick = onBack,
                modifier = Modifier.size(44.dp),
                shape = CircleShape,
                color = IPGuardSurfaceElevated,
                contentColor = IPGuardPlatinum,
                border = BorderStroke(1.dp, IPGuardHairline)
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                        contentDescription = stringResource(R.string.action_back),
                        modifier = Modifier.size(18.dp)
                    )
                }
            }
            Spacer(Modifier.width(12.dp))
        }
        BrandWordmark()
        Spacer(Modifier.weight(1f))
        if (headerTrailing != null) {
            headerTrailing()
        } else {
            PlatformPill()
        }
    }
}

@Composable
private fun BrandWordmark() {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Surface(
            shape = RoundedCornerShape(12.dp),
            color = IPGuardGold.copy(alpha = 0.1f),
            border = BorderStroke(1.dp, IPGuardGold.copy(alpha = 0.4f))
        ) {
            Box(
                modifier = Modifier.size(38.dp),
                contentAlignment = Alignment.Center
            ) {
                ShieldCrestIcon(
                    tint = IPGuardGoldBright,
                    modifier = Modifier.size(20.dp)
                )
            }
        }
        Spacer(Modifier.width(10.dp))
        Column {
            Text(
                text = stringResource(R.string.brand_name),
                style = MaterialTheme.typography.labelLarge,
                color = IPGuardPlatinum,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.8.sp
            )
            Text(
                text = stringResource(R.string.brand_product),
                style = MaterialTheme.typography.labelSmall,
                color = IPGuardGoldMutedText(),
                fontSize = 9.sp,
                letterSpacing = 1.6.sp
            )
        }
    }
}

@Composable
private fun IPGuardGoldMutedText(): Color = IPGuardGold.copy(alpha = 0.85f)

@Composable
private fun PlatformPill() {
    Surface(
        shape = RoundedCornerShape(100),
        color = IPGuardSurfaceElevated,
        border = BorderStroke(1.dp, IPGuardGold.copy(alpha = 0.36f))
    ) {
        Text(
            text = stringResource(R.string.platform_badge),
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 5.dp),
            style = MaterialTheme.typography.labelSmall,
            color = IPGuardGoldBright,
            fontSize = 9.sp,
            letterSpacing = 1.2.sp
        )
    }
}

@Composable
fun ShieldCrestIcon(
    tint: Color,
    modifier: Modifier = Modifier
) {
    Canvas(modifier = modifier) {
        val w = size.width
        val h = size.height
        val shield = Path().apply {
            moveTo(w * 0.50f, h * 0.08f)
            lineTo(w * 0.86f, h * 0.22f)
            lineTo(w * 0.86f, h * 0.50f)
            cubicTo(
                w * 0.86f, h * 0.72f,
                w * 0.68f, h * 0.86f,
                w * 0.50f, h * 0.94f
            )
            cubicTo(
                w * 0.32f, h * 0.86f,
                w * 0.14f, h * 0.72f,
                w * 0.14f, h * 0.50f
            )
            lineTo(w * 0.14f, h * 0.22f)
            close()
        }
        drawPath(
            path = shield,
            color = tint,
            style = Stroke(width = 1.8.dp.toPx(), cap = StrokeCap.Round, join = StrokeJoin.Round)
        )
        drawCircle(
            color = tint,
            radius = w * 0.11f,
            center = Offset(w * 0.50f, h * 0.47f),
            style = Stroke(width = 1.6.dp.toPx())
        )
        drawLine(
            color = tint,
            start = Offset(w * 0.50f, h * 0.58f),
            end = Offset(w * 0.50f, h * 0.71f),
            strokeWidth = 1.6.dp.toPx(),
            cap = StrokeCap.Round
        )
    }
}
