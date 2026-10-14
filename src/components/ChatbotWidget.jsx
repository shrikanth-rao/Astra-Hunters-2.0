
import { useState } from "react";
import { Bot, X, Send, Sparkles } from "lucide-react";
import "./chatbot.css";

export default function ChatbotWidget() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hi! I'm your SpeakKaro.AI assistant. Ask me about speech analysis, speaking pace, filler words or improving your presentation.",
    },
  ]);

  function sendMessage(event) {
    event.preventDefault();

    const question = input.trim();
    if (!question) return;

    setMessages((previous) => [
      ...previous,
      { role: "user", text: question },
      {
        role: "assistant",
        text: "I'm currently in demo mode. Once connected to an AI service, I'll be able to answer your question about public speaking in more detail.",
      },
    ]);

    setInput("");
  }

  return (
    <div className="speech-assistant">
      {open && (
        <section
          className="assistant-panel"
          aria-label="SpeakKaro AI chat"
        >
          <header className="assistant-header">
            <div className="assistant-heading-icon">
              <Sparkles size={19} />
            </div>
            <div className="assistant-heading-text">
              <strong>SpeakKaro Assistant</strong>
              <span>Speech coaching companion</span>
            </div>
            <button
              className="assistant-close"
              onClick={() => setOpen(false)}
              aria-label="Close chat"
            >
              <X size={19} />
            </button>
          </header>

          <div className="assistant-messages" aria-live="polite">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`assistant-message ${message.role}`}
              >
                {message.text}
              </div>
            ))}
          </div>

          <form className="assistant-input-row" onSubmit={sendMessage}>
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask about your speech..."
              aria-label="Your message"
            />
            <button type="submit" aria-label="Send message">
              <Send size={17} />
            </button>
          </form>
        </section>
      )}

      <button
        className={`assistant-orb ${open ? "orb-active" : ""}`}
        onClick={() => setOpen((previous) => !previous)}
        aria-label={open ? "Close AI assistant" : "Open AI assistant"}
        aria-expanded={open}
      >
        <span className="orb-halo" />
        <span className="orb-shine" />
        <span className="orb-inner">
          {open ? <X size={29} /> : <Bot size={31} />}
        </span>
        {!open && <span className="orb-sparkle"><Sparkles size={14} /></span>}
      </button>
    </div>
  );
}
