import React, { useState, useEffect, useRef } from 'react';
import { Send, Mic, Camera, AlertTriangle, Phone, MessageCircle } from 'lucide-react';
import './MobileChatInterface.css';

const MobileChatInterface = ({ onSendMessage, messages, isLoading, isOffline }) => {
    const [inputText, setInputText] = useState('');
    const [isRecording, setIsRecording] = useState(false);
    const [showEmergencyPanel, setShowEmergencyPanel] = useState(false);
    const [inputMode, setInputMode] = useState('text'); // text, voice, image
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);
    const mediaRecorderRef = useRef(null);
    
    useEffect(() => {
        scrollToBottom();
    }, [messages]);
    
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };
    
    const handleSendMessage = async () => {
        if (!inputText.trim() || isLoading) return;
        
        const message = inputText.trim();
        setInputText('');
        
        // Check for crisis keywords
        const crisisKeywords = ['suicide', 'kill myself', 'end it all', 'hurt myself', 'die'];
        const isCrisis = crisisKeywords.some(keyword => 
            message.toLowerCase().includes(keyword)
        );
        
        if (isCrisis) {
            setShowEmergencyPanel(true);
            // Vibrate if supported
            if ('vibrate' in navigator) {
                navigator.vibrate([300, 100, 300]);
            }
        }
        
        await onSendMessage(message, { inputMode, isCrisis });
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
            setInputMode('voice');
            
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
            // Send voice message to backend for processing
            await onSendMessage('[Voice Message]', { 
                inputMode: 'voice', 
                audioData: formData 
            });
        } catch (error) {
            console.error('Error sending voice message:', error);
        }
    };
    
    const handleImageCapture = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: 'environment' } 
            });
            
            // Create video element for camera preview
            const video = document.createElement('video');
            video.srcObject = stream;
            video.play();
            
            // Show camera interface
            showCameraInterface(video, stream);
            
        } catch (error) {
            console.error('Error accessing camera:', error);
            alert('Unable to access camera. Please check permissions.');
        }
    };
    
    const showCameraInterface = (video, stream) => {
        const modal = document.createElement('div');
        modal.className = 'camera-modal';
        modal.innerHTML = `
            <div class="camera-container">
                <video autoplay playsinline></video>
                <div class="camera-controls">
                    <button class="camera-btn cancel">Cancel</button>
                    <button class="camera-btn capture">📷</button>
                    <button class="camera-btn switch">🔄</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        const videoElement = modal.querySelector('video');
        videoElement.srcObject = stream;
        
        // Handle camera controls
        modal.querySelector('.cancel').onclick = () => {
            stream.getTracks().forEach(track => track.stop());
            modal.remove();
        };
        
        modal.querySelector('.capture').onclick = () => {
            captureImage(videoElement, stream, modal);
        };
    };
    
    const captureImage = async (video, stream, modal) => {
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0);
        
        canvas.toBlob(async (blob) => {
            stream.getTracks().forEach(track => track.stop());
            modal.remove();
            
            await onSendMessage('[Image]', { 
                inputMode: 'image', 
                imageData: blob 
            });
        }, 'image/jpeg', 0.8);
    };
    
    const EmergencyPanel = () => (
        <div className={`emergency-panel ${showEmergencyPanel ? 'show' : ''}`}>
            <div className="emergency-content">
                <div className="emergency-header">
                    <AlertTriangle className="emergency-icon" />
                    <h3>Crisis Support Available</h3>
                </div>
                
                <p>If you're having thoughts of self-harm, please reach out for help immediately:</p>
                
                <div className="emergency-resources">
                    <a href="tel:988" className="emergency-link primary">
                        <Phone size={20} />
                        <div>
                            <strong>988</strong>
                            <span>Suicide & Crisis Lifeline</span>
                        </div>
                    </a>
                    
                    <a href="sms:741741&body=HOME" className="emergency-link">
                        <MessageCircle size={20} />
                        <div>
                            <strong>Text HOME to 741741</strong>
                            <span>Crisis Text Line</span>
                        </div>
                    </a>
                    
                    <a href="tel:911" className="emergency-link">
                        <Phone size={20} />
                        <div>
                            <strong>911</strong>
                            <span>Emergency Services</span>
                        </div>
                    </a>
                </div>
                
                <div className="emergency-actions">
                    <button 
                        onClick={() => setShowEmergencyPanel(false)}
                        className="btn-secondary"
                    >
                        Continue Conversation
                    </button>
                </div>
            </div>
        </div>
    );
    
    return (
        <div className="mobile-chat-interface">
            {/* Connection Status */}
            {isOffline && (
                <div className="offline-banner">
                    <span>You're offline - Emergency resources still available</span>
                </div>
            )}
            
            {/* Messages Container */}
            <div className="messages-container">
                {messages.map((message, index) => (
                    <div 
                        key={index} 
                        className={`message ${message.isUser ? 'user' : 'agent'}`}
                    >
                        <div className="message-content">
                            {message.content}
                            {message.medical_disclaimer && (
                                <div className="medical-disclaimer">
                                    ⚕️ {message.medical_disclaimer}
                                </div>
                            )}
                            {message.safety_warnings && message.safety_warnings.length > 0 && (
                                <div className="safety-warnings">
                                    {message.safety_warnings.map((warning, idx) => (
                                        <div key={idx} className="safety-warning">
                                            ⚠️ {warning}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                        <div className="message-time">
                            {new Date(message.timestamp).toLocaleTimeString([], {
                                hour: '2-digit',
                                minute: '2-digit'
                            })}
                        </div>
                    </div>
                ))}
                
                {isLoading && (
                    <div className="message agent">
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
                    {inputMode === 'text' && (
                        <>
                            <textarea
                                ref={inputRef}
                                value={inputText}
                                onChange={(e) => setInputText(e.target.value)}
                                onKeyPress={handleKeyPress}
                                placeholder={isOffline ? "Offline - Emergency resources available" : "Type your message..."}
                                className="message-input"
                                rows="1"
                                disabled={isOffline}
                            />
                            
                            <div className="input-actions">
                                <button
                                    onClick={handleImageCapture}
                                    className="action-btn"
                                    disabled={isOffline}
                                    title="Take photo"
                                >
                                    <Camera size={20} />
                                </button>
                                
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
                    )}
                    
                    {inputMode === 'voice' && (
                        <div className="voice-recording">
                            <div className="recording-indicator">
                                <div className="pulse"></div>
                                <span>Recording...</span>
                            </div>
                            <button
                                onClick={stopVoiceRecording}
                                className="stop-recording-btn"
                            >
                                Stop
                            </button>
                        </div>
                    )}
                </div>
                
                {/* Emergency Button */}
                <button
                    onClick={() => setShowEmergencyPanel(true)}
                    className="emergency-btn"
                    title="Emergency Resources"
                >
                    <AlertTriangle size={20} />
                </button>
            </div>
            
            {/* Emergency Panel */}
            <EmergencyPanel />
        </div>
    );
};

export default MobileChatInterface;
