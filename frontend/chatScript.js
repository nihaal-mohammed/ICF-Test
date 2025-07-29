const chatDisplay = document.getElementById('chat-display');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');

let conversationHistory = []; 

sendButton.addEventListener('click', async () => {
  const userMessage = messageInput.value.trim();
  if (!userMessage) return;

  appendMessage(userMessage, 'user');
  messageInput.value = '';

  const requestData = {
    question: userMessage,
    history: conversationHistory 
  };

  try {
    const response = await fetch('http://localhost:5000/ask', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestData)
    });

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    const data = await response.json();
    appendMessage(data.answer, 'bot');

    conversationHistory = data.history; 
  } catch (error) {
    appendMessage('Error', 'bot');
  }
});

function appendMessage(text, sender) {
  const messageDiv = document.createElement('div');
  messageDiv.classList.add('message', sender === 'user' ? 'user-message' : 'bot-message');
  messageDiv.textContent = text;
  chatDisplay.appendChild(messageDiv);
  chatDisplay.scrollTop = chatDisplay.scrollHeight;
}
