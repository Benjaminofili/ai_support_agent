/**
 * AI Support Dashboard - Conversations Page JavaScript
 * Handles conversations list and detail functionality
 */

(function() {
    'use strict';

    // ===========================================
    // Conversations Manager Class
    // ===========================================
    
    class ConversationsManager {
        constructor() {
            this.conversations = [];
            this.currentFilter = 'all';
            this.searchQuery = '';
            this.isLoading = false;
            this.selectedConversation = null;
            
            this.init();
        }

        init() {
            this.bindEvents();
            this.checkUrlHash();
        }

        bindEvents() {
            // Search input
            const searchInput = document.getElementById('conversation-search');
            if (searchInput) {
                searchInput.addEventListener('input', Dashboard.debounce((e) => {
                    this.handleSearch(e.target.value);
                }, 300));
            }

            // Status filter
            const statusFilter = document.getElementById('status-filter');
            if (statusFilter) {
                statusFilter.addEventListener('change', (e) => {
                    this.handleStatusFilter(e.target.value);
                });
            }

            // Close modal on escape
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    this.closeConversationModal();
                }
            });

            // Handle browser back/forward
            window.addEventListener('popstate', () => {
                this.checkUrlHash();
            });
        }

        checkUrlHash() {
            const hash = window.location.hash;
            if (hash && hash.startsWith('#')) {
                const conversationId = hash.substring(1);
                if (conversationId) {
                    this.openConversation(conversationId);
                }
            }
        }

        handleSearch(query) {
            this.searchQuery = query.toLowerCase();
            this.filterConversations();
        }

        handleStatusFilter(status) {
            this.currentFilter = status;
            this.filterConversations();
        }

        filterConversations() {
            const rows = document.querySelectorAll('[data-conversation-row]');
            
            rows.forEach(row => {
                const customerName = row.dataset.customerName?.toLowerCase() || '';
                const customerId = row.dataset.customerId?.toLowerCase() || '';
                const status = row.dataset.status?.toLowerCase() || '';
                const channel = row.dataset.channel?.toLowerCase() || '';

                // Check search query
                const matchesSearch = !this.searchQuery || 
                    customerName.includes(this.searchQuery) || 
                    customerId.includes(this.searchQuery);

                // Check status filter
                const matchesStatus = this.currentFilter === 'all' || 
                    status === this.currentFilter;

                // Show/hide row
                if (matchesSearch && matchesStatus) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });

            // Update visible count
            this.updateVisibleCount();
        }

        updateVisibleCount() {
            const visibleRows = document.querySelectorAll('[data-conversation-row]:not([style*="display: none"])');
            const countElement = document.getElementById('visible-count');
            if (countElement) {
                countElement.textContent = visibleRows.length;
            }
        }

        async openConversation(conversationId) {
            const modal = document.getElementById('conversation-modal');
            const content = document.getElementById('conversation-modal-content');
            
            if (!modal || !content) return;

            // Update URL
            history.pushState(null, '', `#${conversationId}`);

            // Show modal with loading state
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            document.body.style.overflow = 'hidden';

            content.innerHTML = `
                <div class="p-8 text-center">
                    <i class="fas fa-spinner fa-spin text-3xl text-purple-500 mb-4"></i>
                    <p class="text-gray-600">Loading conversation...</p>
                </div>
            `;

            try {
                const response = await fetch(`/api/chat/conversations/${conversationId}/`, {
                    headers: {
                        'Authorization': `Bearer ${Dashboard.getApiKey()}`
                    }
                });

                if (!response.ok) {
                    throw new Error('Failed to load conversation');
                }

                const conversation = await response.json();
                this.selectedConversation = conversation;
                this.renderConversationDetail(conversation);

            } catch (error) {
                console.error('Error loading conversation:', error);
                content.innerHTML = `
                    <div class="p-8 text-center">
                        <i class="fas fa-exclamation-circle text-3xl text-red-500 mb-4"></i>
                        <p class="text-gray-600">Failed to load conversation</p>
                        <button onclick="conversationsManager.closeConversationModal()" 
                                class="mt-4 px-4 py-2 bg-gray-200 rounded-lg hover:bg-gray-300 transition">
                            Close
                        </button>
                    </div>
                `;
            }
        }

        renderConversationDetail(conversation) {
            const content = document.getElementById('conversation-modal-content');
            if (!content) return;

            const channelIcons = {
                'whatsapp': 'fab fa-whatsapp text-green-600',
                'web': 'fas fa-globe text-blue-600',
                'email': 'fas fa-envelope text-purple-600'
            };

            const channelColors = {
                'whatsapp': 'bg-green-100',
                'web': 'bg-blue-100',
                'email': 'bg-purple-100'
            };

            const messages = conversation.messages || [];

            content.innerHTML = `
                <!-- Header -->
                <div class="conversation-detail-header">
                    <div class="flex items-center gap-3">
                        <div class="w-12 h-12 rounded-full ${channelColors[conversation.channel] || 'bg-gray-100'} flex items-center justify-center">
                            <i class="${channelIcons[conversation.channel] || 'fas fa-comment'} text-xl"></i>
                        </div>
                        <div>
                            <h3 class="text-lg font-semibold text-gray-900">
                                ${Dashboard.escapeHtml(conversation.customer_name || conversation.customer_identifier)}
                            </h3>
                            <p class="text-sm text-gray-500">
                                ${Dashboard.escapeHtml(conversation.customer_identifier)}
                            </p>
                        </div>
                    </div>
                    <div class="flex items-center gap-3">
                        <span class="status-badge ${conversation.status}">
                            ${conversation.status}
                        </span>
                        <button onclick="conversationsManager.closeConversationModal()" 
                                class="p-2 hover:bg-gray-100 rounded-lg transition">
                            <i class="fas fa-times text-gray-500"></i>
                        </button>
                    </div>
                </div>

                <!-- Messages -->
                <div class="conversation-detail-body">
                    <div class="messages-container">
                        ${messages.length > 0 ? messages.map(msg => this.renderMessage(msg)).join('') : `
                            <div class="text-center text-gray-500 py-8">
                                <i class="fas fa-comments text-4xl text-gray-300 mb-3"></i>
                                <p>No messages in this conversation</p>
                            </div>
                        `}
                    </div>
                </div>

                <!-- Footer -->
                <div class="conversation-detail-footer">
                    <div class="flex items-center justify-between text-sm text-gray-500">
                        <span>
                            <i class="fas fa-calendar mr-1"></i>
                            Started ${Dashboard.formatTime(conversation.created_at)}
                        </span>
                        <span>
                            <i class="fas fa-comment mr-1"></i>
                            ${messages.length} messages
                        </span>
                    </div>
                </div>
            `;
        }

        renderMessage(message) {
            const isCustomer = message.role === 'user' || message.role === 'customer';
            const isHuman = message.role === 'human_agent';
            
            let bubbleClass = 'customer';
            if (!isCustomer) {
                bubbleClass = isHuman ? 'human' : 'ai';
            }

            const senderLabel = isCustomer ? 'Customer' : (isHuman ? 'Agent' : 'AI Assistant');

            return `
                <div class="message-bubble ${bubbleClass}">
                    <div class="text-xs font-medium mb-1 opacity-75">${senderLabel}</div>
                    <div class="message-content">${Dashboard.escapeHtml(message.content)}</div>
                    <div class="message-time">${Dashboard.formatTime(message.created_at)}</div>
                </div>
            `;
        }

        closeConversationModal() {
            const modal = document.getElementById('conversation-modal');
            if (modal) {
                modal.classList.add('hidden');
                modal.classList.remove('flex');
                document.body.style.overflow = '';
                history.pushState(null, '', window.location.pathname + window.location.search);
            }
            this.selectedConversation = null;
        }

        async deleteConversation(conversationId) {
            if (!confirm('Are you sure you want to delete this conversation? This action cannot be undone.')) {
                return;
            }

            try {
                const response = await fetch(`/api/chat/conversations/${conversationId}/`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${Dashboard.getApiKey()}`,
                        'X-CSRFToken': Dashboard.getCookie('csrftoken')
                    }
                });

                if (response.ok) {
                    Dashboard.showToast('Conversation deleted successfully', 'success');
                    
                    // Remove row from table
                    const row = document.querySelector(`[data-conversation-row][data-id="${conversationId}"]`);
                    if (row) {
                        row.remove();
                    }

                    // Close modal if open
                    this.closeConversationModal();
                    
                    // Update count
                    this.updateVisibleCount();
                } else {
                    throw new Error('Failed to delete conversation');
                }
            } catch (error) {
                console.error('Error deleting conversation:', error);
                Dashboard.showToast('Failed to delete conversation', 'error');
            }
        }

        async updateConversationStatus(conversationId, status) {
            try {
                const response = await fetch(`/api/chat/conversations/${conversationId}/`, {
                    method: 'PATCH',
                    headers: {
                        'Authorization': `Bearer ${Dashboard.getApiKey()}`,
                        'Content-Type': 'application/json',
                        'X-CSRFToken': Dashboard.getCookie('csrftoken')
                    },
                    body: JSON.stringify({ status })
                });

                if (response.ok) {
                    Dashboard.showToast(`Conversation marked as ${status}`, 'success');
                    
                    // Update row status
                    const row = document.querySelector(`[data-conversation-row][data-id="${conversationId}"]`);
                    if (row) {
                        row.dataset.status = status;
                        const badge = row.querySelector('.status-badge');
                        if (badge) {
                            badge.className = `status-badge ${status}`;
                            badge.textContent = status.charAt(0).toUpperCase() + status.slice(1);
                        }
                    }
                } else {
                    throw new Error('Failed to update status');
                }
            } catch (error) {
                console.error('Error updating conversation status:', error);
                Dashboard.showToast('Failed to update status', 'error');
            }
        }

        exportConversation(conversationId) {
            if (!this.selectedConversation) {
                Dashboard.showToast('No conversation loaded', 'error');
                return;
            }

            const conv = this.selectedConversation;
            const messages = conv.messages || [];

            let exportText = `Conversation Export\n`;
            exportText += `${'='.repeat(50)}\n\n`;
            exportText += `Customer: ${conv.customer_name || conv.customer_identifier}\n`;
            exportText += `Channel: ${conv.channel}\n`;
            exportText += `Status: ${conv.status}\n`;
            exportText += `Started: ${new Date(conv.created_at).toLocaleString()}\n`;
            exportText += `\n${'='.repeat(50)}\n\n`;
            exportText += `Messages:\n\n`;

            messages.forEach(msg => {
                const sender = msg.role === 'user' ? 'Customer' : (msg.role === 'human_agent' ? 'Agent' : 'AI');
                const time = new Date(msg.created_at).toLocaleString();
                exportText += `[${time}] ${sender}:\n${msg.content}\n\n`;
            });

            // Create and download file
            const blob = new Blob([exportText], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `conversation-${conversationId}.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            Dashboard.showToast('Conversation exported', 'success');
        }
    }

    // ===========================================
    // Global Functions
    // ===========================================
    
    function viewConversation(conversationId) {
        if (window.conversationsManager) {
            window.conversationsManager.openConversation(conversationId);
        }
    }

    function deleteConversation(conversationId) {
        if (window.conversationsManager) {
            window.conversationsManager.deleteConversation(conversationId);
        }
    }

    function closeConversationModal() {
        if (window.conversationsManager) {
            window.conversationsManager.closeConversationModal();
        }
    }

    function exportConversation(conversationId) {
        if (window.conversationsManager) {
            window.conversationsManager.exportConversation(conversationId);
        }
    }

    // ===========================================
    // Initialize
    // ===========================================
    
    function init() {
        window.conversationsManager = new ConversationsManager();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // ===========================================
    // Export to Global Scope
    // ===========================================
    
    window.viewConversation = viewConversation;
    window.deleteConversation = deleteConversation;
    window.closeConversationModal = closeConversationModal;
    window.exportConversation = exportConversation;

})();