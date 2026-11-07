package com.ipguard.authenticator.network

sealed class ApiResult<out T> {
    data class Success<out T>(val data: T) : ApiResult<T>()
    data class HttpError(
        val code: Int,
        val errorCode: String,
        val message: String
    ) : ApiResult<Nothing>()
    data class NetworkError(
        val message: String,
        val cause: Throwable? = null
    ) : ApiResult<Nothing>()
}
