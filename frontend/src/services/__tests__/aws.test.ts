import { fetchSessionStatus, waitForSession } from "../aws";
import { SessionStatus } from "../../types";

const fetchMock = jest.fn();

beforeEach(() => {
  fetchMock.mockReset();
  global.fetch = fetchMock;
});

function statusResponse(status: SessionStatus, error?: string) {
  return {
    ok: true,
    json: async () => ({ sessionId: "s1", status, ...(error ? { error } : {}) }),
  };
}

describe("fetchSessionStatus", () => {
  test("requests the session status route", async () => {
    fetchMock.mockResolvedValue(statusResponse("PROCESSING"));

    const result = await fetchSessionStatus("s1");

    expect(fetchMock).toHaveBeenCalledWith("/sessions/s1");
    expect(result.status).toBe("PROCESSING");
  });

  test("throws with the response body when the request fails", async () => {
    fetchMock.mockResolvedValue({ ok: false, text: async () => "Invalid sessionId" });

    await expect(fetchSessionStatus("s1")).rejects.toThrow("Status check failed: Invalid sessionId");
  });
});

describe("waitForSession", () => {
  test("polls until the session is ready", async () => {
    fetchMock
      .mockResolvedValueOnce(statusResponse("AWAITING_UPLOAD"))
      .mockResolvedValueOnce(statusResponse("PROCESSING"))
      .mockResolvedValueOnce(statusResponse("READY_FOR_QUERY"));

    const result = await waitForSession("s1", { intervalMs: 1 });

    expect(result.status).toBe("READY_FOR_QUERY");
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  test("returns the error when parsing fails", async () => {
    fetchMock
      .mockResolvedValueOnce(statusResponse("PROCESSING"))
      .mockResolvedValueOnce(statusResponse("ERROR", "No text could be extracted from this PDF."));

    const result = await waitForSession("s1", { intervalMs: 1 });

    expect(result).toEqual({
      sessionId: "s1",
      status: "ERROR",
      error: "No text could be extracted from this PDF.",
    });
  });

  test("gives up after the timeout", async () => {
    fetchMock.mockResolvedValue(statusResponse("PROCESSING"));

    await expect(waitForSession("s1", { intervalMs: 5, timeoutMs: 20 })).rejects.toThrow(
      "Timed out waiting for the document to finish processing"
    );
  });

  test("stops when the signal is aborted", async () => {
    const controller = new AbortController();
    controller.abort();

    await expect(waitForSession("s1", { signal: controller.signal })).rejects.toThrow(
      "Stopped waiting for the document"
    );
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
