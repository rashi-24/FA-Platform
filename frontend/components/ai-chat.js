/**
 * AI Chat Widget - Capital Companion
 * Floating chat widget available on all pages
 * SECURITY: Filters PII requests on backend
 */

class AIChatWidget {
    constructor() {
        this.isOpen = false;
        this.messages = this.loadMessages();
        this.API_BASE_URL = 'http://localhost:8000';
        this.init();
    }

    init() {
        // Create chat widget HTML
        this.createWidget();
        // Attach event listeners
        this.attachEventListeners();
    }

    createWidget() {
        const widgetHTML = `
            <!-- Chat Button -->
            <div id="ai-chat-button" class="ai-chat-button">
                <span class="chat-icon">💬</span>
                <span class="chat-text">Capital Companion</span>
            </div>

            <!-- Chat Panel -->
            <div id="ai-chat-panel" class="ai-chat-panel">
                <div class="chat-header">
                    <h3>💼 Capital Companion</h3>
                    <p>Your AI Financial Assistant</p>
                    <button id="ai-chat-close" class="chat-close">×</button>
                </div>

                <div id="chat-messages" class="chat-messages">
                    <div class="chat-message bot">
                        <div class="message-content">
                            👋 Hello! I'm Capital Companion, your AI financial assistant.
                            I can help answer general financial questions and provide insights.
                        </div>
                        <div class="message-disclaimer">
                            Note: For privacy, I cannot access specific client information.
                        </div>
                    </div>
                </div>

                <div class="chat-input-container">
                    <input
                        type="text"
                        id="chat-input"
                        placeholder="Ask a financial question..."
                        autocomplete="off"
                    />
                    <button id="chat-send" class="chat-send-btn">
                        <span>Send</span>
                    </button>
                </div>

                <div class="chat-quick-actions">
                    <button class="quick-action" data-question="How many policies are expiring this month?">
                        Expiring Policies
                    </button>
                    <button class="quick-action" data-question="What is term insurance?">
                        About Term Insurance
                    </button>
                    <button class="quick-action" data-question="Explain SIP benefits">
                        SIP Benefits
                    </button>
                </div>
            </div>
        `;

        // Add to document body
        document.body.insertAdjacentHTML('beforeend', widgetHTML);
    }

    attachEventListeners() {
        // Toggle chat panel
        document.getElementById('ai-chat-button').addEventListener('click', () => this.toggleChat());
        document.getElementById('ai-chat-close').addEventListener('click', () => this.toggleChat());

        // Send message on button click
        document.getElementById('chat-send').addEventListener('click', () => this.sendMessage());

        // Send message on Enter key
        document.getElementById('chat-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });

        // Quick action buttons
        document.querySelectorAll('.quick-action').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const question = e.target.dataset.question;
                document.getElementById('chat-input').value = question;
                this.sendMessage();
            });
        });

        // Load previous messages
        this.renderMessages();
    }

    toggleChat() {
        this.isOpen = !this.isOpen;
        const panel = document.getElementById('ai-chat-panel');
        const button = document.getElementById('ai-chat-button');

        if (this.isOpen) {
            panel.classList.add('open');
            button.classList.add('hidden');
            document.getElementById('chat-input').focus();
        } else {
            panel.classList.remove('open');
            button.classList.remove('hidden');
        }
    }

    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();

        if (!message) return;

        // Add user message to UI
        this.addMessage('user', message);
        input.value = '';

        // Show typing indicator
        this.showTyping();

        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`${this.API_BASE_URL}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ message })
            });

            const data = await response.json();

            // Remove typing indicator
            this.hideTyping();

            if (response.ok) {
                if (data.is_blocked) {
                    // PII request was blocked
                    this.addMessage('bot', data.response, true);
                } else {
                    this.addMessage('bot', data.response);
                }
            } else {
                this.addMessage('bot', 'Sorry, I encountered an error. Please try again.', true);
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.hideTyping();
            this.addMessage('bot', 'Network error. Please check your connection.', true);
        }
    }

    addMessage(type, content, isWarning = false) {
        const messagesContainer = document.getElementById('chat-messages');

        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type} ${isWarning ? 'warning' : ''}`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;

        messageDiv.appendChild(contentDiv);
        messagesContainer.appendChild(messageDiv);

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Save to messages history
        this.messages.push({ type, content, timestamp: new Date().toISOString() });
        this.saveMessages();
    }

    showTyping() {
        const messagesContainer = document.getElementById('chat-messages');
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'chat-message bot';
        typingDiv.innerHTML = '<div class="message-content typing"><span></span><span></span><span></span></div>';
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    hideTyping() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    renderMessages() {
        // Render previous messages from localStorage
        const messagesContainer = document.getElementById('chat-messages');

        // Keep welcome message, add history after it
        this.messages.slice(-10).forEach(msg => {  // Last 10 messages only
            const messageDiv = document.createElement('div');
            messageDiv.className = `chat-message ${msg.type}`;

            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = msg.content;

            messageDiv.appendChild(contentDiv);
            messagesContainer.appendChild(messageDiv);
        });

        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    loadMessages() {
        const saved = localStorage.getItem('ai_chat_messages');
        return saved ? JSON.parse(saved) : [];
    }

    saveMessages() {
        // Keep only last 50 messages
        if (this.messages.length > 50) {
            this.messages = this.messages.slice(-50);
        }
        localStorage.setItem('ai_chat_messages', JSON.stringify(this.messages));
    }
}

// Initialize chat widget when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new AIChatWidget();
    });
} else {
    new AIChatWidget();
}
