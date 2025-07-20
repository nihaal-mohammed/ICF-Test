const chatDisplay = document.getElementById('chat-display');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');

sendButton.addEventListener('click', () => {
  const userMessage = messageInput.value.trim();
  if (!userMessage) return;

  appendMessage(userMessage, 'user');
  messageInput.value = '';

  // Fake chatbot response
  setTimeout(() => {
    const response = generateResponse(userMessage);
    appendMessage(response, 'bot');
  }, 600);
});

function appendMessage(text, sender) {
  const messageDiv = document.createElement('div');
  messageDiv.classList.add('message', sender === 'user' ? 'user-message' : 'bot-message');
  messageDiv.textContent = text;
  chatDisplay.appendChild(messageDiv);
  chatDisplay.scrollTop = chatDisplay.scrollHeight;
}

function generateResponse(input) {
  // Replace this logic with AI later
  return "I'm here to help you with your prayers!";
}