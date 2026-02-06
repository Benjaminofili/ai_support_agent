/**
 * AI Support Dashboard - Upload Page JavaScript
 * Handles document upload functionality
 */

(function() {
    'use strict';

    // ===========================================
    // Configuration
    // ===========================================
    
    const CONFIG = {
        // API endpoints - match your Django Ninja routes
        apiEndpoint: '/api/knowledge/documents/upload/',
        documentsEndpoint: '/api/knowledge/documents/',
        maxFileSize: 10 * 1024 * 1024, // 10MB
        allowedExtensions: ['.pdf', '.docx', '.txt', '.csv', '.json', '.md', '.markdown'],
        pollingInterval: 3000 // 3 seconds
    };

    // ===========================================
    // Upload Manager Class
    // ===========================================
    
    class UploadManager {
        constructor() {
            this.selectedFile = null;
            this.isUploading = false;
            this.currentTab = 'file';
            this.documents = [];
            this.pollingIntervals = {};
            
            this.init();
        }

        init() {
            this.cacheElements();
            
            // Check if API key is available
            const apiKey = this.getApiKey();
            if (!apiKey) {
                console.warn('No API key found. Upload functionality may not work.');
            }
            
            this.bindEvents();
            this.loadDocuments();
        }

        getApiKey() {
            const apiKeyInput = document.getElementById('api-key-hidden');
            const key = apiKeyInput ? apiKeyInput.value : '';
            
            if (!key) {
                console.error('API key not found in hidden input');
            }
            
            return key;
        }

        cacheElements() {
            // Upload zone
            this.uploadZone = document.getElementById('upload-zone');
            this.fileInput = document.getElementById('file-input');
            this.filePreview = document.getElementById('file-preview');
            
            // Form elements
            this.uploadForm = document.getElementById('upload-form');
            this.titleInput = document.getElementById('document-title');
            this.contentInput = document.getElementById('document-content');
            this.submitBtn = document.getElementById('submit-btn');
            this.submitText = document.getElementById('submit-text');
            this.submitSpinner = document.getElementById('submit-spinner');
            
            // Tabs
            this.tabButtons = document.querySelectorAll('[data-upload-tab]');
            this.tabContents = document.querySelectorAll('[data-tab-content]');
            
            // Progress
            this.progressContainer = document.getElementById('upload-progress');
            this.progressBar = document.getElementById('progress-bar-fill');
            this.progressText = document.getElementById('progress-text');
            
            // Documents list
            this.documentsList = document.getElementById('documents-list');
            this.documentsCount = document.getElementById('documents-count');
        }

        bindEvents() {
            // File input change
            if (this.fileInput) {
                this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
            }

            // Upload zone events
            if (this.uploadZone) {
                this.uploadZone.addEventListener('click', (e) => {
                    // Don't trigger if clicking on the file preview remove button
                    if (!e.target.closest('.file-preview-remove')) {
                        this.fileInput?.click();
                    }
                });
                this.uploadZone.addEventListener('dragover', (e) => this.handleDragOver(e));
                this.uploadZone.addEventListener('dragleave', (e) => this.handleDragLeave(e));
                this.uploadZone.addEventListener('drop', (e) => this.handleDrop(e));
            }

            // Form submission
            if (this.uploadForm) {
                this.uploadForm.addEventListener('submit', (e) => this.handleSubmit(e));
            }

            // Tab switching
            this.tabButtons.forEach(btn => {
                btn.addEventListener('click', () => this.switchTab(btn.dataset.uploadTab));
            });

            // Title input auto-fill
            if (this.titleInput) {
                this.titleInput.addEventListener('focus', () => this.autoFillTitle());
            }
        }

        // ===========================================
        // Tab Management
        // ===========================================

        switchTab(tabName) {
            this.currentTab = tabName;

            // Update tab buttons
            this.tabButtons.forEach(btn => {
                btn.classList.toggle('active', btn.dataset.uploadTab === tabName);
            });

            // Update tab contents
            this.tabContents.forEach(content => {
                content.classList.toggle('active', content.dataset.tabContent === tabName);
            });

            // Clear file selection when switching tabs
            if (tabName === 'paste') {
                this.clearFileSelection();
            }
        }

        // ===========================================
        // File Handling
        // ===========================================

        handleDragOver(e) {
            e.preventDefault();
            e.stopPropagation();
            this.uploadZone.classList.add('drag-over');
        }

        handleDragLeave(e) {
            e.preventDefault();
            e.stopPropagation();
            this.uploadZone.classList.remove('drag-over');
        }

        handleDrop(e) {
            e.preventDefault();
            e.stopPropagation();
            this.uploadZone.classList.remove('drag-over');

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.processFile(files[0]);
            }
        }

        handleFileSelect(e) {
            const files = e.target.files;
            if (files.length > 0) {
                this.processFile(files[0]);
            }
        }

        processFile(file) {
            // Validate file size
            if (file.size > CONFIG.maxFileSize) {
                this.showToast(`File too large. Maximum size is ${this.formatFileSize(CONFIG.maxFileSize)}`, 'error');
                return;
            }

            // Validate file type
            const ext = this.getFileExtension(file.name);
            if (!CONFIG.allowedExtensions.includes(ext)) {
                this.showToast(`Invalid file type. Allowed: ${CONFIG.allowedExtensions.join(', ')}`, 'error');
                return;
            }

            this.selectedFile = file;
            this.renderFilePreview(file);
            this.uploadZone.classList.add('has-file');
            
            // Auto-fill title if empty
            if (this.titleInput && !this.titleInput.value.trim()) {
                this.titleInput.value = this.getFileNameWithoutExtension(file.name);
            }
        }

        renderFilePreview(file) {
            if (!this.filePreview) return;

            const ext = this.getFileExtension(file.name).replace('.', '');
            const iconClass = this.getFileIcon(ext);

            this.filePreview.innerHTML = `
                <div class="file-preview">
                    <div class="file-preview-icon ${ext}">
                        <i class="fas ${iconClass}"></i>
                    </div>
                    <div class="file-preview-info">
                        <div class="file-preview-name">${this.escapeHtml(file.name)}</div>
                        <div class="file-preview-size">${this.formatFileSize(file.size)}</div>
                    </div>
                    <button type="button" class="file-preview-remove" onclick="event.stopPropagation(); uploadManager.clearFileSelection()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
            this.filePreview.style.display = 'block';
        }

        clearFileSelection() {
            this.selectedFile = null;
            if (this.fileInput) this.fileInput.value = '';
            if (this.filePreview) {
                this.filePreview.innerHTML = '';
                this.filePreview.style.display = 'none';
            }
            if (this.uploadZone) {
                this.uploadZone.classList.remove('has-file');
            }
        }

        autoFillTitle() {
            if (this.selectedFile && this.titleInput && !this.titleInput.value.trim()) {
                this.titleInput.value = this.getFileNameWithoutExtension(this.selectedFile.name);
            }
        }

        // ===========================================
        // Form Submission
        // ===========================================

        async handleSubmit(e) {
            e.preventDefault();

            if (this.isUploading) return;

            // Get API key
            const apiKey = this.getApiKey();
            if (!apiKey) {
                this.showToast('API key not found. Please refresh the page.', 'error');
                return;
            }

            // Validate
            const title = this.titleInput?.value.trim();
            if (!title) {
                this.showToast('Please enter a document title', 'error');
                this.titleInput?.focus();
                return;
            }

            if (this.currentTab === 'file' && !this.selectedFile) {
                this.showToast('Please select a file to upload', 'error');
                return;
            }

            if (this.currentTab === 'paste') {
                const content = this.contentInput?.value.trim();
                if (!content) {
                    this.showToast('Please enter or paste some content', 'error');
                    this.contentInput?.focus();
                    return;
                }
            }

            // Start upload
            this.setUploadingState(true);
            this.showProgress(0, 'Preparing upload...');

            try {
                const formData = new FormData();
                formData.append('title', title);

                if (this.currentTab === 'file' && this.selectedFile) {
                    formData.append('file', this.selectedFile);
                } else if (this.currentTab === 'paste') {
                    formData.append('content', this.contentInput.value.trim());
                }

                this.showProgress(30, 'Uploading...');

                const response = await fetch(CONFIG.apiEndpoint, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${apiKey}`
                        // Note: Don't set Content-Type for FormData, browser sets it with boundary
                    },
                    body: formData
                });

                this.showProgress(70, 'Processing response...');

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || data.detail || 'Upload failed');
                }

                this.showProgress(100, 'Complete!');

                this.showToast(data.message || 'Document uploaded successfully!', 'success');

                // Reset form
                this.resetForm();

                // Reload documents list
                await this.loadDocuments();

                // Start polling for processing status
                if (data.id) {
                    this.startStatusPolling(data.id);
                }

            } catch (error) {
                console.error('Upload error:', error);
                this.showToast(error.message || 'Failed to upload document', 'error');
                this.hideProgress();
            } finally {
                this.setUploadingState(false);
            }
        }

        setUploadingState(isUploading) {
            this.isUploading = isUploading;

            if (this.submitBtn) {
                this.submitBtn.disabled = isUploading;
            }
            if (this.submitText) {
                this.submitText.textContent = isUploading ? 'Uploading...' : 'Upload Document';
            }
            if (this.submitSpinner) {
                this.submitSpinner.classList.toggle('hidden', !isUploading);
            }
        }

        showProgress(percent, text) {
            if (this.progressContainer) {
                this.progressContainer.classList.add('show');
            }
            if (this.progressBar) {
                this.progressBar.style.width = `${percent}%`;
            }
            if (this.progressText) {
                this.progressText.textContent = text;
            }
        }

        hideProgress() {
            if (this.progressContainer) {
                this.progressContainer.classList.remove('show');
            }
        }

        resetForm() {
            this.clearFileSelection();
            if (this.titleInput) this.titleInput.value = '';
            if (this.contentInput) this.contentInput.value = '';
            
            setTimeout(() => this.hideProgress(), 2000);
        }

        // ===========================================
        // Documents List
        // ===========================================

        async loadDocuments() {
            const apiKey = this.getApiKey();
            if (!apiKey) {
                console.warn('No API key, cannot load documents');
                return;
            }

            try {
                const response = await fetch(CONFIG.documentsEndpoint, {
                    headers: {
                        'Authorization': `Bearer ${apiKey}`
                    }
                });

                if (!response.ok) {
                    if (response.status === 401) {
                        console.error('Unauthorized - invalid API key');
                    }
                    throw new Error('Failed to load documents');
                }

                this.documents = await response.json();
                this.renderDocuments();

                // Start polling for any processing documents
                this.documents.forEach(doc => {
                    if (doc.status === 'pending' || doc.status === 'processing') {
                        this.startStatusPolling(doc.id);
                    }
                });

            } catch (error) {
                console.error('Error loading documents:', error);
                this.renderDocumentsError();
            }
        }

        renderDocuments() {
            if (!this.documentsList) return;

            // Update count
            if (this.documentsCount) {
                this.documentsCount.textContent = this.documents.length;
            }

            if (this.documents.length === 0) {
                this.documentsList.innerHTML = `
                    <div class="documents-empty">
                        <div class="documents-empty-icon">
                            <i class="fas fa-file-alt"></i>
                        </div>
                        <h3 class="documents-empty-title">No documents yet</h3>
                        <p class="documents-empty-text">Upload your first document to get started</p>
                    </div>
                `;
                return;
            }

            this.documentsList.innerHTML = this.documents.map(doc => this.renderDocumentItem(doc)).join('');
        }

        renderDocumentsError() {
            if (!this.documentsList) return;
            
            this.documentsList.innerHTML = `
                <div class="documents-empty">
                    <div class="documents-empty-icon">
                        <i class="fas fa-exclamation-triangle text-yellow-500"></i>
                    </div>
                    <h3 class="documents-empty-title">Failed to load documents</h3>
                    <p class="documents-empty-text">Please check your connection and try again</p>
                    <button onclick="uploadManager.loadDocuments()" class="mt-4 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition">
                        <i class="fas fa-refresh mr-2"></i>Retry
                    </button>
                </div>
            `;
        }

        renderDocumentItem(doc) {
            const iconClass = this.getFileIcon(doc.source_type);
            const statusClass = doc.status.toLowerCase();

            return `
                <div class="document-item" data-document-id="${doc.id}">
                    <div class="document-icon ${doc.source_type}">
                        <i class="fas ${iconClass}"></i>
                    </div>
                    <div class="document-info">
                        <div class="document-title">${this.escapeHtml(doc.title)}</div>
                        <div class="document-meta">
                            <span>${doc.source_type.toUpperCase()}</span>
                            <span>•</span>
                            <span>${doc.chunk_count} chunks</span>
                            <span>•</span>
                            <span>${this.formatDate(doc.created_at)}</span>
                        </div>
                    </div>
                    <span class="document-status ${statusClass}">
                        ${this.formatStatus(doc.status)}
                    </span>
                    <div class="document-actions">
                        <button class="document-action-btn delete" onclick="uploadManager.deleteDocument('${doc.id}')" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
        }

        async deleteDocument(docId) {
            if (!confirm('Are you sure you want to delete this document? This action cannot be undone.')) {
                return;
            }

            const apiKey = this.getApiKey();
            if (!apiKey) {
                this.showToast('API key not found', 'error');
                return;
            }

            try {
                const response = await fetch(`${CONFIG.documentsEndpoint}${docId}/`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${apiKey}`
                    }
                });

                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.error || 'Failed to delete document');
                }

                this.showToast('Document deleted successfully', 'success');
                
                // Stop polling if active
                this.stopStatusPolling(docId);
                
                // Remove from list
                this.documents = this.documents.filter(d => d.id !== docId);
                this.renderDocuments();

            } catch (error) {
                console.error('Delete error:', error);
                this.showToast(error.message || 'Failed to delete document', 'error');
            }
        }

        // ===========================================
        // Status Polling
        // ===========================================

        startStatusPolling(docId) {
            // Don't duplicate polling
            if (this.pollingIntervals[docId]) return;

            console.log(`Starting status polling for document: ${docId}`);

            this.pollingIntervals[docId] = setInterval(async () => {
                try {
                    const apiKey = this.getApiKey();
                    if (!apiKey) {
                        this.stopStatusPolling(docId);
                        return;
                    }

                    const response = await fetch(`${CONFIG.documentsEndpoint}${docId}/`, {
                        headers: {
                            'Authorization': `Bearer ${apiKey}`
                        }
                    });

                    if (!response.ok) {
                        this.stopStatusPolling(docId);
                        return;
                    }

                    const doc = await response.json();

                    // Update document in list
                    const index = this.documents.findIndex(d => d.id === docId);
                    if (index !== -1) {
                        this.documents[index] = doc;
                        this.renderDocuments();
                    }

                    // Stop polling if completed or failed
                    if (doc.status === 'completed' || doc.status === 'failed') {
                        this.stopStatusPolling(docId);
                        
                        if (doc.status === 'completed') {
                            this.showToast(`"${doc.title}" processing complete! (${doc.chunk_count} chunks)`, 'success');
                        } else {
                            this.showToast(`"${doc.title}" processing failed`, 'error');
                        }
                    }

                } catch (error) {
                    console.error('Polling error:', error);
                    this.stopStatusPolling(docId);
                }
            }, CONFIG.pollingInterval);
        }

        stopStatusPolling(docId) {
            if (this.pollingIntervals[docId]) {
                console.log(`Stopping status polling for document: ${docId}`);
                clearInterval(this.pollingIntervals[docId]);
                delete this.pollingIntervals[docId];
            }
        }

        // ===========================================
        // Utility Functions
        // ===========================================

        showToast(message, type = 'info') {
            // Use global Dashboard.showToast if available
            if (window.Dashboard && window.Dashboard.showToast) {
                window.Dashboard.showToast(message, type);
            } else if (window.showToast) {
                window.showToast(message, type);
            } else {
                // Fallback to alert
                console.log(`[${type.toUpperCase()}] ${message}`);
                if (type === 'error') {
                    alert(message);
                }
            }
        }

        escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text || '';
            return div.innerHTML;
        }

        getFileExtension(filename) {
            if (!filename) return '';
            const lastDot = filename.lastIndexOf('.');
            return lastDot !== -1 ? filename.substring(lastDot).toLowerCase() : '';
        }

        getFileNameWithoutExtension(filename) {
            if (!filename) return '';
            const lastDot = filename.lastIndexOf('.');
            return lastDot !== -1 ? filename.substring(0, lastDot) : filename;
        }

        getFileIcon(type) {
            const icons = {
                'pdf': 'fa-file-pdf',
                'docx': 'fa-file-word',
                'text': 'fa-file-alt',
                'txt': 'fa-file-alt',
                'csv': 'fa-file-csv',
                'json': 'fa-file-code',
                'markdown': 'fa-file-alt',
                'md': 'fa-file-alt',
                'paste': 'fa-paste',
                'excel': 'fa-file-excel'
            };
            return icons[type?.toLowerCase()] || 'fa-file';
        }

        formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }

        formatDate(dateString) {
            if (!dateString) return 'Unknown';
            
            try {
                const date = new Date(dateString);
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

        formatStatus(status) {
            const statusMap = {
                'pending': 'Pending',
                'processing': 'Processing',
                'completed': 'Completed',
                'failed': 'Failed'
            };
            return statusMap[status?.toLowerCase()] || status;
        }
    }

    // ===========================================
    // Initialize
    // ===========================================
    
    function init() {
        window.uploadManager = new UploadManager();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();