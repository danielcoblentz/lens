import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Sidebar from "../Sidebar";
import { FileMeta, UploadPhase, UploadStatus } from "../../types";

function file(name: string): FileMeta {
  return { name, size: 1024, type: "application/pdf", lastModified: 0 };
}

function status(phase: UploadPhase, progress = 100): UploadStatus {
  return { status: phase, progress, sessionId: null };
}

const files = [file("lease.pdf"), file("nda.pdf")];

test("renders the file list", () => {
  render(<Sidebar files={files} onSelect={() => {}} />);

  expect(screen.getByText("lease.pdf")).toBeInTheDocument();
  expect(screen.getByText("nda.pdf")).toBeInTheDocument();
});

test("renders nothing in the list when there are no files", () => {
  render(<Sidebar files={[]} onSelect={() => {}} />);

  expect(screen.getByText("Files")).toBeInTheDocument();
  expect(screen.queryByText("lease.pdf")).not.toBeInTheDocument();
});

test("calls onSelect with the clicked file", async () => {
  const onSelect = jest.fn();
  render(<Sidebar files={files} onSelect={onSelect} />);

  await userEvent.click(screen.getByText("nda.pdf"));

  expect(onSelect).toHaveBeenCalledWith(files[1]);
});

test("shows upload progress while a file is uploading", () => {
  render(
    <Sidebar
      files={files}
      onSelect={() => {}}
      uploadStatus={{ "lease.pdf": status("uploading", 42) }}
    />
  );

  expect(screen.getByText("42%")).toBeInTheDocument();
});

test("shows each terminal status label", () => {
  render(
    <Sidebar
      files={[file("a.pdf"), file("b.pdf"), file("c.pdf")]}
      onSelect={() => {}}
      uploadStatus={{
        "a.pdf": status("processing"),
        "b.pdf": status("ready"),
        "c.pdf": status("error"),
      }}
    />
  );

  expect(screen.getByText("Processing...")).toBeInTheDocument();
  expect(screen.getByText("Ready")).toBeInTheDocument();
  expect(screen.getByText("Error")).toBeInTheDocument();
});

test("shows no badge for a file with no status", () => {
  render(<Sidebar files={files} onSelect={() => {}} uploadStatus={{}} />);

  expect(screen.queryByText("Ready")).not.toBeInTheDocument();
  expect(screen.queryByText("Processing...")).not.toBeInTheDocument();
});
