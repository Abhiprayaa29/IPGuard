export interface Note {
  id: string
  title: string
  content: string
  created_at: string
  updated_at: string
}

export interface NoteCreateRequest {
  title: string
  content: string
}

export interface NoteUpdateRequest {
  title?: string
  content?: string
}
