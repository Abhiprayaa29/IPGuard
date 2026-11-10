package com.ipguard.authenticator.navigation

import com.ipguard.authenticator.ui.state.PreviewResult

sealed class AppDestination(val route: String) {
    data object Welcome : AppDestination("welcome")
    data object Registration : AppDestination("registration")
    data object FaceGate : AppDestination("face_gate")
    data object QrScanner : AppDestination("qr_scanner")
    data object AuthenticationRequest : AppDestination("authentication_request")
    data object Approval : AppDestination("approval")
    data object DeviceInformation : AppDestination("device_information")
    data object SecuritySettings : AppDestination("security_settings")
    data object AssetVault : AppDestination("asset_vault")

    data object Result : AppDestination("result/{outcome}") {
        const val OUTCOME_ARG = "outcome"

        fun createRoute(result: PreviewResult): String {
            return "result/${result.routeValue}"
        }
    }
}
