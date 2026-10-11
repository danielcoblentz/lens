import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ChatBox from "../ChatBox";
import { queryRAG } from "../../services/aws";

jest.mock("../../services/aws");

const mockedQueryRAG = queryRAG as jest.MockedFunction<typeof queryRAG>;

function answer(text: string) {
  return { sessionId: "session-1", answer: text };
}

beforeEach(() => {
  jest.clearAllMocks();
});

describe("ChatBox without a selected document", () => {
  test("disables the input and button", () => {
    render(<ChatBox sessionId={null} />);

    expect(screen.getByPlaceholderText("Select a document first")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
  });

  test("does not call the backend", async () => {
    render(<ChatBox sessionId={null} />);

    await userEvent.click(screen.getByRole("button", { name: "Send" }));

    expect(queryRAG).not.toHaveBeenCalled();
  });
});

describe("ChatBox while the selected document is processing", () => {
  test("says so and stays disabled", () => {
    render(<ChatBox sessionId={null} processing />);

    expect(screen.getByPlaceholderText("Processing document...")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
  });
});

describe("ChatBox with a selected document", () => {
  test("enables the input once a session exists", () => {
    render(<ChatBox sessionId="session-1" />);

    expect(screen.getByPlaceholderText("Ask a question...")).toBeEnabled();
    expect(screen.getByRole("button", { name: "Send" })).toBeEnabled();
  });

  test("sends the question and renders the answer", async () => {
    mockedQueryRAG.mockResolvedValue(answer("Either party may terminate on 30 days notice."));
    render(<ChatBox sessionId="session-1" />);

    await userEvent.type(
      screen.getByPlaceholderText("Ask a question..."),
      "What is the termination clause?"
    );
    await userEvent.click(screen.getByRole("button", { name: "Send" }));

    expect(queryRAG).toHaveBeenCalledWith("session-1", "What is the termination clause?");
    expect(await screen.findByText("What is the termination clause?")).toBeInTheDocument();
    expect(
      await screen.findByText("Either party may terminate on 30 days notice.")
    ).toBeInTheDocument();
  });

  test("clears the input after sending", async () => {
    mockedQueryRAG.mockResolvedValue(answer("ok"));
    render(<ChatBox sessionId="session-1" />);

    const input = screen.getByPlaceholderText("Ask a question...");
    await userEvent.type(input, "Who are the parties?");
    await userEvent.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => expect(input).toHaveValue(""));
  });

  test("ignores an empty or whitespace-only question", async () => {
    render(<ChatBox sessionId="session-1" />);

    await userEvent.type(screen.getByPlaceholderText("Ask a question..."), "   ");
    await userEvent.click(screen.getByRole("button", { name: "Send" }));

    expect(queryRAG).not.toHaveBeenCalled();
  });

  test("sends on the Enter key", async () => {
    mockedQueryRAG.mockResolvedValue(answer("ok"));
    render(<ChatBox sessionId="session-1" />);

    await userEvent.type(
      screen.getByPlaceholderText("Ask a question..."),
      "Any indemnity?{enter}"
    );

    await waitFor(() => expect(queryRAG).toHaveBeenCalledWith("session-1", "Any indemnity?"));
  });

  test("shows the error message when the query fails", async () => {
    mockedQueryRAG.mockRejectedValue(new Error("No chunks found"));
    jest.spyOn(console, "error").mockImplementation(() => {});
    render(<ChatBox sessionId="session-1" />);

    await userEvent.type(screen.getByPlaceholderText("Ask a question..."), "What now?");
    await userEvent.click(screen.getByRole("button", { name: "Send" }));

    expect(await screen.findByText("Error: No chunks found")).toBeInTheDocument();
  });
});
