import { apiClient, getApiErrorMessage } from './api'
import type { Asset, AssetRenameRequest } from '../types/assets'

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
