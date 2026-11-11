import { apiClient, getApiErrorMessage } from './api'
import type {
  AnchorVerifyResponse,
  BlockchainAnchorRecord,
  BlockchainOverviewResponse,
} from '../types/blockchain'

function authHeaders(token: string) {
  return {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  }
}

export async function fetchBlockchainOverview(
  token: string,
): Promise<BlockchainOverviewResponse> {
  try {
    const response = await apiClient.get<BlockchainOverviewResponse>(
      '/blockchain/anchors',
      authHeaders(token),
    )
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}

export async function triggerAuditBatchAnchor(
  token: string,
): Promise<BlockchainAnchorRecord> {
  try {
    const response = await apiClient.post<BlockchainAnchorRecord>(
      '/blockchain/anchors',
      {},
      {
        ...authHeaders(token),
        timeout: 60_000,
      },
    )
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}

export async function verifyBlockchainAnchor(
  anchorId: string,
  token: string,
): Promise<AnchorVerifyResponse> {
  try {
    const response = await apiClient.get<AnchorVerifyResponse>(
      `/blockchain/anchors/${anchorId}/verify`,
      authHeaders(token),
    )
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}
