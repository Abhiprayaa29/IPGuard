package com.ipguard.authenticator.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
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
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.ipguard.authenticator.R
import com.ipguard.authenticator.ui.theme.IPGuardGold
import com.ipguard.authenticator.ui.theme.IPGuardMist
import com.ipguard.authenticator.ui.theme.IPGuardMistMuted
import com.ipguard.authenticator.ui.theme.IPGuardNavy800
import com.ipguard.authenticator.ui.theme.IPGuardNavy900
import com.ipguard.authenticator.ui.theme.IPGuardNavy950
import com.ipguard.authenticator.ui.theme.IPGuardOutline
import com.ipguard.authenticator.ui.theme.IPGuardTeal

@Composable
fun AuthenticatorScreen(
    eyebrow: String,
    title: String,
    subtitle: String,
    modifier: Modifier = Modifier,
    onBack: (() -> Unit)? = null,
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
                modifier = Modifier.padding(horizontal = 24.dp, vertical = 16.dp)
            )
            Column(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth()
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 24.dp)
                    .padding(bottom = 32.dp)
            ) {
                Spacer(Modifier.height(8.dp))
                Text(
                    text = eyebrow,
                    style = MaterialTheme.typography.labelSmall,
                    color = IPGuardTeal,
                    letterSpacing = 1.8.sp
                )
                Spacer(Modifier.height(10.dp))
                Text(
                    text = title,
                    style = MaterialTheme.typography.displaySmall,
                    color = IPGuardMist
                )
                Spacer(Modifier.height(10.dp))
                Text(
                    text = subtitle,
                    style = MaterialTheme.typography.bodyLarge,
                    color = IPGuardMistMuted
                )
                Spacer(Modifier.height(28.dp))
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
                    listOf(IPGuardNavy950, IPGuardNavy900, IPGuardNavy950)
                )
            )
    ) {
        Box(
            modifier = Modifier
                .align(Alignment.TopEnd)
                .offset(x = 110.dp, y = (-130).dp)
                .size(280.dp)
                .background(
                    Brush.radialGradient(
                        listOf(IPGuardTeal.copy(alpha = 0.13f), Color.Transparent)
                    ),
                    CircleShape
                )
        )
        Box(
            modifier = Modifier
                .align(Alignment.BottomStart)
                .offset(x = (-120).dp, y = 140.dp)
                .size(300.dp)
                .background(
                    Brush.radialGradient(
                        listOf(IPGuardGold.copy(alpha = 0.08f), Color.Transparent)
                    ),
                    CircleShape
                )
        )
    }
}

@Composable
private fun AppTopBar(
    onBack: (() -> Unit)?,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically
    ) {
        if (onBack != null) {
            Surface(
                onClick = onBack,
                modifier = Modifier.size(40.dp),
                shape = CircleShape,
                color = IPGuardNavy800.copy(alpha = 0.72f),
                contentColor = IPGuardMist,
                border = BorderStroke(1.dp, IPGuardOutline.copy(alpha = 0.8f))
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
        PlatformPill()
    }
}

@Composable
private fun BrandWordmark() {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Surface(
            shape = RoundedCornerShape(14.dp),
            color = IPGuardTeal.copy(alpha = 0.12f),
            border = BorderStroke(1.dp, IPGuardTeal.copy(alpha = 0.36f))
        ) {
            Box(
                modifier = Modifier.size(40.dp),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = stringResource(R.string.brand_mark),
                    color = IPGuardTeal,
                    style = MaterialTheme.typography.labelLarge,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
            }
        }
        Spacer(Modifier.width(10.dp))
        Column {
            Text(
                text = stringResource(R.string.brand_name),
                style = MaterialTheme.typography.labelLarge,
                color = IPGuardMist,
                letterSpacing = 2.sp
            )
            Text(
                text = stringResource(R.string.brand_product),
                style = MaterialTheme.typography.labelSmall,
                color = IPGuardMistMuted,
                fontSize = 9.sp,
                letterSpacing = 1.8.sp
            )
        }
    }
}

@Composable
private fun PlatformPill() {
    Surface(
        shape = RoundedCornerShape(100),
        color = Color.Transparent,
        border = BorderStroke(1.dp, IPGuardGold.copy(alpha = 0.5f))
    ) {
        Text(
            text = stringResource(R.string.platform_badge),
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
            style = MaterialTheme.typography.labelSmall,
            color = IPGuardGold,
            fontSize = 9.sp,
            letterSpacing = 1.3.sp
        )
    }
}
