import React from "react";
import { FileMeta, UploadPhase, UploadStatus } from "../types";

// shows where a file is in the upload, parse, ready pipeline
interface StatusBadgeProps {
  status: UploadPhase;
  progress: number;
  error?: string;
}

function StatusBadge({ status, progress, error }: StatusBadgeProps) {
  const getStatusStyle = () => {
    switch (status) {
      case "uploading":
        return { background: "#ffd700", color: "#000" };
      case "processing":
        return { background: "#87ceeb", color: "#000" };
      case "ready":
        return { background: "#90ee90", color: "#000" };
      case "error":
        return { background: "#ff6b6b", color: "#fff" };
      default:
        return { background: "#ddd", color: "#000" };
    }
  };

  const getStatusText = () => {
    switch (status) {
      case "uploading":
        return `${progress}%`;
      case "processing":
        return "Processing...";
      case "ready":
        return "Ready";
      case "error":
        return "Error";
      default:
        return "";
    }
  };

  return (
    <span style={{ ...styles.badge, ...getStatusStyle() }} title={error}>
      {getStatusText()}
    </span>
  );
}

// holds files the user will upload and later review the contents
interface SidebarProps {
  files: FileMeta[];
  onSelect: (file: FileMeta) => void;
  uploadStatus?: Record<string, UploadStatus>;
}

function Sidebar({ files, onSelect, uploadStatus = {} }: SidebarProps) {
  return (
    <div style={styles.sidebar}>
      <h2 style={styles.title}>Lens</h2>
      <h3 style={styles.header}>Files</h3>

      {/* scrollable section if we have many files uploaded */}
      <div style={styles.list}>
        {files.map((file, idx) => {
          const status = uploadStatus[file.name];
          return (
            <div
              key={idx}
              style={styles.item}
              onClick={() => onSelect(file)}
            >
              <div style={styles.fileName}>{file.name}</div>
              {status && (
                <StatusBadge status={status.status} progress={status.progress} error={status.error} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  sidebar: {
    width: "250px",
    height: "100vh",
    display: "flex",
    flexDirection: "column",
    background: "#f4f4f4",
    padding: "1rem",
    borderRight: "1px solid #ddd",
    boxSizing: "border-box"
  },
  title: {
    margin: 0,
    marginBottom: "0.5rem",
  },
  header: {
    margin: 0,
    marginBottom: "0.75rem",
    fontSize: "1rem"
  },
  list: {
    flex: 1,                
    overflowY: "auto",       
    display: "flex",
    flexDirection: "column",
    gap: "0.5rem",
    paddingRight: "0.25rem"
  },
  item: {
    padding: "0.5rem",
    background: "#fff",
    borderRadius: "4px",
    border: "1px solid #ccc",
    cursor: "pointer",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "0.5rem"
  },
  fileName: {
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    flex: 1
  },
  badge: {
    padding: "0.2rem 0.5rem",
    borderRadius: "4px",
    fontSize: "0.75rem",
    fontWeight: "bold",
    whiteSpace: "nowrap"
  }
};

export default Sidebar;
