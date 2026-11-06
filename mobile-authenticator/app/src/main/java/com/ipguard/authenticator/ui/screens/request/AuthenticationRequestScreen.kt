package com.ipguard.authenticator.ui.screens.request

import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
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
import com.ipguard.authenticator.ui.components.PillTone
import com.ipguard.authenticator.ui.components.ScreenActions
import com.ipguard.authenticator.ui.components.SectionTitle
import com.ipguard.authenticator.ui.state.PreviewSignInRequest

@Composable
fun AuthenticationRequestScreen(
    request: PreviewSignInRequest,
    onBack: () -> Unit,
    onReview: () -> Unit,
    onReject: () -> Unit,
    onScan: () -> Unit,
    modifier: Modifier = Modifier
) {
    AuthenticatorScreen(
        eyebrow = stringResource(R.string.request_eyebrow),
        title = stringResource(R.string.request_title),
        subtitle = stringResource(R.string.request_subtitle),
        modifier = modifier,
        onBack = onBack
    ) {
        AppPill(
            text = stringResource(R.string.request_sample_badge),
            tone = PillTone.GOLD
        )
        Spacer(Modifier.height(20.dp))

        InformationCard {
            SectionTitle(text = stringResource(R.string.request_context_title))
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = stringResource(R.string.request_service_label),
                value = request.service
            )
            KeyValueRow(
                label = stringResource(R.string.request_browser_label),
                value = request.browser
            )
            KeyValueRow(
                label = stringResource(R.string.request_origin_label),
                value = request.origin
            )
            KeyValueRow(
                label = stringResource(R.string.request_purpose_label),
                value = stringResource(R.string.request_purpose_value)
            )
            KeyValueRow(
                label = stringResource(R.string.request_received_label),
                value = stringResource(R.string.request_received_value),
                showDivider = false
            )
        }

        Spacer(Modifier.height(14.dp))
        NoticeCard(
            text = stringResource(R.string.request_notice),
            tone = NoticeTone.INFO
        )
        Spacer(Modifier.height(10.dp))
        NoticeCard(
            text = stringResource(R.string.request_warning),
            tone = NoticeTone.WARNING
        )
        Spacer(Modifier.height(24.dp))
        ScreenActions(
            primaryLabel = stringResource(R.string.request_primary_action),
            onPrimary = onReview,
            secondaryLabel = stringResource(R.string.request_secondary_action),
            onSecondary = onReject,
            tertiaryLabel = stringResource(R.string.request_scan_link),
            onTertiary = onScan
        )
    }
}
