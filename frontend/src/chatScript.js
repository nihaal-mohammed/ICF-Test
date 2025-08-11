import React, { useEffect, useRef, useState } from "react";
import "./chatStyling.css";

const ChatComponent = () => {
  const chatDisplay = useRef(null);
  const messageInput = useRef(null);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [userMessage, setUserMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [chatDisplayHeight, setChatDisplayHeight] = useState(400);
  const [isExpanded, setIsExpanded] = useState(false);
  const [sentMessages, setSentMessages] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  // 🔹 Added this for resize toggle
  const [isLarge, setIsLarge] = useState(false);

  const baseHeight = 40;
  const maxHeight = 120;

  const adjustLayout = () => {
    const input = messageInput.current;
    if (!input) return;
    input.style.height = "auto";
    const scrollH = input.scrollHeight;

    if (scrollH < maxHeight) {
      input.style.height = `${scrollH}px`;
      input.style.overflowY = "hidden";
      setChatDisplayHeight((isLarge ? 600 : 400) - (scrollH - baseHeight));
    } else {
      input.style.height = `${maxHeight}px`;
      input.style.overflowY = "auto";
      setChatDisplayHeight((isLarge ? 600 : 400) - (maxHeight - baseHeight));
    }
  };

  const appendMessage = (text, sender) => {
    if (!chatDisplay.current) return;
    const div = document.createElement("div");
    div.classList.add("chat-bubble", sender === "user" ? "user-bubble" : "bot-bubble");
    div.textContent = text;
    chatDisplay.current.appendChild(div);
    chatDisplay.current.scrollTop = chatDisplay.current.scrollHeight;
  };

  const sendMessage = () => {
    const msg = userMessage.trim();
    if (!msg || isLoading) return;

    setSentMessages((prev) => [...prev, msg]);
    setHistoryIndex(-1);
    
    appendMessage(msg, "user");
    setUserMessage("");
    adjustLayout();
    setIsLoading(true);

    const loading = document.createElement("div");
    loading.classList.add("chat-bubble", "bot-bubble", "loading-bubble");
    loading.innerHTML = `
      <div class="typing-dots">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>`;
    chatDisplay.current.appendChild(loading);
    chatDisplay.current.scrollTop = chatDisplay.current.scrollHeight;

    fetch("http://localhost:5000/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: msg, history: conversationHistory }),
    })
      .then((res) => res.json())
      .then((data) => {
        chatDisplay.current.removeChild(loading);
        appendMessage(data.answer, "bot");
        setConversationHistory(data.history);
      })
      .catch(() => {
        chatDisplay.current.removeChild(loading);
        appendMessage("Error", "bot");
      })
      .finally(() => setIsLoading(false));
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    } else if (e.key === "ArrowUp") {
    // Navigate up in history
    if (sentMessages.length > 0) {
      e.preventDefault();
      const newIndex =
        historyIndex < sentMessages.length - 1
          ? historyIndex + 1
          : sentMessages.length - 1;
      setHistoryIndex(newIndex);
      setUserMessage(sentMessages[sentMessages.length - 1 - newIndex]);
    }
  } else if (e.key === "ArrowDown") {
    // Navigate down in history
    if (historyIndex > 0) {
      e.preventDefault();
      const newIndex = historyIndex - 1;
      setHistoryIndex(newIndex);
      setUserMessage(sentMessages[sentMessages.length - 1 - newIndex]);
    } else if (historyIndex === 0) {
      e.preventDefault();
      setHistoryIndex(-1);
      setUserMessage("");
    }
  }
};


  useEffect(adjustLayout, [userMessage, isLarge]);

  return (
    <>
      {!isExpanded ? (
        <button
          className="chat-toggle-button"
          onClick={() => setIsExpanded(true)}
          aria-label="Open chat"
        >
          💬
        </button>
      ) : (
        <div
          className="chat-container expanded-chat"
          style={{
            width: isLarge ? "500px" : "360px",
            height: isLarge ? "700px" : "500px"
          }}
        >
          <button
            className="chat-minimize-button"
            onClick={() => setIsExpanded(false)}
            aria-label="Minimize chat"
          >
            ✕
          </button>

          <button
            className="chat-resize-button"
            onClick={() => setIsLarge(!isLarge)}
            aria-label="Resize chat"
          >
          {isLarge ? "-" : "+"}
          </button>

          <div
            className="chat-window"
            ref={chatDisplay}
            style={{ height: `${chatDisplayHeight}px` }}
          >
            <div className="chat-bubble bot-bubble">
              Assalamu Alaikum! How can I help?
            </div>
          </div>

          <div className="input-wrapper">
            <textarea
              ref={messageInput}
              value={userMessage}
              onChange={(e) => setUserMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message..."
              disabled={isLoading}
              rows={1}
            />
            <button onClick={sendMessage} disabled={isLoading} className="send-button">
              Send
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default ChatComponent;