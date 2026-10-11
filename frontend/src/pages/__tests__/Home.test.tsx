import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Home from "../Home";
import { uploadPDF, waitForSession } from "../../services/aws";
import { SessionStatusResponse } from "../../types";

// react-pdf ships as esm, which jest cannot parse, and these tests only cover the upload flow
jest.mock("../../components/FileViewer", () => () => <div data-testid="file-viewer" />);
jest.mock("../../services/aws");

const mockedUploadPDF = uploadPDF as jest.MockedFunction<typeof uploadPDF>;
const mockedWaitForSession = waitForSession as jest.MockedFunction<typeof waitForSession>;

function pdf(name = "lease.pdf") {
  return new File(["%PDF-1.4"], name, { type: "application/pdf" });
}

function upload(file: File) {
  const input = document.querySelector('input[type="file"]') as HTMLInputElement;
  userEvent.upload(input, file);
}

beforeEach(() => {
  jest.clearAllMocks();
  mockedUploadPDF.mockResolvedValue({ sessionId: "s1" });
});

test("shows processing until the backend reports the document ready", async () => {
  let finish: (result: SessionStatusResponse) => void = () => {};
  mockedWaitForSession.mockReturnValue(new Promise((resolve) => (finish = resolve)));
  render(<Home />);

  upload(pdf());

  expect(await screen.findByText("Processing...")).toBeInTheDocument();
  expect(mockedWaitForSession).toHaveBeenCalledWith("s1", expect.anything());

  finish({ sessionId: "s1", status: "READY_FOR_QUERY" });

  expect(await screen.findByText("Ready")).toBeInTheDocument();
});

test("keeps chat disabled while the selected document is processing, then enables it", async () => {
  let finish: (result: SessionStatusResponse) => void = () => {};
  mockedWaitForSession.mockReturnValue(new Promise((resolve) => (finish = resolve)));
  render(<Home />);

  upload(pdf());
  userEvent.click(await screen.findByText("lease.pdf"));

  expect(screen.getByPlaceholderText("Processing document...")).toBeDisabled();

  finish({ sessionId: "s1", status: "READY_FOR_QUERY" });

  await waitFor(() => expect(screen.getByPlaceholderText("Ask a question...")).toBeEnabled());
});

test("shows the parse error on the badge when processing fails", async () => {
  mockedWaitForSession.mockResolvedValue({
    sessionId: "s1",
    status: "ERROR",
    error: "No text could be extracted from this PDF.",
  });
  render(<Home />);

  upload(pdf());

  const badge = await screen.findByText("Error");
  expect(badge).toHaveAttribute("title", "No text could be extracted from this PDF.");
});
