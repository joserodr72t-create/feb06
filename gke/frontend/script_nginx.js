// Configuration - Empty string means requests go through nginx proxy
const API_URL = '';

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');
const clearButton = document.getElementById('clearChat');
const statusElement = document.getElementById('status');

// State
let isWaitingForResponse = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeChat();
    setupEventListeners();
    autoResizeTextarea();
});

function initializeChat() {
    setStatus('connected', 'Connected');
    userInput.disabled = false;
    sendButton.disabled = false;
    userInput.focus();
}

function setupEventListeners() {
    // Send on Enter (without Shift)
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Send button click
    sendButton.addEventListener('click', sendMessage);

    // Clear chat
    clearButton.addEventListener('click', clearChat);

    // Enable/disable send button based on input
    userInput.addEventListener('input', () => {
        sendButton.disabled = !userInput.value.trim() || isWaitingForResponse;
        autoResizeTextarea();
    });
}

function autoResizeTextarea() {
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 150) + 'px';
}

function setStatus(type, text) {
    statusElement.textContent = text;
    statusElement.className = 'status';
    if (type) {
        statusElement.classList.add(type);
    }
}

function addMessage(content, type = 'bot') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = type === 'user' ? '👤' : '🤖';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Parse content for basic formatting
    contentDiv.innerHTML = formatMessage(content);

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    scrollToBottom();
}

function formatMessage(content) {
    // Convert line breaks to <br>
    let formatted = content.replace(/\n/g, '<br>');
    
    // Convert **bold** to <strong>
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Convert `code` to <code>
    formatted = formatted.replace(/`(.*?)`/g, '<code>$1</code>');
    
    // Wrap in paragraph
    return `<p>${formatted}</p>`;
}

function showTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.id = 'typingIndicator';
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = '🤖';
    
    const dots = document.createElement('div');
    dots.className = 'typing-dots';
    dots.innerHTML = '<span></span><span></span><span></span>';
    
    indicator.appendChild(avatar);
    indicator.appendChild(dots);
    chatMessages.appendChild(indicator);
    
    scrollToBottom();
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendMessage() {
    const message = userInput.value.trim();
    
    if (!message || isWaitingForResponse) return;

    // Update state
    isWaitingForResponse = true;
    userInput.disabled = true;
    sendButton.disabled = true;
    setStatus('connected', 'Thinking...');

    // Add user message
    addMessage(message, 'user');
    
    // Clear input
    userInput.value = '';
    userInput.style.height = 'auto';
    
    // Show typing indicator
    showTypingIndicator();

    try {
        const response = await fetch(`${API_URL}/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ input: message }),
        });

        removeTypingIndicator();

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.text();
        addMessage(data, 'bot');
        setStatus('connected', 'Connected');

    } catch (error) {
        console.error('Error:', error);
        removeTypingIndicator();
        addMessage('Sorry, I encountered an error connecting to the server. Please try again.', 'error');
        setStatus('error', 'Connection error');
    } finally {
        isWaitingForResponse = false;
        userInput.disabled = false;
        sendButton.disabled = false;
        userInput.focus();
    }
}

function clearChat() {
    // Keep only the welcome message
    const messages = chatMessages.querySelectorAll('.message');
    messages.forEach((msg, index) => {
        if (index > 0) {
            msg.remove();
        }
    });
    
    // Also remove any typing indicator
    removeTypingIndicator();
    
    userInput.focus();
}

// Handle visibility change (pause/resume)
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && !isWaitingForResponse) {
        setStatus('connected', 'Connected');
    }
});
