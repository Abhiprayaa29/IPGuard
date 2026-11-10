package com.ipguard.authenticator.ui.screens.registration

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
import com.ipguard.authenticator.ui.components.PrincipleRow
import com.ipguard.authenticator.ui.components.ScreenActions
import com.ipguard.authenticator.ui.components.SectionTitle
import com.ipguard.authenticator.ui.theme.IPGuardGoldBright
import com.ipguard.authenticator.ui.theme.IPGuardVerified

@Composable
fun DeviceRegistrationScreen(
    onBack: () -> Unit,
    onContinue: () -> Unit,
    modifier: Modifier = Modifier
) {
    AuthenticatorScreen(
        eyebrow = "ONE-TIME ENROLLMENT",
        title = "Bind this phone",
        subtitle = "IPGuard links one active hardware authenticator to your account. Enrollment initializes your non-exportable Keystore key.",
        modifier = modifier,
        onBack = onBack
    ) {
        AppPill(
            text = "SECURITY PROTOCOL M2",
            tone = PillTone.GOLD
        )
        Spacer(Modifier.height(18.dp))

        InformationCard {
            SectionTitle(text = "ENROLLMENT GUARANTEES")
            Spacer(Modifier.height(14.dp))
            PrincipleRow(
                marker = "01",
                text = stringResource(R.string.registration_principle_one)
            )
            Spacer(Modifier.height(12.dp))
            PrincipleRow(
                marker = "02",
                text = "ECDSA P-256 private key is generated inside Android Keystore and never leaves the device."
            )
            Spacer(Modifier.height(12.dp))
            PrincipleRow(
                marker = "03",
                text = "Native BiometricPrompt verifies your face/biometric gate, then Keystore authorizes hardware signing."
            )
        }

        Spacer(Modifier.height(14.dp))
        InformationCard {
            SectionTitle(text = "AUTHENTICATION PIPELINE")
            Spacer(Modifier.height(8.dp))
            KeyValueRow(
                label = "STEP 01",
                value = "Scan Enrollment QR Challenge",
                valueColor = IPGuardGoldBright,
                monospaceValue = true
            )
            KeyValueRow(
                label = "STEP 02",
                value = "Native Face / Biometric Gate",
                monospaceValue = true
            )
            KeyValueRow(
                label = "STEP 03",
                value = "Keystore CryptoObject Authorization",
                monospaceValue = true
            )
            KeyValueRow(
                label = "STEP 04",
                value = "Backend Public Key Registration",
                valueColor = IPGuardVerified,
                monospaceValue = true,
                showDivider = false
            )
        }

        Spacer(Modifier.height(14.dp))
        NoticeCard(
            text = "Ensure the Web Console shows an Enrollment QR code before continuing.",
            tone = NoticeTone.INFO
        )
        Spacer(Modifier.height(22.dp))
        ScreenActions(
            primaryLabel = "Continue to QR Scanner",
            onPrimary = onContinue,
            secondaryLabel = stringResource(R.string.registration_secondary_action),
            onSecondary = onBack
        )
    }
}
