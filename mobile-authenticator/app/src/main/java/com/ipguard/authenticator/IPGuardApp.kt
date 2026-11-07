package com.ipguard.authenticator

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.fragment.app.FragmentActivity
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.rememberNavController
import com.ipguard.authenticator.navigation.AppNavHost
import com.ipguard.authenticator.ui.state.AuthenticatorViewModel

@Composable
fun IPGuardApp(
    modifier: Modifier = Modifier,
    viewModel: AuthenticatorViewModel = viewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val navController = rememberNavController()

    AppNavHost(
        navController = navController,
        uiState = uiState,
        onGenerateKey = { viewModel.generateSigningKey(requireUserAuth = true) },
        onRegenerateKey = { viewModel.regenerateSigningKey(requireUserAuth = true) },
        onDeleteKey = { viewModel.deleteSigningKey() },
        onRefreshKey = { viewModel.refreshAll() },
        onApproveSign = { activity: FragmentActivity, onDone: () -> Unit ->
            val challenge = uiState.previewRequest.challenge.toByteArray(Charsets.UTF_8)
            viewModel.authenticateAndSign(activity, challenge) {
                onDone()
            }
        },
        onApprovalError = { viewModel.reportApprovalHostUnavailable() },
        onTestSign = { activity: FragmentActivity ->
            val challenge = "IPGUARD_MANUAL_TEST_${System.currentTimeMillis()}".toByteArray(Charsets.UTF_8)
            viewModel.authenticateAndSign(activity, challenge)
        },
        modifier = modifier
    )
}
