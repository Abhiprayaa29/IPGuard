package com.ipguard.authenticator.ui.screens.registration

import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.ipguard.authenticator.R
import com.ipguard.authenticator.ui.components.AuthenticatorScreen
import com.ipguard.authenticator.ui.components.InformationCard
import com.ipguard.authenticator.ui.components.KeyValueRow
import com.ipguard.authenticator.ui.components.NoticeCard
import com.ipguard.authenticator.ui.components.NoticeTone
import com.ipguard.authenticator.ui.components.PrincipleRow
import com.ipguard.authenticator.ui.components.ScreenActions
import com.ipguard.authenticator.ui.components.SectionTitle
import com.ipguard.authenticator.ui.theme.IPGuardTeal

@Composable
fun DeviceRegistrationScreen(
    onBack: () -> Unit,
    onContinue: () -> Unit,
    modifier: Modifier = Modifier
) {
    AuthenticatorScreen(
        eyebrow = stringResource(R.string.registration_eyebrow),
        title = stringResource(R.string.registration_title),
        subtitle = stringResource(R.string.registration_subtitle),
        modifier = modifier,
        onBack = onBack
    ) {
        InformationCard {
            SectionTitle(text = stringResource(R.string.registration_principles_title))
            Spacer(Modifier.height(16.dp))
            PrincipleRow(
                marker = "01",
                text = stringResource(R.string.registration_principle_one)
            )
            Spacer(Modifier.height(14.dp))
            PrincipleRow(
                marker = "02",
                text = stringResource(R.string.registration_principle_two)
            )
            Spacer(Modifier.height(14.dp))
            PrincipleRow(
                marker = "03",
                text = stringResource(R.string.registration_principle_three)
            )
        }

        Spacer(Modifier.height(14.dp))
        InformationCard {
            SectionTitle(text = stringResource(R.string.registration_stages_title))
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = stringResource(R.string.registration_stage_face),
                value = stringResource(R.string.registration_stage_face_value),
                valueColor = IPGuardTeal
            )
            KeyValueRow(
                label = stringResource(R.string.registration_stage_scan),
                value = stringResource(R.string.registration_stage_scan_value)
            )
            KeyValueRow(
                label = stringResource(R.string.registration_stage_key),
                value = stringResource(R.string.registration_stage_key_value)
            )
            KeyValueRow(
                label = stringResource(R.string.registration_stage_approval),
                value = stringResource(R.string.registration_stage_approval_value),
                showDivider = false
            )
        }

        Spacer(Modifier.height(14.dp))
        NoticeCard(
            text = stringResource(R.string.registration_notice),
            tone = NoticeTone.INFO
        )
        Spacer(Modifier.height(24.dp))
        ScreenActions(
            primaryLabel = stringResource(R.string.registration_primary_action),
            onPrimary = onContinue,
            secondaryLabel = stringResource(R.string.registration_secondary_action),
            onSecondary = onBack
        )
    }
}
