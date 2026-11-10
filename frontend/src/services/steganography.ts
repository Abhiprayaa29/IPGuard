import { apiClient, getApiErrorMessage } from './api'
import type {
  StegoCapacityInfo,
  StegoEncodeRequest,
  StegoEncodeResponse,
  WatermarkInspectResponse,
} from '../types/steganography'

function authHeaders(token: string) {
  const clean = token.startsWith('Bearer ') ? token : `Bearer ${token}`
  return {
    Authorization: clean,
  }
}

export async function getAssetStegoCapacity(
  token: string,
  assetId: string,
): Promise<StegoCapacityInfo> {
  try {
    const response = await apiClient.get<StegoCapacityInfo>(
      `/steganography/assets/${assetId}/capacity`,
      {
        headers: authHeaders(token),
        timeout: 60_000,
      },
    )
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}

export async function encodeCanonicalWatermark(
  token: string,
  assetId: string,
  payload: StegoEncodeRequest,
): Promise<StegoEncodeResponse> {
  try {
    const response = await apiClient.post<StegoEncodeResponse>(
      `/steganography/assets/${assetId}/encode`,
      payload,
      {
        headers: authHeaders(token),
        timeout: 90_000,
      },
    )
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}

export async function inspectExternalPng(
  token: string,
  file: File,
  expectedSourceSha256?: string,
): Promise<WatermarkInspectResponse> {
  try {
    const formData = new FormData()
    formData.append('file', file)
    if (expectedSourceSha256 && expectedSourceSha256.trim().length > 0) {
      formData.append('expected_source_sha256', expectedSourceSha256.trim())
    }

    const response = await apiClient.post<WatermarkInspectResponse>(
      '/steganography/inspect',
      formData,
      {
        headers: authHeaders(token),
        timeout: 90_000,
      },
    )
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}

export async function inspectVaultAssetPng(
  token: string,
  assetId: string,
  expectedSourceSha256?: string,
): Promise<WatermarkInspectResponse> {
  try {
    const body =
      expectedSourceSha256 && expectedSourceSha256.trim().length > 0
        ? { expected_source_sha256: expectedSourceSha256.trim() }
        : undefined
    const response = await apiClient.post<WatermarkInspectResponse>(
      `/steganography/assets/${assetId}/inspect`,
      body,
      {
        headers: authHeaders(token),
        timeout: 90_000,
      },
    )
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}
