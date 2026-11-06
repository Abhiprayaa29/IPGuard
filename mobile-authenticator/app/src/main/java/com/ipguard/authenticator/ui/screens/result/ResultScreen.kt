package com.ipguard.authenticator.ui.screens.result

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.ipguard.authenticator.R
import com.ipguard.authenticator.ui.components.AppPill
import com.ipguard.authenticator.ui.components.AuthenticatorScreen
import com.ipguard.authenticator.ui.components.InformationCard
import com.ipguard.authenticator.ui.components.KeyValueRow
import com.ipguard.authenticator.ui.components.NoticeCard
import com.ipguard.authenticator.ui.components.NoticeTone
import com.ipguard.authenticator.ui.components.OutcomeSeal
import com.ipguard.authenticator.ui.components.PillTone
import com.ipguard.authenticator.ui.components.ScreenActions
import com.ipguard.authenticator.ui.components.SectionTitle
import com.ipguard.authenticator.ui.state.PreviewResult

@Composable
fun ResultScreen(
    outcome: PreviewResult,
    onHome: () -> Unit,
    onDeviceDetails: () -> Unit,
    onReviewAnother: () -> Unit,
    modifier: Modifier = Modifier
) {
    val eyebrow = when (outcome) {
        PreviewResult.SCAN_COMPLETE -> stringResource(R.string.result_eyebrow_scan)
        PreviewResult.APPROVED -> stringResource(R.string.result_eyebrow_approved)
        PreviewResult.REJECTED -> stringResource(R.string.result_eyebrow_rejected)
    }
    val title = when (outcome) {
        PreviewResult.SCAN_COMPLETE -> stringResource(R.string.result_title_scan)
        PreviewResult.APPROVED -> stringResource(R.string.result_title_approved)
        PreviewResult.REJECTED -> stringResource(R.string.result_title_rejected)
    }
    val subtitle = when (outcome) {
        PreviewResult.SCAN_COMPLETE -> stringResource(R.string.result_subtitle_scan)
        PreviewResult.APPROVED -> stringResource(R.string.result_subtitle_approved)
        PreviewResult.REJECTED -> stringResource(R.string.result_subtitle_rejected)
    }

    BackHandler(onBack = onHome)

    AuthenticatorScreen(
        eyebrow = eyebrow,
        title = title,
        subtitle = subtitle,
        modifier = modifier,
        onBack = onHome
    ) {
        AppPill(
            text = stringResource(R.string.result_badge),
            tone = PillTone.GOLD
        )
        Spacer(Modifier.height(22.dp))
        Box(
            modifier = Modifier.fillMaxWidth(),
            contentAlignment = Alignment.Center
        ) {
            OutcomeSeal(positive = outcome != PreviewResult.REJECTED)
        }
        Spacer(Modifier.height(22.dp))

        InformationCard {
            SectionTitle(text = stringResource(R.string.result_state_title))
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = stringResource(R.string.result_auth_label),
                value = stringResource(R.string.result_no_value)
            )
            KeyValueRow(
                label = stringResource(R.string.result_key_label),
                value = stringResource(R.string.result_no_value)
            )
            KeyValueRow(
                label = stringResource(R.string.result_session_label),
                value = stringResource(R.string.result_no_value),
                showDivider = false
            )
        }

        Spacer(Modifier.height(14.dp))
        NoticeCard(
            text = stringResource(R.string.result_notice),
            tone = NoticeTone.INFO
        )
        Spacer(Modifier.height(24.dp))
        ScreenActions(
            primaryLabel = stringResource(R.string.result_primary_action),
            onPrimary = onHome,
            secondaryLabel = stringResource(R.string.result_secondary_action),
            onSecondary = onDeviceDetails,
            tertiaryLabel = stringResource(R.string.result_tertiary_action),
            onTertiary = onReviewAnother
        )
    }
}
