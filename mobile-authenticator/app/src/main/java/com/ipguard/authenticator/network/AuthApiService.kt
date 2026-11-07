package com.ipguard.authenticator.network

import com.ipguard.authenticator.BuildConfig
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import org.json.JSONException
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit

interface AuthApiService {
    suspend fun scanSession(sessionToken: String, deviceId: String?): ApiResult<SessionStatusDto>
    suspend fun verifySession(sessionToken: String, request: VerifySessionRequest): ApiResult<SessionStatusDto>
    suspend fun registerDevice(request: RegisterDeviceRequest): ApiResult<DeviceRegisteredDto>
}

class OkHttpAuthApiService(
    private val baseUrl: String = BuildConfig.API_BASE_URL,
    private val client: OkHttpClient = defaultOkHttpClient()
) : AuthApiService {

    private val jsonMediaType = "application/json; charset=utf-8".toMediaType()

    override suspend fun scanSession(
        sessionToken: String,
        deviceId: String?
    ): ApiResult<SessionStatusDto> = withContext(Dispatchers.IO) {
        val jsonBody = JSONObject().apply {
            if (!deviceId.isNullOrBlank()) {
                put("device_id", deviceId)
            }
        }.toString()

        val request = Request.Builder()
            .url(resolveUrl("/auth/sessions/$sessionToken/scan"))
            .post(jsonBody.toRequestBody(jsonMediaType))
            .build()

        executeRequest(request) { json ->
            SessionStatusDto(
                sessionToken = json.optString("session_token", sessionToken),
                status = json.optString("status", "SCANNED"),
                sessionType = json.optString("session_type", "AUTHENTICATION"),
                expiresAt = json.optString("expires_at", "")
            )
        }
    }

    override suspend fun verifySession(
        sessionToken: String,
        request: VerifySessionRequest
    ): ApiResult<SessionStatusDto> = withContext(Dispatchers.IO) {
        val jsonBody = JSONObject().apply {
            put("device_id", request.deviceId)
            put("canonical_payload", request.canonicalPayload)
            put("signature", request.signature)
        }.toString()

        val httpRequest = Request.Builder()
            .url(resolveUrl("/auth/sessions/$sessionToken/verify"))
            .post(jsonBody.toRequestBody(jsonMediaType))
            .build()

        executeRequest(httpRequest) { json ->
            SessionStatusDto(
                sessionToken = json.optString("session_token", sessionToken),
                status = json.optString("status", "APPROVED"),
                sessionType = json.optString("session_type", "AUTHENTICATION"),
                expiresAt = json.optString("expires_at", "")
            )
        }
    }

    override suspend fun registerDevice(
        request: RegisterDeviceRequest
    ): ApiResult<DeviceRegisteredDto> = withContext(Dispatchers.IO) {
        val jsonBody = JSONObject().apply {
            put("session_token", request.sessionToken)
            put("device_id", request.deviceId)
            put("device_name", request.deviceName)
            put("model", request.model)
            put("android_version", request.androidVersion)
            put("public_key_x509", request.publicKeyX509)
            put("security_level", request.securityLevel)
            put("canonical_payload", request.canonicalPayload)
            put("signature", request.signature)
        }.toString()

        val httpRequest = Request.Builder()
            .url(resolveUrl("/auth/devices/register"))
            .post(jsonBody.toRequestBody(jsonMediaType))
            .build()

        executeRequest(httpRequest) { json ->
            DeviceRegisteredDto(
                id = json.optString("id", ""),
                deviceId = json.optString("device_id", request.deviceId),
                deviceName = json.optString("device_name", request.deviceName),
                status = json.optString("status", "ACTIVE"),
                publicKeyFingerprint = json.optString("public_key_fingerprint", "")
            )
        }
    }

    private fun <T> executeRequest(
        request: Request,
        parser: (JSONObject) -> T
    ): ApiResult<T> {
        return try {
            client.newCall(request).execute().use { response ->
                val bodyString = response.body?.string() ?: ""
                if (response.isSuccessful) {
                    val json = if (bodyString.isNotBlank()) JSONObject(bodyString) else JSONObject()
                    ApiResult.Success(parser(json))
                } else {
                    parseHttpError(response, bodyString)
                }
            }
        } catch (e: IOException) {
            ApiResult.NetworkError("Network connection failed: ${e.message}", e)
        } catch (e: Exception) {
            ApiResult.NetworkError("Unexpected network failure: ${e.message}", e)
        }
    }

    private fun parseHttpError(response: Response, bodyString: String): ApiResult.HttpError {
        var errorCode = "http_${response.code}"
        var message = "Request failed with HTTP ${response.code}"

        try {
            if (bodyString.isNotBlank()) {
                val json = JSONObject(bodyString)
                if (json.has("error")) {
                    val errorObj = json.getJSONObject("error")
                    errorCode = errorObj.optString("code", errorCode)
                    message = errorObj.optString("message", message)
                } else if (json.has("detail")) {
                    message = json.optString("detail", message)
                }
            }
        } catch (_: JSONException) {
            // Keep default code and message if parsing fails
        }

        return ApiResult.HttpError(
            code = response.code,
            errorCode = errorCode,
            message = message
        )
    }

    private fun resolveUrl(path: String): String {
        val cleanBase = baseUrl.trimEnd('/')
        val cleanPath = path.trimStart('/')
        return "$cleanBase/$cleanPath"
    }

    companion object {
        fun defaultOkHttpClient(): OkHttpClient {
            return OkHttpClient.Builder()
                .connectTimeout(10, TimeUnit.SECONDS)
                .readTimeout(15, TimeUnit.SECONDS)
                .writeTimeout(15, TimeUnit.SECONDS)
                .retryOnConnectionFailure(false)
                .build()
        }
    }
}
