package com.ipguard.authenticator.ui.state

enum class PreviewResult(val routeValue: String) {
    SCAN_COMPLETE("scan_complete"),
    APPROVED("approved"),
    REJECTED("rejected");

    companion object {
        fun fromRoute(value: String?): PreviewResult {
            return entries.firstOrNull { it.routeValue == value } ?: SCAN_COMPLETE
        }
    }
}
