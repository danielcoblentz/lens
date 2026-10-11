// AWS API service for communicating with Lambda endpoints
import { PresignResponse, QueryResponse } from "../types";

const API_BASE = process.env.REACT_APP_API_BASE || "";

export type UploadProgressCallback = (percentComplete: number) => void;

/**
 * Get a presigned URL for uploading a PDF to S3
 * Also creates a session in DynamoDB with AWAITING_UPLOAD status
 */
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

/**
 * Upload a file directly to S3 using a presigned URL
 * Uses XMLHttpRequest because fetch does not report upload progress
 */
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

/**
 * Upload a PDF file to AWS
 * 1. Gets presigned URL from Lambda (creates session)
 * 2. Uploads file directly to S3
 * 3. S3 upload triggers LlamaParse Lambda automatically
 */
export async function uploadPDF(
  file: File,
  onProgress?: UploadProgressCallback
): Promise<{ sessionId: string }> {
  const { sessionId, uploadUrl } = await getPresignedUploadUrl();
  await uploadFileToS3(uploadUrl, file, onProgress);
  return { sessionId };
}

/**
 * Query the RAG pipeline with a question
 */
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
