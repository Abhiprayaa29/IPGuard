package com.ipguard.authenticator.ui.screens.welcome

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.ipguard.authenticator.R
import com.ipguard.authenticator.ui.components.AppPill
import com.ipguard.authenticator.ui.components.AuthenticatorScreen
import com.ipguard.authenticator.ui.components.CardDivider
import com.ipguard.authenticator.ui.components.InformationCard
import com.ipguard.authenticator.ui.components.InlineLink
import com.ipguard.authenticator.ui.components.KeyValueRow
import com.ipguard.authenticator.ui.components.NoticeCard
import com.ipguard.authenticator.ui.components.NoticeTone
import com.ipguard.authenticator.ui.components.PillTone
import com.ipguard.authenticator.ui.components.ScreenActions
import com.ipguard.authenticator.ui.components.SectionTitle
import com.ipguard.authenticator.ui.state.AuthenticatorUiState
import com.ipguard.authenticator.ui.theme.IPGuardGold
import com.ipguard.authenticator.ui.theme.IPGuardMist
import com.ipguard.authenticator.ui.theme.IPGuardMistMuted
import com.ipguard.authenticator.ui.theme.IPGuardOutline

@Composable
fun WelcomeScreen(
    uiState: AuthenticatorUiState,
    onStartSetup: () -> Unit,
    onReviewRequest: () -> Unit,
    onOpenDeviceInformation: () -> Unit,
    onOpenSecuritySettings: () -> Unit,
    modifier: Modifier = Modifier
) {
    AuthenticatorScreen(
        eyebrow = stringResource(R.string.welcome_eyebrow),
        title = stringResource(R.string.welcome_title),
        subtitle = stringResource(R.string.welcome_subtitle),
        modifier = modifier
    ) {
        AppPill(
            text = stringResource(R.string.welcome_build_badge),
            tone = PillTone.GOLD
        )
        Spacer(Modifier.height(22.dp))

        InformationCard {
            SectionTitle(text = stringResource(R.string.welcome_device_label))
            Spacer(Modifier.height(14.dp))
            Text(
                text = stringResource(R.string.welcome_device_title),
                style = MaterialTheme.typography.titleLarge,
                color = IPGuardMist
            )
            Spacer(Modifier.height(6.dp))
            Text(
                text = stringResource(R.string.welcome_device_body),
                style = MaterialTheme.typography.bodyMedium,
                color = IPGuardMistMuted
            )
            Spacer(Modifier.height(18.dp))
            CardDivider()
            KeyValueRow(
                label = stringResource(R.string.welcome_binding_label),
                value = stringResource(R.string.welcome_binding_value)
            )
            KeyValueRow(
                label = stringResource(R.string.welcome_key_label),
                value = if (uiState.keyDiagnostic.hasKey) {
                    stringResource(R.string.welcome_key_created_value)
                } else {
                    stringResource(R.string.welcome_key_value)
                }
            )
            KeyValueRow(
                label = stringResource(R.string.welcome_face_label),
                value = stringResource(R.string.welcome_face_value)
            )
            KeyValueRow(
                label = stringResource(R.string.welcome_api_label),
                value = stringResource(R.string.welcome_api_value),
                showDivider = false
            )
        }

        Spacer(Modifier.height(14.dp))
        NoticeCard(
            text = stringResource(R.string.welcome_notice),
            tone = NoticeTone.INFO
        )
        Spacer(Modifier.height(24.dp))
        ScreenActions(
            primaryLabel = stringResource(R.string.welcome_primary_action),
            onPrimary = onStartSetup,
            secondaryLabel = stringResource(R.string.welcome_secondary_action),
            onSecondary = onReviewRequest
        )
        Spacer(Modifier.height(6.dp))
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically
        ) {
            InlineLink(
                label = stringResource(R.string.welcome_device_link),
                onClick = onOpenDeviceInformation
            )
            Box(
                modifier = Modifier
                    .width(1.dp)
                    .height(14.dp)
                    .background(IPGuardOutline)
            )
            InlineLink(
                label = stringResource(R.string.welcome_settings_link),
                onClick = onOpenSecuritySettings
            )
        }
        Spacer(Modifier.height(18.dp))
        Text(
            text = stringResource(R.string.welcome_policy),
            modifier = Modifier.fillMaxWidth(),
            style = MaterialTheme.typography.labelSmall,
            color = IPGuardGold.copy(alpha = 0.8f),
            textAlign = TextAlign.Center,
            letterSpacing = 1.5.sp
        )
    }
}
