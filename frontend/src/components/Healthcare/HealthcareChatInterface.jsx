import React, { useState, useEffect, useRef } from 'react';
import { 
    Send, 
    Mic, 
    Camera, 
    AlertTriangle, 
    Phone, 
    MessageCircle, 
    Shield,
    FileText,
    Clock,
    User,
    Bot,
    Heart,
    Brain
} from 'lucide-react';
import './HealthcareChatInterface.css';

const HealthcareChatInterface = ({ 
    userRole = 'patient', 
    onSendMessage, 
    messages = [], 
    isLoading = false, 
    isOffline = false,
    patientId = null 
}) => {
    const [inputText, setInputText] = useState('');
    const [isRecording, setIsRecording] = useState(false);
    const [showEmergencyPanel, setShowEmergencyPanel] = useState(false);
    const [showMedicalDisclaimer, setShowMedicalDisclaimer] = useState(true);
    const [sessionStartTime] = useState(new Date());
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);
    const mediaRecorderRef = useRef(null);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        // Auto-focus input on mount
        if (inputRef.current) {
            inputRef.current.focus();
        }
    }, []);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const handleSendMessage = async () => {
        if (!inputText.trim() || isLoading) return;

        const message = inputText.trim();
        setInputText('');

        // Crisis detection with healthcare-appropriate keywords
        const crisisKeywords = [
            'suicide', 'kill myself', 'end it all', 'hurt myself', 'die',
            'overdose', 'self-harm', 'cutting', 'worthless', 'hopeless'
        ];
        
        const isCrisis = crisisKeywords.some(keyword => 
            message.toLowerCase().includes(keyword)
        );

        if (isCrisis) {
            setShowEmergencyPanel(true);
            // Log crisis event for healthcare providers
            logCrisisEvent(message);
        }

        await onSendMessage(message, { 
            inputMode: 'text', 
            isCrisis,
            timestamp: new Date(),
            patientId,
            sessionId: generateSessionId()
        });
    };

    const logCrisisEvent = (message) => {
        // This would send an alert to healthcare providers
        console.log('Crisis event detected:', {
            message,
            timestamp: new Date(),
            patientId,
            severity: 'high'
        });
    };

    const generateSessionId = () => {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const startVoiceRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;

            const audioChunks = [];

            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                await handleVoiceMessage(audioBlob);
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorder.start();
            setIsRecording(true);

        } catch (error) {
            console.error('Error starting voice recording:', error);
            alert('Unable to access microphone. Please check permissions.');
        }
    };

    const stopVoiceRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
        }
    };

    const handleVoiceMessage = async (audioBlob) => {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'voice-message.wav');

        try {
            await onSendMessage('[Voice Message]', { 
                inputMode: 'voice', 
                audioData: formData,
                timestamp: new Date(),
                patientId
            });
        } catch (error) {
            console.error('Error sending voice message:', error);
        }
    };

    const MedicalDisclaimer = () => (
        showMedicalDisclaimer && (
            <div className="medical-disclaimer-banner">
                <div className="disclaimer-content">
                    <Shield size={20} />
                    <div className="disclaimer-text">
                        <strong>Medical Disclaimer:</strong> This AI assistant provides supportive information only. 
                        It is not a substitute for professional medical advice, diagnosis, or treatment. 
                        Always consult with qualified healthcare professionals for medical concerns.
                    </div>
                    <button 
                        onClick={() => setShowMedicalDisclaimer(false)}
                        className="disclaimer-close"
                    >
                        ×
                    </button>
                </div>
            </div>
        )
    );

    const EmergencyPanel = () => (
        <div className={`emergency-panel ${showEmergencyPanel ? 'show' : ''}`}>
            <div className="emergency-content">
                <div className="emergency-header">
                    <AlertTriangle className="emergency-icon" />
                    <h3>Immediate Support Available</h3>
                </div>

                <p>If you're experiencing a mental health crisis, please reach out for immediate help:</p>

                <div className="emergency-resources">
                    <a href="tel:988" className="emergency-link primary">
                        <Phone size={20} />
                        <div>
                            <strong>988</strong>
                            <span>Suicide & Crisis Lifeline (24/7)</span>
                        </div>
                    </a>

                    <a href="sms:741741&body=HOME" className="emergency-link">
                        <MessageCircle size={20} />
                        <div>
                            <strong>Text HOME to 741741</strong>
                            <span>Crisis Text Line (24/7)</span>
                        </div>
                    </a>

                    <a href="tel:911" className="emergency-link">
                        <Phone size={20} />
                        <div>
                            <strong>911</strong>
                            <span>Emergency Services</span>
                        </div>
                    </a>

                    {userRole === 'patient' && (
                        <button className="emergency-link provider-contact">
                            <User size={20} />
                            <div>
                                <strong>Contact Your Provider</strong>
                                <span>Reach your healthcare team</span>
                            </div>
                        </button>
                    )}
                </div>

                <div className="emergency-actions">
                    <button 
                        onClick={() => setShowEmergencyPanel(false)}
                        className="btn-secondary"
                    >
                        Continue Session
                    </button>
                </div>
            </div>
        </div>
    );

    const SessionHeader = () => (
        <div className="session-header">
            <div className="session-info">
                <div className="session-title">
                    <Brain size={20} />
                    <span>Sage Healthcare Session</span>
                </div>
                <div className="session-details">
                    <span className="session-time">
                        <Clock size={16} />
                        Started: {sessionStartTime.toLocaleTimeString()}
                    </span>
                    {patientId && (
                        <span className="patient-id">
                            <User size={16} />
                            Patient ID: {patientId}
                        </span>
                    )}
                </div>
            </div>
            <div className="session-status">
                <div className={`status-indicator ${isOffline ? 'offline' : 'online'}`}>
                    {isOffline ? 'Offline' : 'Secure Connection'}
                </div>
                <Shield size={16} className="security-icon" />
            </div>
        </div>
    );

    return (
        <div className="healthcare-chat-interface">
            <MedicalDisclaimer />
            <SessionHeader />

            {/* Messages Container */}
            <div className="messages-container">
                {messages.length === 0 && (
                    <div className="welcome-message">
                        <div className="welcome-content">
                            <Heart size={48} className="welcome-icon" />
                            <h3>Welcome to Sage Healthcare AI</h3>
                            <p>
                                I'm here to provide supportive mental health guidance. 
                                This is a safe, confidential space to discuss your thoughts and feelings.
                            </p>
                            <div className="welcome-features">
                                <div className="feature">
                                    <Shield size={16} />
                                    <span>HIPAA Compliant</span>
                                </div>
                                <div className="feature">
                                    <AlertTriangle size={16} />
                                    <span>Crisis Support Available</span>
                                </div>
                                <div className="feature">
                                    <FileText size={16} />
                                    <span>Session Documentation</span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {messages.map((message, index) => (
                    <div 
                        key={index} 
                        className={`message ${message.isUser ? 'user' : 'assistant'}`}
                    >
                        <div className="message-avatar">
                            {message.isUser ? (
                                <User size={20} />
                            ) : (
                                <Bot size={20} />
                            )}
                        </div>
                        <div className="message-content">
                            <div className="message-text">
                                {message.content}
                            </div>
                            {message.medical_disclaimer && (
                                <div className="message-disclaimer">
                                    <Shield size={14} />
                                    {message.medical_disclaimer}
                                </div>
                            )}
                            {message.safety_warnings && message.safety_warnings.length > 0 && (
                                <div className="safety-warnings">
                                    {message.safety_warnings.map((warning, idx) => (
                                        <div key={idx} className="safety-warning">
                                            <AlertTriangle size={14} />
                                            {warning}
                                        </div>
                                    ))}
                                </div>
                            )}
                            <div className="message-timestamp">
                                {new Date(message.timestamp).toLocaleTimeString([], {
                                    hour: '2-digit',
                                    minute: '2-digit'
                                })}
                            </div>
                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div className="message assistant">
                        <div className="message-avatar">
                            <Bot size={20} />
                        </div>
                        <div className="message-content">
                            <div className="typing-indicator">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input Container */}
            <div className="input-container">
                <div className="input-wrapper">
                    {!isRecording ? (
                        <>
                            <textarea
                                ref={inputRef}
                                value={inputText}
                                onChange={(e) => setInputText(e.target.value)}
                                onKeyPress={handleKeyPress}
                                placeholder={isOffline ? "Offline - Emergency resources available" : "Share your thoughts and feelings..."}
                                className="message-input"
                                rows="1"
                                disabled={isOffline}
                                maxLength={2000}
                            />

                            <div className="input-actions">
                                <button
                                    onClick={startVoiceRecording}
                                    className="action-btn"
                                    disabled={isOffline}
                                    title="Voice message"
                                >
                                    <Mic size={20} />
                                </button>

                                <button
                                    onClick={handleSendMessage}
                                    className="send-btn"
                                    disabled={!inputText.trim() || isLoading || isOffline}
                                >
                                    <Send size={20} />
                                </button>
                            </div>
                        </>
                    ) : (
                        <div className="voice-recording">
                            <div className="recording-indicator">
                                <div className="pulse"></div>
                                <span>Recording your message...</span>
                            </div>
                            <button
                                onClick={stopVoiceRecording}
                                className="stop-recording-btn"
                            >
                                Stop Recording
                            </button>
                        </div>
                    )}
                </div>

                {/* Emergency Button */}
                <button
                    onClick={() => setShowEmergencyPanel(true)}
                    className="emergency-btn"
                    title="Crisis Support Resources"
                >
                    <AlertTriangle size={20} />
                    <span>Crisis Support</span>
                </button>
            </div>

            {/* Emergency Panel */}
            <EmergencyPanel />
        </div>
    );
};

export default HealthcareChatInterface;
