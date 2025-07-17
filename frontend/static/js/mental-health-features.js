/**
 * Mental Health Agent - Custom JavaScript Features
 * Enhances Open WebUI with mental health specific functionality
 */

class MentalHealthAgent {
    constructor() {
        this.websocket = null;
        this.sessionId = this.generateSessionId();
        this.crisisKeywords = [
            'suicide', 'kill myself', 'end my life', 'self-harm', 'hurt myself',
            'crisis', 'emergency', 'hopeless', 'worthless', 'die'
        ];
        this.isConnected = false;
        this.messageQueue = [];
        
        this.init();
    }
    
    init() {
        this.setupWebSocket();
        this.setupCrisisDetection();
        this.setupMedicalDisclaimer();
        this.setupConfidenceIndicators();
        this.setupCitationsDisplay();
        this.setupAccessibility();
        this.setupEventListeners();
        
        console.log('Mental Health Agent initialized');
    }
    
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    setupWebSocket() {
        const wsUrl = this.getWebSocketUrl();
        const token = this.getAuthToken();
        
        if (!token) {
            console.warn('No auth token found, WebSocket connection may fail');
            return;
        }
        
        try {
            this.websocket = new WebSocket(`${wsUrl}?token=${token}&session_id=${this.sessionId}`);
            
            this.websocket.onopen = (event) => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.processMessageQueue();
                this.showConnectionStatus('connected');
            };
            
            this.websocket.onmessage = (event) => {
                this.handleWebSocketMessage(event);
            };
            
            this.websocket.onclose = (event) => {
                console.log('WebSocket disconnected');
                this.isConnected = false;
                this.showConnectionStatus('disconnected');
                
                // Attempt to reconnect after 3 seconds
                setTimeout(() => {
                    this.setupWebSocket();
                }, 3000);
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.showConnectionStatus('error');
            };
            
        } catch (error) {
            console.error('Failed to setup WebSocket:', error);
        }
    }
    
    getWebSocketUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        return `${protocol}//${host}/api/ws`;
    }
    
    getAuthToken() {
        // Try to get token from localStorage or sessionStorage
        return localStorage.getItem('auth_token') || 
               sessionStorage.getItem('auth_token') ||
               this.getCookie('auth_token');
    }
    
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }
    
    handleWebSocketMessage(event) {
        try {
            const data = JSON.parse(event.data);
            
            switch (data.type) {
                case 'connection_established':
                    this.handleConnectionEstablished(data);
                    break;
                case 'message_received':
                    this.handleMessageReceived(data);
                    break;
                case 'agent_response':
                    this.handleAgentResponse(data);
                    break;
                case 'error':
                    this.handleError(data);
                    break;
                case 'pong':
                    // Heartbeat response
                    break;
                default:
                    console.log('Unknown message type:', data.type);
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }
    
    handleConnectionEstablished(data) {
        console.log('Connection established:', data);
        this.sessionId = data.session_id;
    }
    
    handleMessageReceived(data) {
        console.log('Message received:', data);
        this.showTypingIndicator();
    }
    
    handleAgentResponse(data) {
        console.log('Agent response:', data);
        this.hideTypingIndicator();
        this.displayAgentResponse(data);
    }
    
    handleError(data) {
        console.error('WebSocket error:', data);
        this.showErrorMessage(data.message);
    }
    
    sendMessage(message) {
        const messageData = {
            type: 'chat_message',
            content: message,
            session_id: this.sessionId,
            timestamp: new Date().toISOString(),
            metadata: {
                user_agent: navigator.userAgent,
                timestamp: Date.now()
            }
        };
        
        if (this.isConnected && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify(messageData));
        } else {
            this.messageQueue.push(messageData);
            console.log('Message queued (WebSocket not connected)');
        }
        
        // Check for crisis keywords
        this.checkForCrisisContent(message);
    }
    
    processMessageQueue() {
        while (this.messageQueue.length > 0 && this.isConnected) {
            const message = this.messageQueue.shift();
            this.websocket.send(JSON.stringify(message));
        }
    }
    
    setupCrisisDetection() {
        // Monitor all text inputs for crisis keywords
        document.addEventListener('input', (event) => {
            if (event.target.matches('textarea, input[type="text"]')) {
                this.checkForCrisisContent(event.target.value);
            }
        });
    }
    
    checkForCrisisContent(text) {
        const lowerText = text.toLowerCase();
        const foundKeywords = this.crisisKeywords.filter(keyword => 
            lowerText.includes(keyword)
        );
        
        if (foundKeywords.length > 0) {
            this.showCrisisResources();
            this.logSafetyEvent('crisis_keywords_detected', { keywords: foundKeywords });
        }
    }
    
    showCrisisResources() {
        // Remove existing crisis panel
        const existing = document.querySelector('.crisis-resources-panel');
        if (existing) existing.remove();
        
        const crisisPanel = document.createElement('div');
        crisisPanel.className = 'crisis-resources-panel crisis-resources';
        crisisPanel.innerHTML = `
            <h3>🆘 Immediate Help Resources</h3>
            <p><strong>If you're in immediate danger, please contact emergency services:</strong></p>
            
            <div class="crisis-resource-item">
                <h4>Emergency Services</h4>
                <div class="phone">911 (US) • 999 (UK) • 112 (EU)</div>
            </div>
            
            <div class="crisis-resource-item">
                <h4>National Suicide Prevention Lifeline</h4>
                <div class="phone">988</div>
                <p>24/7 crisis support</p>
            </div>
            
            <div class="crisis-resource-item">
                <h4>Crisis Text Line</h4>
                <div class="phone">Text HOME to 741741</div>
                <p>24/7 text-based crisis support</p>
            </div>
            
            <button class="btn btn-crisis" onclick="this.parentElement.style.display='none'">
                I understand
            </button>
        `;
        
        // Insert at the top of the chat area
        const chatContainer = document.querySelector('.chat-container') || document.body;
        chatContainer.insertBefore(crisisPanel, chatContainer.firstChild);
        
        // Auto-scroll to crisis resources
        crisisPanel.scrollIntoView({ behavior: 'smooth' });
    }
    
    setupMedicalDisclaimer() {
        // Show medical disclaimer if not already shown in this session
        if (!sessionStorage.getItem('medical_disclaimer_shown')) {
            this.showMedicalDisclaimer();
            sessionStorage.setItem('medical_disclaimer_shown', 'true');
        }
    }
    
    showMedicalDisclaimer() {
        const disclaimer = document.createElement('div');
        disclaimer.className = 'medical-disclaimer';
        disclaimer.innerHTML = `
            <h3>⚠️ Important Medical Disclaimer</h3>
            <p>This AI assistant provides general mental health information and support. 
            It is not a substitute for professional medical advice, diagnosis, or treatment.</p>
            <p>Always seek the advice of qualified mental health professionals with any questions 
            you may have regarding a medical condition.</p>
            <div class="emergency-info">
                <strong>If you are experiencing a mental health emergency, please contact:</strong><br>
                • Emergency Services: 911 (US), 999 (UK), 112 (EU)<br>
                • National Suicide Prevention Lifeline: 988<br>
                • Crisis Text Line: Text HOME to 741741
            </div>
        `;
        
        // Insert at the top of the page
        document.body.insertBefore(disclaimer, document.body.firstChild);
    }
    
    setupConfidenceIndicators() {
        // This will be called when displaying agent responses
        this.confidenceThresholds = {
            high: 0.8,
            medium: 0.5,
            low: 0.0
        };
    }
    
    displayConfidenceIndicator(confidence) {
        let level, text, className;
        
        if (confidence >= this.confidenceThresholds.high) {
            level = 'high';
            text = 'High Confidence';
            className = 'confidence-high';
        } else if (confidence >= this.confidenceThresholds.medium) {
            level = 'medium';
            text = 'Medium Confidence';
            className = 'confidence-medium';
        } else {
            level = 'low';
            text = 'Low Confidence';
            className = 'confidence-low';
        }
        
        return `
            <div class="confidence-indicator ${className}">
                <span class="confidence-icon">📊</span>
                <span>${text} (${Math.round(confidence * 100)}%)</span>
            </div>
        `;
    }
    
    setupCitationsDisplay() {
        // Citations will be displayed with agent responses
    }
    
    displayCitations(citations) {
        if (!citations || citations.length === 0) return '';
        
        const citationsHtml = citations.map(citation => `
            <div class="citation-item">
                <div class="title">${citation.title}</div>
                <div class="source">${citation.source}</div>
                ${citation.url ? `<a href="${citation.url}" target="_blank" rel="noopener">View Source</a>` : ''}
            </div>
        `).join('');
        
        return `
            <div class="citations">
                <h4>📚 Scientific Sources</h4>
                ${citationsHtml}
            </div>
        `;
    }
    
    displayReasoningSteps(steps) {
        if (!steps || steps.length === 0) return '';
        
        const stepsHtml = steps.map((step, index) => `
            <div class="reasoning-step">
                ${index + 1}. ${step}
            </div>
        `).join('');
        
        return `
            <div class="reasoning-steps">
                <h4>🧠 Reasoning Process</h4>
                ${stepsHtml}
            </div>
        `;
    }
    
    displayAgentResponse(data) {
        const messageContainer = document.createElement('div');
        messageContainer.className = 'chat-message assistant';
        
        // Check for safety warnings
        if (data.safety_warnings && data.safety_warnings.length > 0) {
            messageContainer.classList.add('crisis');
        }
        
        messageContainer.innerHTML = `
            <div class="message-content">${data.response}</div>
            ${this.displayConfidenceIndicator(data.confidence_level)}
            ${this.displayCitations(data.citations)}
            ${this.displayReasoningSteps(data.reasoning_steps)}
            ${data.medical_disclaimer ? `<div class="medical-disclaimer-small">${data.medical_disclaimer}</div>` : ''}
        `;
        
        // Add to chat
        const chatContainer = document.querySelector('.chat-messages') || document.querySelector('.chat-container');
        if (chatContainer) {
            chatContainer.appendChild(messageContainer);
            messageContainer.scrollIntoView({ behavior: 'smooth' });
        }
    }
    
    setupAccessibility() {
        // Add ARIA labels and roles
        document.addEventListener('DOMContentLoaded', () => {
            const chatInput = document.querySelector('.chat-input');
            if (chatInput) {
                chatInput.setAttribute('aria-label', 'Type your message to the mental health agent');
                chatInput.setAttribute('role', 'textbox');
            }
        });
        
        // Keyboard navigation support
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                // Close any open crisis panels
                const crisisPanel = document.querySelector('.crisis-resources-panel');
                if (crisisPanel) {
                    crisisPanel.style.display = 'none';
                }
            }
        });
    }
    
    setupEventListeners() {
        // Send message on Enter (but not Shift+Enter)
        document.addEventListener('keydown', (event) => {
            if (event.target.matches('.chat-input') && event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                const message = event.target.value.trim();
                if (message) {
                    this.sendMessage(message);
                    event.target.value = '';
                }
            }
        });
        
        // Heartbeat to keep connection alive
        setInterval(() => {
            if (this.isConnected && this.websocket.readyState === WebSocket.OPEN) {
                this.websocket.send(JSON.stringify({
                    type: 'ping',
                    timestamp: Date.now()
                }));
            }
        }, 30000); // Every 30 seconds
    }
    
    showTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
        
        const chatContainer = document.querySelector('.chat-messages') || document.querySelector('.chat-container');
        if (chatContainer) {
            chatContainer.appendChild(indicator);
            indicator.scrollIntoView({ behavior: 'smooth' });
        }
    }
    
    hideTypingIndicator() {
        const indicator = document.querySelector('.typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }
    
    showConnectionStatus(status) {
        const statusElement = document.querySelector('.connection-status') || this.createConnectionStatus();
        
        statusElement.className = `connection-status status-${status}`;
        statusElement.textContent = {
            connected: '🟢 Connected',
            disconnected: '🟡 Reconnecting...',
            error: '🔴 Connection Error'
        }[status] || '🟡 Unknown';
    }
    
    createConnectionStatus() {
        const status = document.createElement('div');
        status.className = 'connection-status';
        status.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            z-index: 1000;
        `;
        document.body.appendChild(status);
        return status;
    }
    
    showErrorMessage(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.style.cssText = `
            background: #fee2e2;
            color: #dc2626;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            border-left: 4px solid #dc2626;
        `;
        errorDiv.textContent = message;
        
        const chatContainer = document.querySelector('.chat-container') || document.body;
        chatContainer.appendChild(errorDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => errorDiv.remove(), 5000);
    }
    
    logSafetyEvent(eventType, data) {
        console.log('Safety event:', eventType, data);
        
        // Send to backend for logging
        if (this.isConnected) {
            this.websocket.send(JSON.stringify({
                type: 'safety_event',
                event_type: eventType,
                data: data,
                timestamp: Date.now()
            }));
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.mentalHealthAgent = new MentalHealthAgent();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MentalHealthAgent;
}
