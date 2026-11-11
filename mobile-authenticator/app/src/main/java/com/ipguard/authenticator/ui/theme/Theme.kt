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

// Charcoal security surface hierarchy (harmonized with Web Console)
val IPGuardObsidian = Color(0xFF0B0D11)
val IPGuardCharcoal = Color(0xFF11141B)
val IPGuardSurface = Color(0xFF11141B)
val IPGuardSurfaceElevated = Color(0xFF171B24)
val IPGuardHairline = Color(0xFF242936)

// Restrained Teal primary accent spectrum
val IPGuardAccent = Color(0xFF14B8A6)
val IPGuardAccentBright = Color(0xFF2DD4BF)
val IPGuardAccentMuted = Color(0xFF0F766E)

// Neutral typography hierarchy
val IPGuardPlatinum = Color(0xFFF4F4F5)
val IPGuardSlate = Color(0xFFA1A1AA)
val IPGuardSlateDim = Color(0xFF71717A)

// Semantic status tokens (always paired with iconography & labels)
val IPGuardVerified = Color(0xFF10B981)
val IPGuardWarning = Color(0xFFF59E0B)
val IPGuardDanger = Color(0xFFEF4444)

// Compatibility aliases mapped cleanly to Charcoal & Teal system
val IPGuardGold = IPGuardAccent
val IPGuardGoldBright = IPGuardAccentBright
val IPGuardGoldMuted = IPGuardAccentMuted
val IPGuardNavy950 = IPGuardObsidian
val IPGuardNavy900 = IPGuardSurface
val IPGuardNavy800 = IPGuardSurfaceElevated
val IPGuardNavy700 = IPGuardSurfaceElevated
val IPGuardTeal = IPGuardAccentBright
val IPGuardMist = IPGuardPlatinum
val IPGuardMistMuted = IPGuardSlate
val IPGuardOutline = IPGuardHairline
val IPGuardSuccess = IPGuardVerified

private val IPGuardColorScheme = darkColorScheme(
    primary = IPGuardAccent,
    onPrimary = IPGuardObsidian,
    primaryContainer = Color(0xFF0F2926),
    onPrimaryContainer = IPGuardAccentBright,
    secondary = IPGuardAccentBright,
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
