package com.ipguard.authenticator.security.qr

sealed class QrPayloadValidationResult {
    data class Valid(val payload: QrAuthPayload) : QrPayloadValidationResult()
    data class Invalid(val reason: String, val errorCode: String) : QrPayloadValidationResult() {
        companion object {
            const val CODE_EMPTY_PAYLOAD = "empty_payload"
            const val CODE_OVERSIZED_PAYLOAD = "oversized_payload"
            const val CODE_MALFORMED_JSON = "malformed_json"
            const val CODE_UNSUPPORTED_VERSION = "unsupported_version"
            const val CODE_UNSUPPORTED_TYPE = "unsupported_type"
            const val CODE_INVALID_TOKEN = "invalid_session_token"
            const val CODE_INVALID_NONCE = "invalid_nonce"
            const val CODE_INVALID_ORIGIN = "invalid_origin"
            const val CODE_INVALID_TIMESTAMP = "invalid_timestamp"
            const val CODE_EXPIRED_TIMESTAMP = "expired_timestamp"
            const val CODE_FORBIDDEN_FIELD = "forbidden_secret_field"
        }
    }
}
