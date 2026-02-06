/**
 * AI Support Dashboard - Base JavaScript
 * Common utilities and functions used across the dashboard
 */

(function() {
    'use strict';

    // ===========================================
    // Configuration
    // ===========================================
    const CONFIG = {
        toastDuration: 3000,
        animationDuration: 300,
        debounceDelay: 250
    };

    // ===========================================
    // Utility Functions
    // ===========================================
    
    /**
     * Get CSRF token from cookies
     * @returns {string|null}
     */
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    /**
     * Get API key from hidden input
     * @returns {string}
     */
    function getApiKey() {
        const apiKeyInput = document.getElementById('api-key-hidden');
        return apiKeyInput ? apiKeyInput.value : 'demo-key';
    }

    /**
     * Format timestamp to relative time
     * @param {string} timestamp
     * @returns {string}
     */
    function formatTime(timestamp) {
        if (!timestamp) return 'Unknown';
        
        try {
            const date = new Date(timestamp);
            const now = new Date();
            const diff = now - date;

            if (diff < 60000) return 'Just now';
            if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
            if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
            return date.toLocaleDateString();
        } catch (e) {
            return 'Unknown';
        }
    }

    /**
     * Escape HTML to prevent XSS
     * @param {string} text
     * @returns {string}
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }

    /**
     * Debounce function
     * @param {Function} func
     * @param {number} wait
     * @returns {Function}
     */
    function debounce(func, wait = CONFIG.debounceDelay) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Throttle function
     * @param {Function} func
     * @param {number} limit
     * @returns {Function}
     */
    function throttle(func, limit) {
        let inThrottle;
        return function executedFunction(...args) {
            if (!inThrottle) {
                func(...args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // ===========================================
    // Toast Notifications
    // ===========================================
    
    /**
     * Show toast notification
     * @param {string} message
     * @param {string} type - 'success', 'error', 'warning', 'info'
     */
    function showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        if (!container) {
            console.warn('Toast container not found');
            return;
        }

        const toast = document.createElement('div');
        
        const colors = {
            'success': 'bg-green-500',
            'error': 'bg-red-500',
            'warning': 'bg-yellow-500',
            'info': 'bg-blue-500'
        };

        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };

        toast.className = `${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg toast`;
        toast.innerHTML = `
            <div class="flex items-center space-x-3">
                <i class="fas fa-${icons[type]}"></i>
                <span>${escapeHtml(message)}</span>
            </div>
        `;

        container.appendChild(toast);

        // Remove toast after duration
        setTimeout(() => {
            toast.classList.add('hiding');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, CONFIG.animationDuration);
        }, CONFIG.toastDuration);
    }

    // ===========================================
    // API Helper
    // ===========================================
    
    /**
     * Make API request with proper headers
     * @param {string} url
     * @param {Object} options
     * @returns {Promise}
     */
    async function apiRequest(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getApiKey()}`,
                'X-CSRFToken': getCookie('csrftoken')
            }
        };

        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };

        try {
            const response = await fetch(url, mergedOptions);
            
            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.message || `HTTP ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Request Error:', error);
            throw error;
        }
    }

    // ===========================================
    // Counter Animation
    // ===========================================
    
    /**
     * Animate counter from current value to target
     * @param {string} elementId
     * @param {number} targetValue
     * @param {number} duration
     */
    function animateCounter(elementId, targetValue, duration = 800) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const currentText = element.textContent.replace(/[^0-9.-]/g, '');
        const start = parseFloat(currentText) || 0;

        // If values are the same, just return
        if (start === targetValue) {
            return;
        }

        const startTime = Date.now();
        const difference = targetValue - start;

        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function (ease-out cubic)
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const current = Math.floor(start + (difference * easeOut));
            
            element.textContent = current;

            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                element.textContent = targetValue;
            }
        };

        requestAnimationFrame(animate);
    }

    // ===========================================
    // Modal Helpers
    // ===========================================
    
    /**
     * Open modal by ID
     * @param {string} modalId
     */
    function openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            document.body.style.overflow = 'hidden';
        }
    }

    /**
     * Close modal by ID
     * @param {string} modalId
     */
    function closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
            document.body.style.overflow = '';
        }
    }

    // ===========================================
    // Copy to Clipboard
    // ===========================================
    
    /**
     * Copy text to clipboard
     * @param {string} text
     * @param {string} successMessage
     */
    async function copyToClipboard(text, successMessage = 'Copied to clipboard') {
        try {
            await navigator.clipboard.writeText(text);
            showToast(successMessage, 'success');
        } catch (error) {
            console.error('Copy failed:', error);
            showToast('Failed to copy', 'error');
        }
    }

    // ===========================================
    // Event Delegation Helper
    // ===========================================
    
    /**
     * Add delegated event listener
     * @param {string} parentSelector
     * @param {string} childSelector
     * @param {string} event
     * @param {Function} callback
     */
    function delegateEvent(parentSelector, childSelector, event, callback) {
        const parent = document.querySelector(parentSelector);
        if (!parent) return;

        parent.addEventListener(event, function(e) {
            const target = e.target.closest(childSelector);
            if (target && parent.contains(target)) {
                callback.call(target, e, target);
            }
        });
    }

    // ===========================================
    // Initialize
    // ===========================================
    
    function init() {
        // Close modals on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                const openModal = document.querySelector('.modal-backdrop.flex, [class*="modal"].flex');
                if (openModal) {
                    openModal.classList.add('hidden');
                    openModal.classList.remove('flex');
                    document.body.style.overflow = '';
                }
            }
        });

        // Close modals on backdrop click
        document.querySelectorAll('[data-modal-backdrop]').forEach(backdrop => {
            backdrop.addEventListener('click', function(e) {
                if (e.target === this) {
                    this.classList.add('hidden');
                    this.classList.remove('flex');
                    document.body.style.overflow = '';
                }
            });
        });
    }

    // Run init when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // ===========================================
    // Export to Global Scope
    // ===========================================
    window.Dashboard = window.Dashboard || {};
    Object.assign(window.Dashboard, {
        // Utilities
        getCookie,
        getApiKey,
        formatTime,
        escapeHtml,
        debounce,
        throttle,
        
        // Toast
        showToast,
        
        // API
        apiRequest,
        
        // Animation
        animateCounter,
        
        // Modals
        openModal,
        closeModal,
        
        // Clipboard
        copyToClipboard,
        
        // Events
        delegateEvent
    });

    // Also expose showToast globally for convenience
    window.showToast = showToast;

})();