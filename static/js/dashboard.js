/**
 * AI Support Dashboard - Dashboard Overview JavaScript
 * Handles the main dashboard page functionality
 */

(function() {
    'use strict';

    // ===========================================
    // Dashboard Overview Class
    // ===========================================
    
    class DashboardOverview {
        constructor() {
            this.conversations = [];
            this.documents = [];
            this.conversationChart = null;
            this.channelChart = null;
            this.dataLoaded = false;
            this.chartDataCache = null;
            this.isLoading = false;
            
            this.init();
        }

        init() {
            this.loadDashboardData();
            this.initCharts();
            this.bindEvents();
        }

        bindEvents() {
            // Refresh button (if exists)
            const refreshBtn = document.getElementById('refresh-dashboard');
            if (refreshBtn) {
                refreshBtn.addEventListener('click', () => this.loadDashboardData());
            }

            // Time range selector
            const timeRangeSelect = document.getElementById('time-range-select');
            if (timeRangeSelect) {
                timeRangeSelect.addEventListener('change', (e) => {
                    this.handleTimeRangeChange(e.target.value);
                });
            }
        }

        async loadDashboardData() {
            if (this.isLoading) return;
            
            this.isLoading = true;
            
            try {
                const [conversationsData, documentsData] = await Promise.all([
                    this.fetchConversations(),
                    this.fetchDocuments()
                ]);

                this.conversations = conversationsData || [];
                this.documents = documentsData || [];
                this.dataLoaded = true;

                this.updateStats();
                this.renderRecentConversations();
                
                // Calculate and cache chart data
                this.chartDataCache = {
                    trend: this.calculateTrendData(),
                    channels: this.getChannelDistribution()
                };
                this.updateCharts();

            } catch (error) {
                console.error('Error loading dashboard data:', error);
                this.dataLoaded = true;
                this.renderRecentConversations();
            } finally {
                this.isLoading = false;
            }
        }

        async fetchConversations() {
            try {
                const response = await fetch('/api/chat/conversations/', {
                    headers: {
                        'Authorization': `Bearer ${Dashboard.getApiKey()}`
                    }
                });
                
                if (response.ok) {
                    return await response.json();
                }
                console.warn('Failed to load conversations');
                return [];
            } catch (error) {
                console.error('Error fetching conversations:', error);
                return [];
            }
        }

        async fetchDocuments() {
            try {
                const response = await fetch('/api/knowledge/documents/', {
                    headers: {
                        'Authorization': `Bearer ${Dashboard.getApiKey()}`
                    }
                });
                
                if (response.ok) {
                    return await response.json();
                }
                console.warn('Failed to load documents');
                return [];
            } catch (error) {
                console.error('Error fetching documents:', error);
                return [];
            }
        }

        updateStats() {
            // Total conversations
            const totalConv = this.conversations.length;
            Dashboard.animateCounter('total-conversations', totalConv);

            // Active today
            const today = new Date().toDateString();
            const activeToday = this.conversations.filter(c => {
                if (!c.updated_at) return false;
                try {
                    return new Date(c.updated_at).toDateString() === today && c.status === 'active';
                } catch (e) {
                    return false;
                }
            }).length;
            Dashboard.animateCounter('active-today', activeToday);

            // Total documents
            const totalDocs = this.documents.length;
            Dashboard.animateCounter('total-documents', totalDocs);

            // Average response time
            const avgResponse = this.calculateAvgResponseTime();
            const avgResponseEl = document.getElementById('avg-response');
            if (avgResponseEl) {
                avgResponseEl.textContent = avgResponse;
            }
        }

        calculateAvgResponseTime() {
            if (this.conversations.length === 0) return '--';
            // Would need actual message timing data
            return '2.3s';
        }

        renderRecentConversations() {
            const container = document.getElementById('recent-conversations');
            if (!container) return;

            const recentConversations = this.conversations
                .sort((a, b) => {
                    const dateA = new Date(a.updated_at || a.created_at);
                    const dateB = new Date(b.updated_at || b.created_at);
                    return dateB - dateA;
                })
                .slice(0, 5);

            if (recentConversations.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-comments empty-state-icon"></i>
                        <p class="font-semibold text-lg">No conversations yet</p>
                        <p class="text-sm text-gray-400 mt-2">Start by testing your chat widget or email</p>
                    </div>
                `;
                return;
            }

            const channelIcons = {
                'web': 'fa-globe channel-icon web',
                'whatsapp': 'fa-whatsapp channel-icon whatsapp',
                'email': 'fa-envelope channel-icon email'
            };

            container.innerHTML = recentConversations.map(conv => `
                <div class="conversation-item p-4 cursor-pointer" data-conversation-id="${conv.id}">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-3">
                            <div class="conversation-avatar">
                                <i class="fas fa-user text-gray-600"></i>
                            </div>
                            <div>
                                <div class="flex items-center space-x-2">
                                    <p class="font-semibold text-gray-800">
                                        ${Dashboard.escapeHtml(conv.customer_name || conv.customer_identifier || 'Anonymous')}
                                    </p>
                                    <i class="fas ${channelIcons[conv.channel] || 'fa-comment text-gray-500'}"></i>
                                </div>
                                <p class="text-sm text-gray-600 line-clamp-1">
                                    ${Dashboard.escapeHtml(conv.last_message || 'No messages yet')}
                                </p>
                            </div>
                        </div>
                        <div class="text-right">
                            <span class="conversation-status ${conv.status === 'active' ? 'active' : 'closed'}">
                                ${conv.status}
                            </span>
                            <p class="text-xs text-gray-500 mt-1">
                                ${Dashboard.formatTime(conv.updated_at || conv.created_at)}
                            </p>
                        </div>
                    </div>
                </div>
            `).join('');

            // Add click handlers
            container.querySelectorAll('[data-conversation-id]').forEach(item => {
                item.addEventListener('click', () => {
                    const id = item.dataset.conversationId;
                    window.location.href = `/dashboard/conversations/#${id}`;
                });
            });
        }

        initCharts() {
            // Wait for Chart.js to load
            if (typeof Chart === 'undefined') {
                console.warn('Chart.js not loaded');
                return;
            }

            this.initConversationChart();
            this.initChannelChart();
        }

        initConversationChart() {
            const ctx = document.getElementById('conversation-chart');
            if (!ctx) return;

            this.conversationChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: this.getLast7Days(),
                    datasets: [{
                        label: 'Conversations',
                        data: [0, 0, 0, 0, 0, 0, 0],
                        borderColor: 'rgb(139, 92, 246)',
                        backgroundColor: 'rgba(139, 92, 246, 0.1)',
                        tension: 0.4,
                        fill: true,
                        borderWidth: 3,
                        pointBackgroundColor: 'rgb(139, 92, 246)',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        pointRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            padding: 12,
                            cornerRadius: 8
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1,
                                font: {
                                    size: 12
                                }
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)'
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            },
                            ticks: {
                                font: {
                                    size: 12
                                }
                            }
                        }
                    }
                }
            });
        }

        initChannelChart() {
            const ctx = document.getElementById('channel-chart');
            if (!ctx) return;

            this.channelChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Website', 'WhatsApp', 'Email'],
                    datasets: [{
                        data: [1, 0, 0],
                        backgroundColor: [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(139, 92, 246, 0.8)'
                        ],
                        borderWidth: 0,
                        hoverOffset: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '60%',
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 20,
                                font: {
                                    size: 12,
                                    weight: 'bold'
                                },
                                usePointStyle: true,
                                pointStyle: 'circle'
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            padding: 12,
                            cornerRadius: 8
                        }
                    }
                }
            });
        }

        updateCharts() {
            if (this.conversationChart && this.chartDataCache) {
                this.conversationChart.data.datasets[0].data = this.chartDataCache.trend;
                this.conversationChart.update('none');
            }

            if (this.channelChart && this.chartDataCache) {
                const channelData = this.chartDataCache.channels;
                this.channelChart.data.labels = channelData.map(d => d.name);
                this.channelChart.data.datasets[0].data = channelData.map(d => d.count);
                this.channelChart.update('none');
            }
        }

        getLast7Days() {
            const days = [];
            for (let i = 6; i >= 0; i--) {
                const date = new Date();
                date.setDate(date.getDate() - i);
                days.push(date.toLocaleDateString('en-US', { weekday: 'short' }));
            }
            return days;
        }

        calculateTrendData() {
            const counts = new Array(7).fill(0);
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            this.conversations.forEach(conv => {
                try {
                    const convDate = new Date(conv.created_at || conv.updated_at);
                    convDate.setHours(0, 0, 0, 0);
                    const diffTime = today - convDate;
                    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
                    
                    if (diffDays >= 0 && diffDays < 7) {
                        counts[6 - diffDays]++;
                    }
                } catch (e) {
                    // Skip invalid dates
                }
            });

            return counts;
        }

        getChannelDistribution() {
            const channelCounts = { web: 0, whatsapp: 0, email: 0 };

            this.conversations.forEach(conv => {
                if (channelCounts.hasOwnProperty(conv.channel)) {
                    channelCounts[conv.channel]++;
                }
            });

            const total = channelCounts.web + channelCounts.whatsapp + channelCounts.email;
            if (total === 0) {
                channelCounts.web = 1;
            }

            return [
                { name: 'Website', count: channelCounts.web },
                { name: 'WhatsApp', count: channelCounts.whatsapp },
                { name: 'Email', count: channelCounts.email }
            ];
        }

        handleTimeRangeChange(range) {
            // Would reload data based on time range
            console.log('Time range changed to:', range);
            this.loadDashboardData();
        }
    }

    // ===========================================
    // Page Actions
    // ===========================================
    
    function testChatWidget() {
        window.open('/chat/widget/', '_blank', 'width=400,height=600');
    }

    function openEmailTestModal() {
        Dashboard.openModal('email-test-modal');
    }

    function closeEmailTestModal(event) {
        if (!event || event.target.id === 'email-test-modal') {
            Dashboard.closeModal('email-test-modal');
        }
    }

    async function sendTestEmail(event) {
        event.preventDefault();

        const recipient = document.getElementById('test-email-recipient').value;
        const subject = document.getElementById('test-email-subject').value;
        const body = document.getElementById('test-email-body').value;

        const sendButton = document.querySelector('#email-test-form button[type="submit"]');
        const sendText = document.getElementById('email-send-text');
        const sendSpinner = document.getElementById('email-send-spinner');

        sendButton.disabled = true;
        sendText.classList.add('hidden');
        sendSpinner.classList.remove('hidden');

        try {
            const response = await fetch('/api/webhooks/email/test/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    from_email: recipient,
                    subject: subject,
                    body: body
                })
            });

            if (response.ok) {
                Dashboard.showToast('Test email queued successfully!', 'success');
                closeEmailTestModal();

                // Reload dashboard data after delay
                setTimeout(() => {
                    if (window.dashboardOverview) {
                        window.dashboardOverview.loadDashboardData();
                    }
                }, 2000);
            } else {
                const error = await response.json();
                Dashboard.showToast('Failed: ' + (error.message || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('Email test error:', error);
            Dashboard.showToast('Error sending test email', 'error');
        } finally {
            sendButton.disabled = false;
            sendText.classList.remove('hidden');
            sendSpinner.classList.add('hidden');
        }
    }

    // ===========================================
    // Initialize
    // ===========================================
    
    function init() {
        // Initialize dashboard overview
        window.dashboardOverview = new DashboardOverview();
    }

    // Wait for DOM and Chart.js
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // ===========================================
    // Export to Global Scope
    // ===========================================
    
    window.testChatWidget = testChatWidget;
    window.openEmailTestModal = openEmailTestModal;
    window.closeEmailTestModal = closeEmailTestModal;
    window.sendTestEmail = sendTestEmail;

})();