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

val IPGuardNavy950 = Color(0xFF06121F)
val IPGuardNavy900 = Color(0xFF0B1D2D)
val IPGuardNavy800 = Color(0xFF112A3D)
val IPGuardNavy700 = Color(0xFF18374D)
val IPGuardTeal = Color(0xFF38D6C8)
val IPGuardGold = Color(0xFFD8B56C)
val IPGuardMist = Color(0xFFE9F4F5)
val IPGuardMistMuted = Color(0xFF9CB1BE)
val IPGuardOutline = Color(0xFF294456)
val IPGuardSuccess = Color(0xFF6FE7B7)
val IPGuardDanger = Color(0xFFFF9B8F)

private val IPGuardColorScheme = darkColorScheme(
    primary = IPGuardTeal,
    onPrimary = IPGuardNavy950,
    primaryContainer = IPGuardNavy800,
    onPrimaryContainer = IPGuardTeal,
    secondary = IPGuardGold,
    onSecondary = IPGuardNavy950,
    secondaryContainer = IPGuardNavy800,
    onSecondaryContainer = IPGuardGold,
    tertiary = IPGuardGold,
    onTertiary = IPGuardNavy950,
    background = IPGuardNavy950,
    onBackground = IPGuardMist,
    surface = IPGuardNavy900,
    onSurface = IPGuardMist,
    surfaceVariant = IPGuardNavy800,
    onSurfaceVariant = IPGuardMistMuted,
    outline = IPGuardOutline,
    error = IPGuardDanger,
    onError = IPGuardNavy950,
    errorContainer = Color(0xFF4B1E20),
    onErrorContainer = Color(0xFFFFDAD5)
)

private val IPGuardTypography = Typography(
    displaySmall = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Bold,
        fontSize = 36.sp,
        lineHeight = 42.sp,
        letterSpacing = (-0.6).sp
    ),
    headlineMedium = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Bold,
        fontSize = 28.sp,
        lineHeight = 34.sp,
        letterSpacing = (-0.3).sp
    ),
    titleLarge = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.SemiBold,
        fontSize = 22.sp,
        lineHeight = 28.sp
    ),
    titleMedium = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.SemiBold,
        fontSize = 18.sp,
        lineHeight = 24.sp
    ),
    bodyLarge = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Normal,
        fontSize = 16.sp,
        lineHeight = 24.sp
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
        lineHeight = 18.sp
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
        letterSpacing = 0.3.sp
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
