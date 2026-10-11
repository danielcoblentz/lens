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

// returned by /llamaGet
export interface PresignResponse {
  sessionId: string;
  uploadUrl: string;
}

// returned by /query
export interface QueryResponse {
  sessionId: string;
  answer: string;
  metrics?: Record<string, number | boolean>;
}
