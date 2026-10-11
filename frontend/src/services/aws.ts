// client for the lens api gateway endpoints
import { PresignResponse, QueryResponse, SessionStatusResponse } from "../types";

const API_BASE = process.env.REACT_APP_API_BASE || "";

export type UploadProgressCallback = (percentComplete: number) => void;

// opens a session and returns a presigned s3 url to upload the pdf to
export async function getPresignedUploadUrl(): Promise<PresignResponse> {
  const response = await fetch(`${API_BASE}/llamaGet`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to get presigned URL: ${error}`);
  }

  const data = await response.json();
  return {
    sessionId: data.sessionId,
    uploadUrl: data.uploadUrl,
  };
}

// xhr instead of fetch because fetch does not report upload progress
export function uploadFileToS3(
  presignedUrl: string,
  file: File,
  onProgress?: UploadProgressCallback
): Promise<void> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener("progress", (event) => {
      if (event.lengthComputable && onProgress) {
        const percentComplete = Math.round((event.loaded / event.total) * 100);
        onProgress(percentComplete);
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve();
      } else {
        reject(new Error(`Upload failed with status ${xhr.status}`));
      }
    });

    xhr.addEventListener("error", () => {
      reject(new Error("Upload failed due to network error"));
    });

    xhr.open("PUT", presignedUrl);
    xhr.setRequestHeader("Content-Type", "application/pdf");
    xhr.send(file);
  });
}

// the s3 upload is what triggers parsing, so the session id is all the caller needs back
export async function uploadPDF(
  file: File,
  onProgress?: UploadProgressCallback
): Promise<{ sessionId: string }> {
  const { sessionId, uploadUrl } = await getPresignedUploadUrl();
  await uploadFileToS3(uploadUrl, file, onProgress);
  return { sessionId };
}

export async function fetchSessionStatus(sessionId: string): Promise<SessionStatusResponse> {
  const response = await fetch(`${API_BASE}/sessions/${encodeURIComponent(sessionId)}`);

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Status check failed: ${error}`);
  }

  return response.json();
}

export interface WaitOptions {
  intervalMs?: number;
  timeoutMs?: number;
  signal?: AbortSignal;
}

// parsing runs asynchronously off the s3 upload event, so poll until it lands on ready or error
export async function waitForSession(
  sessionId: string,
  { intervalMs = 2000, timeoutMs = 5 * 60 * 1000, signal }: WaitOptions = {}
): Promise<SessionStatusResponse> {
  const deadline = Date.now() + timeoutMs;

  while (true) {
    if (signal?.aborted) {
      throw new Error("Stopped waiting for the document");
    }

    const result = await fetchSessionStatus(sessionId);
    if (result.status === "READY_FOR_QUERY" || result.status === "ERROR") {
      return result;
    }

    if (Date.now() + intervalMs > deadline) {
      throw new Error("Timed out waiting for the document to finish processing");
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
}

export async function queryRAG(sessionId: string, query: string): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      sessionId,
      query,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Query failed: ${error}`);
  }

  return response.json();
}
