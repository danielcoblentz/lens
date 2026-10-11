import React, { useState, useRef, ChangeEvent } from "react";
import Sidebar from "../components/Sidebar";
import FileViewer from "../components/FileViewer";
import ChatBox from "../components/ChatBox";
import { uploadPDF } from "../services/aws";
import { FileMeta, UploadStatus } from "../types";

function Home() {
  const [filesMeta, setFilesMeta] = useState<FileMeta[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  // keyed by file name
  const [uploadStatus, setUploadStatus] = useState<Record<string, UploadStatus>>({});
  // the file objects themselves, which react-pdf needs to render
  const filesRef = useRef<File[]>([]);

  const handleUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files || []);

    for (const file of selected) {
      // the parser only handles pdfs
      if (file.type !== "application/pdf") {
        alert(`${file.name} is not a PDF file`);
        continue;
      }

      filesRef.current = [...filesRef.current, file];

      const meta = {
        name: file.name,
        size: file.size,
        type: file.type,
        lastModified: file.lastModified,
      };
      setFilesMeta((prev) => [...prev, meta]);

      setUploadStatus((prev) => ({
        ...prev,
        [file.name]: { progress: 0, status: "uploading", sessionId: null },
      }));

      try {
        const { sessionId } = await uploadPDF(file, (progress) => {
          setUploadStatus((prev) => ({
            ...prev,
            [file.name]: { ...prev[file.name], progress },
          }));
        });

        // the s3 upload event starts llamaParse on the backend
        setUploadStatus((prev) => ({
          ...prev,
          [file.name]: { progress: 100, status: "processing", sessionId },
        }));

        // the backend has no status endpoint yet, so assume parsing finishes within 10 seconds
        setTimeout(() => {
          setUploadStatus((prev) => ({
            ...prev,
            [file.name]: { ...prev[file.name], status: "ready" },
          }));
        }, 10000);

      } catch (error) {
        console.error("Upload failed:", error);
        setUploadStatus((prev) => ({
          ...prev,
          [file.name]: {
            progress: 0,
            status: "error",
            sessionId: null,
            error: error instanceof Error ? error.message : String(error),
          },
        }));
      }
    }
  };

  const handleSelect = (fileMeta: FileMeta) => {
    const actualFile = filesRef.current.find(
      (f) =>
        f.name === fileMeta.name &&
        f.size === fileMeta.size &&
        f.lastModified === fileMeta.lastModified);

    setSelectedFile(actualFile || null);

    const status = uploadStatus[fileMeta.name];
    // a file still uploading has no session yet, so chat stays disabled
    setActiveSessionId(status?.sessionId || null);
  };

  return (
    <div style={{ display: "flex", height: "100vh" }}>

      <Sidebar files={filesMeta} onSelect={handleSelect} uploadStatus={uploadStatus} />

      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <div style={{ padding: "2rem" }}>
          <h1>Upload Files</h1>
          <input type="file" multiple accept=".pdf" onChange={handleUpload} />
        </div>

        <div style={{ flex: 1, overflow: "auto" }}>
          <FileViewer selectedFile={selectedFile} />
        </div>
      </div>

      <ChatBox sessionId={activeSessionId} />

    </div>
  );
}

export default Home;
