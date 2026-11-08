import { apiClient, getApiErrorMessage } from './api'
import type { Note, NoteCreateRequest, NoteUpdateRequest } from '../types/notes'

function authHeaders(token: string) {
  return {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  }
}

export async function getNotes(token: string): Promise<Note[]> {
  try {
    const response = await apiClient.get<Note[]>('/notes', authHeaders(token))
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}

export async function getNote(id: string, token: string): Promise<Note> {
  try {
    const response = await apiClient.get<Note>(`/notes/${id}`, authHeaders(token))
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}

export async function createNote(
  data: NoteCreateRequest,
  token: string,
): Promise<Note> {
  try {
    const response = await apiClient.post<Note>('/notes', data, authHeaders(token))
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}

export async function updateNote(
  id: string,
  data: NoteUpdateRequest,
  token: string,
): Promise<Note> {
  try {
    const response = await apiClient.put<Note>(`/notes/${id}`, data, authHeaders(token))
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}

export async function deleteNote(id: string, token: string): Promise<void> {
  try {
    await apiClient.delete(`/notes/${id}`, authHeaders(token))
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}
