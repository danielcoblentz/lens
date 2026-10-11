import React, { useState, useRef, useEffect, ChangeEvent } from "react";
import Sidebar from "../components/Sidebar";
import FileViewer from "../components/FileViewer";
import ChatBox from "../components/ChatBox";
import { uploadPDF, waitForSession } from "../services/aws";
import { FileMeta, UploadStatus } from "../types";

function Home() {
  const [filesMeta, setFilesMeta] = useState<FileMeta[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedName, setSelectedName] = useState<string | null>(null);
  // keyed by file name
  const [uploadStatus, setUploadStatus] = useState<Record<string, UploadStatus>>({});
  // the file objects themselves, which react-pdf needs to render
  const filesRef = useRef<File[]>([]);
  // stops any status polling when the page goes away
  const pollingRef = useRef(new AbortController());

  useEffect(() => {
    const polling = pollingRef.current;
    return () => polling.abort();
  }, []);

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

        const result = await waitForSession(sessionId, { signal: pollingRef.current.signal });
        setUploadStatus((prev) => ({
          ...prev,
          [file.name]:
            result.status === "READY_FOR_QUERY"
              ? { progress: 100, status: "ready", sessionId }
              : { progress: 100, status: "error", sessionId, error: result.error },
        }));
      } catch (error) {
        if (pollingRef.current.signal.aborted) return;
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
    setSelectedName(fileMeta.name);
  };

  // chat only opens once the selected document can be queried, and follows its status as it changes
  const selectedStatus = selectedName ? uploadStatus[selectedName] : undefined;
  const chatSessionId = selectedStatus?.status === "ready" ? selectedStatus.sessionId : null;

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

      <ChatBox sessionId={chatSessionId} processing={selectedStatus?.status === "processing"} />

    </div>
  );
}

export default Home;
