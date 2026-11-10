import { apiClient, getApiErrorMessage } from './api'
import type {
  Asset,
  AssetRenameRequest,
  StegoEmbedRequest,
  StegoEmbedResponse,
  WatermarkVerifyResponse,
  WatermarkExtractResponse,
} from '../types/assets'

function authHeaders(token: string) {
  const clean = token.startsWith('Bearer ') ? token : `Bearer ${token}`
  return {
    Authorization: clean,
  }
}

export async function getAssets(token: string): Promise<Asset[]> {
  try {
    const response = await apiClient.get<Asset[]>('/assets', {
      headers: authHeaders(token),
    })
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}

export async function getAssetDetail(token: string, assetId: string): Promise<Asset> {
  try {
    const response = await apiClient.get<Asset>(`/assets/${assetId}`, {
      headers: authHeaders(token),
    })
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}

export async function uploadAsset(
  token: string,
  file: File,
  onProgress?: (progressPercent: number) => void,
): Promise<Asset> {
  try {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post<Asset>('/assets', formData, {
      headers: {
        ...authHeaders(token),
      },
      timeout: 120_000, // 2 minutes for 50 MB uploads
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percent)
        }
      },
    })
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}

export async function downloadAsset(
  token: string,
  assetId: string,
): Promise<Blob> {
  try {
    const response = await apiClient.get(`/assets/${assetId}/download`, {
      headers: authHeaders(token),
      responseType: 'blob',
      timeout: 120_000,
    })
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}

export async function renameAsset(
  token: string,
  assetId: string,
  payload: AssetRenameRequest,
): Promise<Asset> {
  try {
    const response = await apiClient.patch<Asset>(
      `/assets/${assetId}`,
      payload,
      {
        headers: authHeaders(token),
      },
    )
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}

export async function deleteAsset(
  token: string,
  assetId: string,
): Promise<void> {
  try {
    await apiClient.delete(`/assets/${assetId}`, {
      headers: authHeaders(token),
    })
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}

export async function embedWatermark(
  token: string,
  assetId: string,
  payloadB64: string,
): Promise<StegoEmbedResponse> {
  try {
    const requestBody: StegoEmbedRequest = { payload_b64: payloadB64 }
    const response = await apiClient.post<StegoEmbedResponse>(
      `/assets/${assetId}/steganography/embed`,
      requestBody,
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

export async function verifyWatermark(
  token: string,
  assetId: string,
): Promise<WatermarkVerifyResponse> {
  try {
    const response = await apiClient.post<WatermarkVerifyResponse>(
      `/assets/${assetId}/steganography/verify`,
      {},
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

export async function extractWatermark(
  token: string,
  assetId: string,
): Promise<WatermarkExtractResponse> {
  try {
    const response = await apiClient.post<WatermarkExtractResponse>(
      `/assets/${assetId}/steganography/extract`,
      {},
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
