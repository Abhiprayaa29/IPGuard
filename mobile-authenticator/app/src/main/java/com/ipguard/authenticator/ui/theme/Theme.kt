package com.ipguard.authenticator.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

// Obsidian & Charcoal cybersecurity surface hierarchy
val IPGuardObsidian = Color(0xFF090A0D)
val IPGuardCharcoal = Color(0xFF101217)
val IPGuardSurface = Color(0xFF151820)
val IPGuardSurfaceElevated = Color(0xFF1C202B)
val IPGuardHairline = Color(0xFF262B38)

// Metallic Gold primary accent spectrum
val IPGuardGold = Color(0xFFD4AF37)
val IPGuardGoldBright = Color(0xFFE6C86E)
val IPGuardGoldMuted = Color(0xFF8C7430)

// Neutral typography hierarchy
val IPGuardPlatinum = Color(0xFFF3F4F6)
val IPGuardSlate = Color(0xFF9CA3AF)
val IPGuardSlateDim = Color(0xFF6B7280)

// Semantic status tokens (always paired with iconography & labels)
val IPGuardVerified = Color(0xFF34D399)
val IPGuardWarning = Color(0xFFE6C86E)
val IPGuardDanger = Color(0xFFF87171)

// Compatibility aliases mapped cleanly to Obsidian & Gold system
val IPGuardNavy950 = IPGuardObsidian
val IPGuardNavy900 = IPGuardSurface
val IPGuardNavy800 = IPGuardSurfaceElevated
val IPGuardNavy700 = IPGuardSurfaceElevated
val IPGuardTeal = IPGuardGoldBright
val IPGuardMist = IPGuardPlatinum
val IPGuardMistMuted = IPGuardSlate
val IPGuardOutline = IPGuardHairline
val IPGuardSuccess = IPGuardVerified

private val IPGuardColorScheme = darkColorScheme(
    primary = IPGuardGold,
    onPrimary = IPGuardObsidian,
    primaryContainer = Color(0xFF241E11),
    onPrimaryContainer = IPGuardGoldBright,
    secondary = IPGuardGoldBright,
    onSecondary = IPGuardObsidian,
    secondaryContainer = IPGuardSurfaceElevated,
    onSecondaryContainer = IPGuardPlatinum,
    tertiary = IPGuardVerified,
    onTertiary = IPGuardObsidian,
    background = IPGuardObsidian,
    onBackground = IPGuardPlatinum,
    surface = IPGuardSurface,
    onSurface = IPGuardPlatinum,
    surfaceVariant = IPGuardSurfaceElevated,
    onSurfaceVariant = IPGuardSlate,
    outline = IPGuardHairline,
    error = IPGuardDanger,
    onError = IPGuardObsidian,
    errorContainer = Color(0xFF3A1619),
    onErrorContainer = Color(0xFFFEE2E2)
)

private val IPGuardTypography = Typography(
    displaySmall = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.SemiBold,
        fontSize = 30.sp,
        lineHeight = 36.sp,
        letterSpacing = (-0.5).sp
    ),
    headlineMedium = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.SemiBold,
        fontSize = 24.sp,
        lineHeight = 30.sp,
        letterSpacing = (-0.3).sp
    ),
    titleLarge = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.SemiBold,
        fontSize = 19.sp,
        lineHeight = 25.sp
    ),
    titleMedium = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Medium,
        fontSize = 16.sp,
        lineHeight = 22.sp
    ),
    bodyLarge = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Normal,
        fontSize = 15.sp,
        lineHeight = 22.sp
    ),
    bodyMedium = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Normal,
        fontSize = 14.sp,
        lineHeight = 20.sp
    ),
    bodySmall = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Normal,
        fontSize = 12.sp,
        lineHeight = 17.sp
    ),
    labelLarge = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.SemiBold,
        fontSize = 14.sp,
        lineHeight = 20.sp,
        letterSpacing = 0.2.sp
    ),
    labelMedium = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Medium,
        fontSize = 13.sp,
        lineHeight = 18.sp
    ),
    labelSmall = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.SemiBold,
        fontSize = 11.sp,
        lineHeight = 15.sp,
        letterSpacing = 0.8.sp
    )
)

@Composable
fun IPGuardTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = IPGuardColorScheme,
        typography = IPGuardTypography,
        content = content
    )
}
