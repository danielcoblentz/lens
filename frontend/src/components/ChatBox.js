import { useState } from "react";
import { queryRAG } from "../services/aws";

function ChatBox({ sessionId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;

    if (!sessionId) {
      alert("Please select an uploaded document first");
      return;
    }

    const userMessage = input;
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await queryRAG(sessionId, userMessage);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.answer },
      ]);
    } catch (error) {
      console.error("Query failed:", error);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${error.message}` },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.messages}>
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              ...styles.message,
              alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
              background: msg.role === "user" ? "#daf1ff" : "#eee",
            }}
          >
            {msg.content}
          </div>
        ))}
      </div>

      <div style={styles.inputRow}>
        <input
          style={styles.input}
          value={input}
          placeholder={sessionId ? "Ask a question..." : "Select a document first"}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !isLoading && handleSend()}
          disabled={isLoading || !sessionId}
        />
        <button
          style={{
            ...styles.button,
            opacity: isLoading || !sessionId ? 0.6 : 1,
          }}
          onClick={handleSend}
          disabled={isLoading || !sessionId}
        >
          {isLoading ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}

const styles = {
  container: {
    width: "250px",
    height: "100vh",
    display: "flex",
    flexDirection: "column",
    borderLeft: "1px solid #ddd",
    boxSizing: "border-box",
  },
  messages: {
    flex: 1,
    padding: "1rem",
    overflowY: "auto",
    display: "flex",
    flexDirection: "column",
    gap: "0.5rem",
  },
  message: {
    padding: "0.5rem 1rem",
    borderRadius: "12px",
    maxWidth: "80%",
  },
  inputRow: {
    display: "flex",
    padding: "0.5rem",
    borderTop: "1px solid #ddd",
  },
  input: {
    flex: 1,
    // inputs default to about 20 characters wide, which pushed the button out of the panel
    minWidth: 0,
    padding: "0.5rem",
  },
  button: {
    marginLeft: "0.5rem",
    padding: "0.5rem 1rem",
  },
};

export default ChatBox;
