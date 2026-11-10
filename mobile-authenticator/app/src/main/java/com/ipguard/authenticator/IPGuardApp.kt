package com.ipguard.authenticator

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.fragment.app.FragmentActivity
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.rememberNavController
import com.ipguard.authenticator.navigation.AppDestination
import com.ipguard.authenticator.navigation.AppNavHost
import com.ipguard.authenticator.ui.state.AuthenticatorViewModel
import com.ipguard.authenticator.ui.state.PreviewResult

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
        onApproveSign = { activity: FragmentActivity, onDone: (Boolean) -> Unit ->
            if (uiState.activeSession.payload != null) {
                viewModel.approveAndExecuteAuth(activity) { success ->
                    onDone(success)
                }
            } else {
                val challenge = uiState.previewRequest.challenge.toByteArray(Charsets.UTF_8)
                viewModel.authenticateAndSign(activity, challenge) {
                    onDone(true)
                }
            }
        },
        onContinueExistingAuth = { activity: FragmentActivity, onDone: (Boolean) -> Unit ->
            if (uiState.activeSession.payload != null) {
                viewModel.continueWithExistingAuthFallback(activity) { success ->
                    onDone(success)
                }
            }
        },
        onApprovalError = { viewModel.reportApprovalHostUnavailable() },
        onTestSign = { activity: FragmentActivity ->
            val challenge = "IPGUARD_MANUAL_TEST_${System.currentTimeMillis()}".toByteArray(Charsets.UTF_8)
            viewModel.authenticateAndSign(activity, challenge)
        },
        onQrScanned = { rawBarcode ->
            viewModel.onQrCodeScanned(
                rawBarcode = rawBarcode,
                onValid = { _ ->
                    navController.navigate(AppDestination.AuthenticationRequest.route)
                },
                onInvalid = { _ ->
                    navController.navigate(
                        AppDestination.Result.createRoute(PreviewResult.REJECTED)
                    )
                }
            )
        },
        onCancelActiveSession = {
            viewModel.cancelActiveSession()
        },
        onSyncBackend = {
            viewModel.refreshAll()
            viewModel.syncRegistrationWithBackend()
        },
        modifier = modifier
    )
}
