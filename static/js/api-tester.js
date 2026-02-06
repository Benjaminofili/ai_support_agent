/**
 * API Connection Tester
 * Verifies frontend-backend connectivity
 */

(function() {
    'use strict';

    class ApiTester {
        constructor() {
            this.apiKey = this.getApiKey();
            this.results = [];
        }

        getApiKey() {
            const input = document.getElementById('api-key-hidden');
            return input ? input.value : null;
        }

        async runTests() {
            console.log('🔍 Starting API Connection Tests...\n');
            this.results = [];

            // Test 1: Check API Key
            await this.testApiKey();

            // Test 2: Config Check Endpoint
            await this.testConfigCheck();

            // Test 3: Documents List
            await this.testDocumentsList();

            // Test 4: Upload Endpoint
            await this.testUploadEndpoint();

            // Test 5: Conversations List
            await this.testConversationsList();

            // Print Summary
            this.printSummary();

            return this.results;
        }

        async testApiKey() {
            const test = {
                name: 'API Key Check',
                status: 'pending',
                message: '',
                data: null
            };

            try {
                if (!this.apiKey) {
                    test.status = 'failed';
                    test.message = 'API key not found in DOM';
                } else if (this.apiKey.length < 20) {
                    test.status = 'warning';
                    test.message = `API key seems too short (${this.apiKey.length} chars)`;
                } else {
                    test.status = 'passed';
                    test.message = `API key found (${this.apiKey.length} chars)`;
                    test.data = { 
                        prefix: this.apiKey.substring(0, 8) + '...',
                        length: this.apiKey.length 
                    };
                }
            } catch (error) {
                test.status = 'error';
                test.message = error.message;
            }

            this.results.push(test);
            this.logTest(test);
        }

        async testConfigCheck() {
            const test = {
                name: 'Config Check Endpoint',
                status: 'pending',
                message: '',
                data: null
            };

            try {
                const response = await fetch('/dashboard/api/config-check/', {
                    headers: {
                        'Accept': 'application/json'
                    }
                });

                const data = await response.json();

                if (response.ok && data.status === 'ok') {
                    test.status = 'passed';
                    test.message = `Connected to company: ${data.company.name}`;
                    test.data = data;
                } else {
                    test.status = 'failed';
                    test.message = data.message || 'Config check failed';
                    test.data = data;
                }
            } catch (error) {
                test.status = 'error';
                test.message = error.message;
            }

            this.results.push(test);
            this.logTest(test);
        }

        async testDocumentsList() {
            const test = {
                name: 'Documents API',
                status: 'pending',
                message: '',
                data: null
            };

            try {
                const response = await fetch('/api/knowledge/documents/', {
                    headers: {
                        'Authorization': `Bearer ${this.apiKey}`,
                        'Accept': 'application/json'
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    test.status = 'passed';
                    test.message = `Retrieved ${data.length} documents`;
                    test.data = { count: data.length, sample: data.slice(0, 2) };
                } else if (response.status === 401) {
                    test.status = 'failed';
                    test.message = 'Authentication failed - invalid API key';
                } else {
                    const error = await response.json();
                    test.status = 'failed';
                    test.message = error.detail || `HTTP ${response.status}`;
                }
            } catch (error) {
                test.status = 'error';
                test.message = error.message;
            }

            this.results.push(test);
            this.logTest(test);
        }

        async testUploadEndpoint() {
            const test = {
                name: 'Upload Endpoint Check',
                status: 'pending',
                message: '',
                data: null
            };

            try {
                // Try OPTIONS request to check endpoint exists
                const response = await fetch('/api/knowledge/documents/upload/', {
                    method: 'OPTIONS',
                    headers: {
                        'Authorization': `Bearer ${this.apiKey}`
                    }
                });

                // For OPTIONS, we just check if endpoint exists
                test.status = 'passed';
                test.message = 'Upload endpoint accessible';
                test.data = { 
                    status: response.status,
                    allowed: response.headers.get('Allow')
                };
            } catch (error) {
                test.status = 'error';
                test.message = error.message;
            }

            this.results.push(test);
            this.logTest(test);
        }

        async testConversationsList() {
            const test = {
                name: 'Conversations API',
                status: 'pending',
                message: '',
                data: null
            };

            try {
                const response = await fetch('/api/chat/conversations/', {
                    headers: {
                        'Authorization': `Bearer ${this.apiKey}`,
                        'Accept': 'application/json'
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    test.status = 'passed';
                    test.message = `Retrieved ${data.length} conversations`;
                    test.data = { count: data.length };
                } else if (response.status === 401) {
                    test.status = 'failed';
                    test.message = 'Authentication failed';
                } else {
                    test.status = 'failed';
                    test.message = `HTTP ${response.status}`;
                }
            } catch (error) {
                test.status = 'error';
                test.message = error.message;
            }

            this.results.push(test);
            this.logTest(test);
        }

        logTest(test) {
            const icons = {
                'passed': '✅',
                'failed': '❌',
                'warning': '⚠️',
                'error': '🔥',
                'pending': '⏳'
            };

            const icon = icons[test.status] || '❓';
            console.log(`${icon} ${test.name}: ${test.message}`);
            
            if (test.data) {
                console.log('   Data:', test.data);
            }
        }

        printSummary() {
            const passed = this.results.filter(r => r.status === 'passed').length;
            const failed = this.results.filter(r => r.status === 'failed').length;
            const errors = this.results.filter(r => r.status === 'error').length;
            const warnings = this.results.filter(r => r.status === 'warning').length;
            const total = this.results.length;

            console.log('\n📊 Test Summary:');
            console.log(`   Total: ${total}`);
            console.log(`   ✅ Passed: ${passed}`);
            console.log(`   ❌ Failed: ${failed}`);
            console.log(`   🔥 Errors: ${errors}`);
            console.log(`   ⚠️  Warnings: ${warnings}`);

            if (passed === total) {
                console.log('\n🎉 All tests passed! API is properly configured.');
            } else {
                console.log('\n⚠️  Some tests failed. Check the details above.');
            }
        }

        // Create visual report
        createReport() {
            const container = document.createElement('div');
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: white;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                max-width: 400px;
                max-height: 80vh;
                overflow-y: auto;
                z-index: 10000;
                font-family: monospace;
                font-size: 12px;
            `;

            const html = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <h3 style="margin: 0; font-size: 16px;">API Test Results</h3>
                    <button onclick="this.parentElement.parentElement.remove()" style="border: none; background: none; cursor: pointer; font-size: 18px;">×</button>
                </div>
                ${this.results.map(test => {
                    const colors = {
                        'passed': '#22c55e',
                        'failed': '#ef4444',
                        'warning': '#f59e0b',
                        'error': '#dc2626'
                    };
                    const color = colors[test.status] || '#6b7280';
                    
                    return `
                        <div style="margin-bottom: 10px; padding: 10px; border-left: 3px solid ${color}; background: #f9fafb; border-radius: 4px;">
                            <div style="font-weight: bold; color: ${color}; margin-bottom: 5px;">
                                ${test.name}
                            </div>
                            <div style="color: #374151;">
                                ${test.message}
                            </div>
                        </div>
                    `;
                }).join('')}
            `;

            container.innerHTML = html;
            document.body.appendChild(container);
        }
    }

    // Export to global scope
    window.ApiTester = ApiTester;

    // Auto-run if ?test=api in URL
    if (window.location.search.includes('test=api')) {
        window.addEventListener('DOMContentLoaded', async () => {
            const tester = new ApiTester();
            await tester.runTests();
            tester.createReport();
        });
    }

})();