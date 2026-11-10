package com.ipguard.authenticator.navigation

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.fragment.app.FragmentActivity
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.ipguard.authenticator.ui.screens.approval.ApprovalScreen
import com.ipguard.authenticator.ui.screens.deviceinfo.DeviceInformationScreen
import com.ipguard.authenticator.ui.screens.facegate.FaceGateScreen
import com.ipguard.authenticator.ui.screens.registration.DeviceRegistrationScreen
import com.ipguard.authenticator.ui.screens.request.AuthenticationRequestScreen
import com.ipguard.authenticator.ui.screens.result.ResultScreen
import com.ipguard.authenticator.ui.screens.scanner.QrScannerScreen
import com.ipguard.authenticator.ui.screens.settings.SecuritySettingsScreen
import com.ipguard.authenticator.ui.screens.vault.AssetVaultScreen
import com.ipguard.authenticator.ui.screens.welcome.WelcomeScreen
import com.ipguard.authenticator.ui.state.AuthenticatorUiState
import com.ipguard.authenticator.ui.state.PreviewResult

@Composable
fun AppNavHost(
    navController: NavHostController,
    uiState: AuthenticatorUiState,
    modifier: Modifier = Modifier,
    onGenerateKey: () -> Unit = {},
    onRegenerateKey: () -> Unit = {},
    onDeleteKey: () -> Unit = {},
    onRefreshKey: () -> Unit = {},
    onApproveSign: (FragmentActivity, (Boolean) -> Unit) -> Unit = { _, onDone -> onDone(true) },
    onContinueExistingAuth: (FragmentActivity, (Boolean) -> Unit) -> Unit = { _, onDone -> onDone(true) },
    onApprovalError: () -> Unit = {},
    onTestSign: (FragmentActivity) -> Unit = {},
    onQrScanned: (String) -> Unit = {},
    onCancelActiveSession: () -> Unit = {},
    onSyncBackend: () -> Unit = {}
) {
    val goHome: () -> Unit = {
        navController.popBackStack(
            route = AppDestination.Welcome.route,
            inclusive = false
        )
    }
    val goToDeviceInformation: () -> Unit = {
        navController.navigate(AppDestination.DeviceInformation.route) {
            popUpTo(AppDestination.Welcome.route) { inclusive = false }
            launchSingleTop = true
        }
    }
    val goToSecuritySettings: () -> Unit = {
        navController.navigate(AppDestination.SecuritySettings.route) {
            popUpTo(AppDestination.Welcome.route) { inclusive = false }
            launchSingleTop = true
        }
    }
    val goToRequest: () -> Unit = {
        navController.navigate(AppDestination.AuthenticationRequest.route) {
            popUpTo(AppDestination.Welcome.route) { inclusive = false }
            launchSingleTop = true
        }
    }

    NavHost(
        navController = navController,
        startDestination = AppDestination.Welcome.route,
        modifier = modifier
    ) {
        composable(AppDestination.Welcome.route) {
            WelcomeScreen(
                uiState = uiState,
                onStartSetup = {
                    if (!uiState.isRegistered) {
                        navController.navigate(AppDestination.Registration.route)
                    }
                },
                onStartSignIn = {
                    navController.navigate(AppDestination.QrScanner.route)
                },
                onReviewRequest = goToRequest,
                onOpenAssetVault = {
                    navController.navigate(AppDestination.AssetVault.route) {
                        popUpTo(AppDestination.Welcome.route) { inclusive = false }
                        launchSingleTop = true
                    }
                },
                onOpenDeviceInformation = goToDeviceInformation,
                onOpenSecuritySettings = goToSecuritySettings,
                onRefreshSync = onSyncBackend
            )
        }

        composable(AppDestination.Registration.route) {
            if (uiState.isRegistered) {
                // Already registered: prevent registration flow and return home
                goHome()
            } else {
                DeviceRegistrationScreen(
                    onBack = { navController.navigateUp() },
                    onContinue = {
                        navController.navigate(AppDestination.QrScanner.route)
                    }
                )
            }
        }

        composable(AppDestination.FaceGate.route) {
            FaceGateScreen(
                onBack = { navController.navigateUp() },
                onContinue = {
                    navController.navigate(AppDestination.QrScanner.route)
                }
            )
        }

        composable(AppDestination.QrScanner.route) {
            QrScannerScreen(
                onBack = { navController.navigateUp() },
                onScanComplete = { rawBarcode ->
                    onQrScanned(rawBarcode)
                }
            )
        }

        composable(AppDestination.AuthenticationRequest.route) {
            AuthenticationRequestScreen(
                request = uiState.previewRequest,
                activeSession = uiState.activeSession,
                onBack = {
                    onCancelActiveSession()
                    navController.navigateUp()
                },
                onReview = {
                    navController.navigate(AppDestination.Approval.route)
                },
                onReject = {
                    onCancelActiveSession()
                    navController.navigate(
                        AppDestination.Result.createRoute(PreviewResult.REJECTED)
                    )
                },
                onScan = {
                    navController.navigate(AppDestination.QrScanner.route)
                }
            )
        }

        composable(AppDestination.Approval.route) {
            val context = LocalContext.current
            val activity = context as? FragmentActivity
            ApprovalScreen(
                request = uiState.previewRequest,
                activeSession = uiState.activeSession,
                authPolicy = uiState.authPolicy,
                signingDiagnostic = uiState.signingDiagnostic,
                faceGate = uiState.faceGate,
                onBack = {
                    onCancelActiveSession()
                    navController.navigateUp()
                },
                onApprove = {
                    if (activity == null) {
                        onApprovalError()
                    } else {
                        onApproveSign(activity) { success ->
                            if (success) {
                                navController.navigate(
                                    AppDestination.Result.createRoute(PreviewResult.APPROVED)
                                )
                            } else {
                                navController.navigate(
                                    AppDestination.Result.createRoute(PreviewResult.REJECTED)
                                )
                            }
                        }
                    }
                },
                onContinueFallback = {
                    if (activity == null) {
                        onApprovalError()
                    } else {
                        onContinueExistingAuth(activity) { success ->
                            if (success) {
                                navController.navigate(
                                    AppDestination.Result.createRoute(PreviewResult.APPROVED)
                                )
                            } else {
                                navController.navigate(
                                    AppDestination.Result.createRoute(PreviewResult.REJECTED)
                                )
                            }
                        }
                    }
                },
                onReject = {
                    onCancelActiveSession()
                    navController.navigate(
                        AppDestination.Result.createRoute(PreviewResult.REJECTED)
                    )
                }
            )
        }

        composable(
            route = AppDestination.Result.route,
            arguments = listOf(
                navArgument(AppDestination.Result.OUTCOME_ARG) {
                    type = NavType.StringType
                    defaultValue = PreviewResult.SCAN_COMPLETE.routeValue
                }
            )
        ) { backStackEntry ->
            val result = PreviewResult.fromRoute(
                backStackEntry.arguments?.getString(AppDestination.Result.OUTCOME_ARG)
            )
            ResultScreen(
                outcome = result,
                onHome = {
                    onCancelActiveSession()
                    goHome()
                },
                onDeviceDetails = goToDeviceInformation,
                onReviewAnother = goToRequest,
                signingDiagnostic = uiState.signingDiagnostic,
                activeSession = uiState.activeSession
            )
        }

        composable(AppDestination.DeviceInformation.route) {
            val context = LocalContext.current
            val activity = context as? FragmentActivity
            DeviceInformationScreen(
                uiState = uiState,
                onBack = { navController.navigateUp() },
                onOpenSecuritySettings = {
                    navController.navigate(AppDestination.SecuritySettings.route)
                },
                onHome = goHome,
                onGenerateKey = onGenerateKey,
                onRegenerateKey = onRegenerateKey,
                onDeleteKey = onDeleteKey,
                onRefreshKey = onRefreshKey,
                onSyncBackend = onSyncBackend,
                onTestSign = {
                    if (activity != null) {
                        onTestSign(activity)
                    }
                }
            )
        }

        composable(AppDestination.SecuritySettings.route) {
            SecuritySettingsScreen(
                uiState = uiState,
                onBack = { navController.navigateUp() },
                onDeviceInformation = goToDeviceInformation,
                onHome = goHome
            )
        }

        composable(AppDestination.AssetVault.route) {
            AssetVaultScreen(
                uiState = uiState,
                onBack = { navController.navigateUp() },
                onUnlockWithQr = {
                    if (uiState.isRegistered) {
                        navController.navigate(AppDestination.QrScanner.route)
                    } else {
                        navController.navigate(AppDestination.Registration.route)
                    }
                },
                onOpenDeviceSecurity = goToDeviceInformation,
                onRefreshSync = onSyncBackend
            )
        }
    }
}
