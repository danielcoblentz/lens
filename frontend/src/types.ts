// shared shapes for files, upload progress, chat, and the backend responses

export interface FileMeta {
  name: string;
  size: number;
  type: string;
  lastModified: number;
}

export type UploadPhase = "uploading" | "processing" | "ready" | "error";

export interface UploadStatus {
  progress: number;
  status: UploadPhase;
  sessionId: string | null;
  error?: string;
}

export interface Message {
  role: "user" | "assistant";
  content: string;
}

// POST /llamaGet
export interface PresignResponse {
  sessionId: string;
  uploadUrl: string;
}

// POST /query
export interface QueryResponse {
  sessionId: string;
  answer: string;
  metrics?: Record<string, number | boolean>;
}
