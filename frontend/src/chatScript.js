import React, { useEffect, useRef, useState } from 'react';
import './chatStyling.css';

const ChatComponent = () => {
  const chatDisplay = useRef(null);
  const messageInput = useRef(null);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [userMessage, setUserMessage] = useState('');

  const sendMessage = () => {
    const trimmedMessage = userMessage.trim();
    if (!trimmedMessage) return;

    appendMessage(trimmedMessage, 'user');
    setUserMessage('');

    const requestData = {
      question: trimmedMessage,
      history: conversationHistory,
    };

    fetch('http://localhost:5000/ask', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestData),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then((data) => {
        appendMessage(data.answer, 'bot');
        setConversationHistory(data.history);
      })
      .catch((error) => {
        appendMessage('Error', 'bot');
      });
  };

  const appendMessage = (text, sender) => {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender === 'user' ? 'user-message' : 'bot-message');
    messageDiv.textContent = text;
    chatDisplay.current.appendChild(messageDiv);
    chatDisplay.current.scrollTop = chatDisplay.current.scrollHeight;
  };

  useEffect(() => {
    messageInput.current.focus();
  }, []);

  const handleKeyDown = (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="prayer-mat-container">
      <div className="prayer-mat-top-arch">
        <div className="prayer-mat-body">
            <div className="chat-display" ref={chatDisplay} style={{ overflowY: 'auto', height: '400px' }}>
              <div className="message bot-message">Assalamu Alaikum! How can I assist you today?</div>
            </div>
            <div className="chat-input-area"> {/* Uncommented and applied the class */}
              <input
                id="message-input"
                ref={messageInput}
                value={userMessage}
                onChange={(e) => setUserMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your message..."
              />
              <button id="send-button" onClick={sendMessage}>
                Send
              </button>
            </div>
          </div>
        </div>
      </div>
  );
};

export default ChatComponent;
