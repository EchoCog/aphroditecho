const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-message');

function addMessage(message, isUser = false, code = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${isUser ? 'user-message' : 'bot-message'}`;
    
    // Handle regular text message
    if (typeof message === 'string') {
        messageDiv.textContent = message;
    } else {
        messageDiv.textContent = 'Error: Invalid message format';
    }
    
    // Add code block if provided
    if (code && !isUser) {
        const codeBlock = document.createElement('pre');
        codeBlock.style.marginTop = '10px';
        codeBlock.style.background = '#1a1a1a';
        codeBlock.style.padding = '10px';
        codeBlock.style.borderRadius = '4px';
        codeBlock.style.color = '#f8f9fa';
        codeBlock.style.overflowX = 'auto';
        codeBlock.textContent = code;
        
        // Separate message div for code to maintain bubble style
        const codeDiv = document.createElement('div');
        codeDiv.className = 'chat-message bot-message code-block';
        codeDiv.style.marginTop = '5px';
        codeDiv.appendChild(codeBlock);
        
        // Add both to chat
        chatMessages.appendChild(messageDiv);
        chatMessages.appendChild(codeDiv);
    } else {
        chatMessages.appendChild(messageDiv);
    }
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;

    addMessage(message, true);
    chatInput.value = '';

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: message })
        });
        const data = await response.json();
        
        // Update visualization if state data is provided
        if (data.state) {
            if (typeof updateVisualization === 'function') {
                updateVisualization(data.state);
            }
        }
        
        // Check if there's code to display
        if (data.code) {
            addMessage(data.response, false, data.code);
        } else {
            addMessage(data.response);
        }
    } catch (error) {
        console.error('Chat error:', error);
        addMessage('Error: Unable to get response from the chatbot');
    }
}

sendButton.addEventListener('click', sendMessage);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});
