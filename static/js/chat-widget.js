// Chat Widget JavaScript - Enhanced functionality

class ChatWidget {
    constructor(config = {}) {
        this.config = {
            apiKey: config.apiKey || null,
            apiUrl: config.apiUrl || '/api/chat/message/',
            placeholder: config.placeholder || 'Type your message...',
            title: config.title || 'AI Support Assistant',
            subtitle: config.subtitle || 'Usually responds instantly',
            primaryColor: config.primaryColor || '#3b82f6',
            position: config.position || 'bottom-right',
            autoOpen: config.autoOpen || false,
            welcomeMessage: config.welcomeMessage || 'Hello! I\'m your AI support assistant. How can I help you today?',
            ...config
        };
        
        this.isOpen = false;
        this.conversationId = null;
        this.messages = [];
        this.isTyping = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        
        this.init();
    }
    
    init() {
        this.createWidget();
        this.setupEventListeners();
        this.loadConversationHistory();
        
        if (this.config.autoOpen) {
            setTimeout(() => this.openChat(), 1000);
        }
    }
    
    createWidget() {
        // Create main widget container
        const widget = document.createElement('div');
        widget.id = 'ai-chat-widget';
        widget.className = `fixed ${this.getPositionClasses()} z-50`;
        
        widget.innerHTML = `
            <!-- Chat Button -->
            <button id="chat-toggle" class="chat-button bg-blue-600 hover:bg-blue-700 text-white rounded-full p-4 shadow-lg transition-all duration-300 hover:scale-110">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
                </svg>
                <span class="notification-dot absolute top-0 right-0 w-3 h-3 bg-red-500 rounded-full hidden"></span>
            </button>
            
            <!-- Chat Window -->
            <div id="chat-window" class="chat-window hidden absolute bottom-20 right-0 w-96 h-[600px] bg-white rounded-lg shadow-2xl flex flex-col overflow-hidden">
                <!-- Chat Header -->
                <div class="chat-header bg-blue-600 text-white p-4 flex items-center justify-between">
                    <div class="flex items-center space-x-3">
                        <div class="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                            </svg>
                        </div>
                        <div>
                            <h3 class="font-semibold">${this.config.title}</h3>
                            <p class="text-xs text-blue-100">${this.config.subtitle}</p>
                        </div>
                    </div>
                    <div class="flex items-center space-x-2">
                        <button id="chat-clear" class="hover:bg-blue-700 rounded-full p-1 transition-colors" title="Clear conversation">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                            </svg>
                        </button>
                        <button id="chat-minimize" class="hover:bg-blue-700 rounded-full p-1 transition-colors" title="Minimize">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4"></path>
                            </svg>
                        </button>
                        <button id="chat-close" class="hover:bg-blue-700 rounded-full p-1 transition-colors" title="Close">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                        </button>
                    </div>
                </div>
                
                <!-- Chat Messages -->
                <div id="chat-messages" class="chat-messages flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 custom-scrollbar">
                    <!-- Messages will be loaded here -->
                </div>
                
                <!-- Typing Indicator -->
                <div id="typing-indicator" class="typing-indicator hidden px-4 py-2">
                    <div class="flex items-center space-x-2">
                        <div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                            <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                            </svg>
                        </div>
                        <div class="bg-white rounded-lg p-3 shadow-sm">
                            <div class="typing-dots flex space-x-1">
                                <span class="w-2 h-2 bg-gray-400 rounded-full"></span>
                                <span class="w-2 h-2 bg-gray-400 rounded-full"></span>
                                <span class="w-2 h-2 bg-gray-400 rounded-full"></span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Chat Input -->
                <div class="chat-input-container border-t border-gray-200 p-4 bg-white">
                    <form id="chat-form" class="flex items-center space-x-2">
                        <button type="button" id="chat-attach" class="text-gray-400 hover:text-gray-600 transition-colors" title="Attach file">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"></path>
                            </svg>
                        </button>
                        <input 
                            type="text" 
                            id="chat-input" 
                            placeholder="${this.config.placeholder}" 
                            class="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            autocomplete="off"
                        >
                        <button 
                            type="submit" 
                            id="send-button"
                            class="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-full p-2 transition-colors"
                        >
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                            </svg>
                        </button>
                    </form>
                    <input type="file" id="file-input" class="hidden" accept=".pdf,.txt,.doc,.docx">
                </div>
            </div>
        `;
        
        document.body.appendChild(widget);
        
        // Apply custom color if provided
        if (this.config.primaryColor !== '#3b82f6') {
            this.applyCustomColors();
        }
    }
    
    getPositionClasses() {
        const positions = {
            'bottom-right': 'bottom-4 right-4',
            'bottom-left': 'bottom-4 left-4',
            'top-right': 'top-4 right-4',
            'top-left': 'top-4 left-4'
        };
        return positions[this.config.position] || positions['bottom-right'];
    }
    
    applyCustomColors() {
        const style = document.createElement('style');
        style.textContent = `
            #ai-chat-widget .chat-button,
            #ai-chat-widget .chat-header,
            #ai-chat-widget #send-button {
                background-color: ${this.config.primaryColor} !important;
            }
            #ai-chat-widget .chat-button:hover,
            #ai-chat-widget .chat-header button:hover,
            #ai-chat-widget #send-button:hover {
                background-color: ${this.adjustColor(this.config.primaryColor, -20)} !important;
            }
            #ai-chat-widget #chat-input:focus {
                border-color: ${this.config.primaryColor} !important;
                --tw-ring-color: ${this.config.primaryColor} !important;
            }
        `;
        document.head.appendChild(style);
    }
    
    adjustColor(color, amount) {
        const num = parseInt(color.replace('#', ''), 16);
        const r = Math.max(0, Math.min(255, (num >> 16) + amount));
        const g = Math.max(0, Math.min(255, ((num >> 8) & 0x00FF) + amount));
        const b = Math.max(0, Math.min(255, (num & 0x0000FF) + amount));
        return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`;
    }
    
    setupEventListeners() {
        // Chat controls
        document.getElementById('chat-toggle').addEventListener('click', () => this.toggleChat());
        document.getElementById('chat-close').addEventListener('click', () => this.closeChat());
        document.getElementById('chat-minimize').addEventListener('click', () => this.minimizeChat());
        document.getElementById('chat-clear').addEventListener('click', () => this.clearConversation());
        
        // Form submission
        document.getElementById('chat-form').addEventListener('submit', (e) => this.sendMessage(e));
        
        // File attachment
        document.getElementById('chat-attach').addEventListener('click', () => {
            document.getElementById('file-input').click();
        });
        
        document.getElementById('file-input').addEventListener('change', (e) => {
            this.handleFileAttachment(e.target.files[0]);
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.closeChat();
            }
            if (e.ctrlKey && e.key === 'm' && !this.isOpen) {
                e.preventDefault();
                this.openChat();
            }
        });
        
        // Handle window resize
        window.addEventListener('resize', () => this.handleResize());
    }
    
    toggleChat() {
        if (this.isOpen) {
            this.closeChat();
        } else {
            this.openChat();
        }
    }
    
    openChat() {
        const chatWindow = document.getElementById('chat-window');
        chatWindow.classList.remove('hidden');
        chatWindow.classList.add('slide-in-up');
        this.isOpen = true;
        
        // Focus input
        setTimeout(() => {
            document.getElementById('chat-input').focus();
        }, 300);
        
        // Hide notification dot
        document.querySelector('.notification-dot').classList.add('hidden');
        
        this.emit('chat:opened');
    }
    
    closeChat() {
        const chatWindow = document.getElementById('chat-window');
        chatWindow.classList.add('hidden');
        this.isOpen = false;
        this.emit('chat:closed');
    }
    
    minimizeChat() {
        this.closeChat();
    }
    
    clearConversation() {
        if (confirm('Are you sure you want to clear this conversation?')) {
            this.messages = [];
            this.conversationId = null;
            this.renderMessages();
            this.saveConversationHistory();
            this.emit('conversation:cleared');
        }
    }
    
    async sendMessage(e) {
        e.preventDefault();
        
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message || this.isTyping) return;
        
        // Add user message
        this.addMessage(message, 'customer');
        input.value = '';
        
        // Show typing indicator
        this.showTypingIndicator();
        this.isTyping = true;
        
        try {
            const response = await this.makeRequest(this.config.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.config.apiKey}`
                },
                body: JSON.stringify({
                    message: message,
                    conversation_id: this.conversationId
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Update conversation ID
            if (data.conversation_id) {
                this.conversationId = data.conversation_id;
            }
            
            // Add AI response
            this.addMessage(data.response, 'assistant');
            
            // Reset reconnect attempts on success
            this.reconnectAttempts = 0;
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
            
            // Handle reconnection
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                setTimeout(() => {
                    this.sendMessage(new Event('submit'));
                }, 1000 * this.reconnectAttempts);
            }
        } finally {
            this.hideTypingIndicator();
            this.isTyping = false;
        }
    }
    
    handleFileAttachment(file) {
        if (!file) return;
        
        // Validate file
        const validTypes = ['application/pdf', 'text/plain', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        const maxSize = 10 * 1024 * 1024; // 10MB
        
        if (!validTypes.includes(file.type)) {
            alert('Please upload a PDF, TXT, or DOC file.');
            return;
        }
        
        if (file.size > maxSize) {
            alert('File size must be less than 10MB.');
            return;
        }
        
        // Add file message
        this.addMessage(`📎 ${file.name} (${this.formatFileSize(file.size)})`, 'customer');
        
        // TODO: Implement file upload
        this.addMessage('File upload functionality coming soon!', 'assistant');
        
        // Clear file input
        document.getElementById('file-input').value = '';
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    addMessage(content, role) {
        const message = {
            id: Date.now(),
            role,
            content,
            timestamp: new Date().toISOString()
        };
        
        this.messages.push(message);
        this.renderMessage(message);
        this.saveConversationHistory();
        
        // Scroll to bottom
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        this.emit('message:added', message);
    }
    
    renderMessage(message) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-bubble flex items-start space-x-2 ${message.role === 'customer' ? 'flex-row-reverse space-x-reverse' : ''}`;
        messageDiv.dataset.messageId = message.id;
        
        if (message.role === 'customer') {
            messageDiv.innerHTML = `
                <div class="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center flex-shrink-0">
                    <svg class="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                    </svg>
                </div>
                <div class="bg-blue-600 text-white rounded-lg p-3 max-w-[80%] shadow-sm">
                    <p class="text-sm">${this.escapeHtml(message.content)}</p>
                    <p class="text-xs text-blue-100 mt-1">${this.formatTime(message.timestamp)}</p>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                    </svg>
                </div>
                <div class="bg-white rounded-lg p-3 max-w-[80%] shadow-sm">
                    <p class="text-sm text-gray-800">${this.escapeHtml(message.content)}</p>
                    <p class="text-xs text-gray-500 mt-1">${this.formatTime(message.timestamp)}</p>
                </div>
            `;
        }
        
        messagesContainer.appendChild(messageDiv);
    }
    
    renderMessages() {
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.innerHTML = '';
        
        if (this.messages.length === 0) {
            // Show welcome message
            this.addMessage(this.config.welcomeMessage, 'assistant');
        } else {
            this.messages.forEach(message => this.renderMessage(message));
        }
    }
    
    showTypingIndicator() {
        document.getElementById('typing-indicator').classList.remove('hidden');
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    hideTypingIndicator() {
        document.getElementById('typing-indicator').classList.add('hidden');
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    saveConversationHistory() {
        try {
            localStorage.setItem('ai_chat_messages', JSON.stringify(this.messages));
            if (this.conversationId) {
                localStorage.setItem('ai_chat_conversation_id', this.conversationId);
            }
        } catch (error) {
            console.error('Error saving conversation history:', error);
        }
    }
    
    loadConversationHistory() {
        try {
            const savedMessages = localStorage.getItem('ai_chat_messages');
            const savedConversationId = localStorage.getItem('ai_chat_conversation_id');
            
            if (savedMessages) {
                this.messages = JSON.parse(savedMessages);
                this.renderMessages();
            }
            
            if (savedConversationId) {
                this.conversationId = savedConversationId;
            }
        } catch (error) {
            console.error('Error loading conversation history:', error);
        }
    }
    
    handleResize() {
        if (window.innerWidth < 768 && this.isOpen) {
            const chatWindow = document.getElementById('chat-window');
            chatWindow.style.width = '100vw';
            chatWindow.style.height = '100vh';
            chatWindow.style.bottom = '0';
            chatWindow.style.right = '0';
            chatWindow.style.borderRadius = '0';
        }
    }
    
    async makeRequest(url, options) {
        // Add timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000);
        
        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            throw error;
        }
    }
    
    emit(event, data) {
        if (this.config.onEvent) {
            this.config.onEvent(event, data);
        }
        
        // Also dispatch as custom event
        const customEvent = new CustomEvent(`chat:${event}`, { detail: data });
        document.dispatchEvent(customEvent);
    }
    
    // Public API methods
    showNotification() {
        const dot = document.querySelector('.notification-dot');
        dot.classList.remove('hidden');
    }
    
    destroy() {
        const widget = document.getElementById('ai-chat-widget');
        if (widget) {
            widget.remove();
        }
    }
}

// Auto-initialization
window.AIChatWidget = ChatWidget;

// Initialize if config is provided globally
if (window.CHAT_WIDGET_CONFIG) {
    document.addEventListener('DOMContentLoaded', () => {
        new ChatWidget(window.CHAT_WIDGET_CONFIG);
    });
}
