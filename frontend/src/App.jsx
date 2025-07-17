import React, { useState, useEffect } from 'react';
import HealthcareDashboard from './components/Healthcare/HealthcareDashboard';
import HealthcareChatInterface from './components/Healthcare/HealthcareChatInterface';
import PatientProgressDashboard from './components/Progress/PatientProgressDashboard';
import HealthcareOnboarding from './components/Onboarding/HealthcareOnboarding';
import UserGuide from './components/Onboarding/UserGuide';
import { ContextualHelp, QuickTips } from './components/Onboarding/TooltipSystem';
import './App.css';

const App = () => {
    const [currentView, setCurrentView] = useState('dashboard');
    const [userRole, setUserRole] = useState('patient'); // 'patient' or 'provider'
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isOffline, setIsOffline] = useState(false);
    const [patientId] = useState('P-2024-001'); // This would come from authentication

    // Onboarding state
    const [showOnboarding, setShowOnboarding] = useState(false);
    const [onboardingCompleted, setOnboardingCompleted] = useState(false);
    const [isFirstTimeUser, setIsFirstTimeUser] = useState(true);
    const [showQuickTips, setShowQuickTips] = useState(false);
    const [showUserGuide, setShowUserGuide] = useState(false);

    useEffect(() => {
        // Check online status
        const handleOnline = () => setIsOffline(false);
        const handleOffline = () => setIsOffline(true);

        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);

        // Initial check
        setIsOffline(!navigator.onLine);

        // Check if user has completed onboarding
        const onboardingStatus = localStorage.getItem('sage-onboarding-completed');
        const userFirstTime = localStorage.getItem('sage-first-time-user');

        if (!onboardingStatus) {
            setShowOnboarding(true);
            setIsFirstTimeUser(true);
        } else {
            setOnboardingCompleted(true);
            setIsFirstTimeUser(userFirstTime !== 'false');
        }

        return () => {
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
        };
    }, []);

    const handleSendMessage = async (message, metadata = {}) => {
        if (isOffline) return;

        // Add user message to chat
        const userMessage = {
            content: message,
            isUser: true,
            timestamp: new Date(),
            ...metadata
        };

        setMessages(prev => [...prev, userMessage]);
        setIsLoading(true);

        try {
            // Send message to backend
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message,
                    metadata: {
                        ...metadata,
                        userRole,
                        patientId,
                        sessionId: generateSessionId()
                    }
                })
            });

            if (!response.ok) {
                throw new Error('Failed to send message');
            }

            const data = await response.json();

            // Add AI response to chat
            const aiMessage = {
                content: data.response,
                isUser: false,
                timestamp: new Date(),
                medical_disclaimer: data.medical_disclaimer,
                safety_warnings: data.safety_warnings,
                confidence_score: data.confidence_score
            };

            setMessages(prev => [...prev, aiMessage]);

        } catch (error) {
            console.error('Error sending message:', error);
            
            // Add error message
            const errorMessage = {
                content: "I'm sorry, I'm having trouble connecting right now. Please try again or contact your healthcare provider if this is urgent.",
                isUser: false,
                timestamp: new Date(),
                isError: true
            };

            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const generateSessionId = () => {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    };

    const handleNavigation = (view) => {
        if (view === 'user-guide') {
            setShowUserGuide(true);
        } else {
            setCurrentView(view);
        }
    };

    const handleRoleSwitch = (role) => {
        setUserRole(role);
        // Clear messages when switching roles for privacy
        setMessages([]);

        // Show onboarding for new role if first time
        const roleOnboardingKey = `sage-onboarding-${role}`;
        const roleOnboardingCompleted = localStorage.getItem(roleOnboardingKey);
        if (!roleOnboardingCompleted) {
            setShowOnboarding(true);
        }
    };

    const handleOnboardingComplete = (onboardingData) => {
        setShowOnboarding(false);
        setOnboardingCompleted(true);
        setIsFirstTimeUser(false);

        // Save onboarding completion to localStorage
        localStorage.setItem('sage-onboarding-completed', 'true');
        localStorage.setItem(`sage-onboarding-${userRole}`, 'true');
        localStorage.setItem('sage-first-time-user', 'false');
        localStorage.setItem('sage-onboarding-data', JSON.stringify(onboardingData));

        // Show quick tips for first-time users
        setShowQuickTips(true);
    };

    const handleOnboardingSkip = () => {
        setShowOnboarding(false);
        setOnboardingCompleted(true);

        // Mark as skipped but still first time
        localStorage.setItem('sage-onboarding-completed', 'skipped');
        localStorage.setItem(`sage-onboarding-${userRole}`, 'skipped');
    };

    const getQuickTips = () => {
        const tips = {
            patient: [
                "Start by sharing how you're feeling today - be as specific as possible",
                "Ask Sage for coping strategies when you're feeling overwhelmed",
                "Use the mood tracker regularly to identify patterns in your mental health",
                "Remember: Sage is here to support you, but always seek professional help for serious concerns"
            ],
            provider: [
                "Review patient interactions to identify concerning patterns or progress",
                "Use Sage's insights to inform your treatment planning and clinical decisions",
                "Monitor crisis detection alerts to ensure patient safety",
                "Remember to maintain professional oversight of all AI-assisted care"
            ]
        };
        return tips[userRole] || [];
    };

    const renderCurrentView = () => {
        switch (currentView) {
            case 'dashboard':
                return (
                    <HealthcareDashboard
                        userRole={userRole}
                        patientData={{ patientId }}
                        onNavigate={handleNavigation}
                    />
                );
            case 'chat':
                return (
                    <HealthcareChatInterface
                        userRole={userRole}
                        onSendMessage={handleSendMessage}
                        messages={messages}
                        isLoading={isLoading}
                        isOffline={isOffline}
                        patientId={patientId}
                    />
                );
            case 'progress':
                return (
                    <PatientProgressDashboard
                        userRole={userRole}
                        patientId={patientId}
                        onNavigate={handleNavigation}
                    />
                );
            case 'mood-tracker':
                return (
                    <div className="coming-soon">
                        <h2>Mood Tracker</h2>
                        <p>This feature is coming soon.</p>
                        <button onClick={() => setCurrentView('dashboard')}>
                            Back to Dashboard
                        </button>
                    </div>
                );
            case 'resources':
                return (
                    <div className="coming-soon">
                        <h2>Healthcare Resources</h2>
                        <p>This feature is coming soon.</p>
                        <button onClick={() => setCurrentView('dashboard')}>
                            Back to Dashboard
                        </button>
                    </div>
                );
            case 'emergency':
                return (
                    <div className="emergency-resources">
                        <h2>Crisis Support Resources</h2>
                        <div className="emergency-contacts">
                            <div className="emergency-contact">
                                <h3>National Suicide Prevention Lifeline</h3>
                                <a href="tel:988" className="emergency-number">988</a>
                                <p>24/7 crisis support</p>
                            </div>
                            <div className="emergency-contact">
                                <h3>Crisis Text Line</h3>
                                <a href="sms:741741&body=HOME" className="emergency-number">Text HOME to 741741</a>
                                <p>24/7 text support</p>
                            </div>
                            <div className="emergency-contact">
                                <h3>Emergency Services</h3>
                                <a href="tel:911" className="emergency-number">911</a>
                                <p>Immediate emergency response</p>
                            </div>
                        </div>
                        <button onClick={() => setCurrentView('dashboard')}>
                            Back to Dashboard
                        </button>
                    </div>
                );
            default:
                return (
                    <HealthcareDashboard
                        userRole={userRole}
                        patientData={{ patientId }}
                        onNavigate={handleNavigation}
                    />
                );
        }
    };

    return (
        <div className="app">
            {/* Healthcare Onboarding */}
            {showOnboarding && (
                <HealthcareOnboarding
                    userRole={userRole}
                    onComplete={handleOnboardingComplete}
                    onSkip={handleOnboardingSkip}
                />
            )}

            {/* User Guide */}
            {showUserGuide && (
                <UserGuide
                    userRole={userRole}
                    onClose={() => setShowUserGuide(false)}
                />
            )}

            {/* Quick Tips for First-Time Users */}
            {showQuickTips && onboardingCompleted && (
                <QuickTips
                    tips={getQuickTips()}
                    onDismiss={() => setShowQuickTips(false)}
                />
            )}

            {/* Role Switcher for Development/Testing */}
            {process.env.NODE_ENV === 'development' && (
                <div className="role-switcher">
                    <button
                        className={userRole === 'patient' ? 'active' : ''}
                        onClick={() => handleRoleSwitch('patient')}
                    >
                        Patient View
                    </button>
                    <button
                        className={userRole === 'provider' ? 'active' : ''}
                        onClick={() => handleRoleSwitch('provider')}
                    >
                        Provider View
                    </button>
                </div>
            )}

            {/* Navigation Bar */}
            {currentView !== 'dashboard' && (
                <div className="app-navigation">
                    <button 
                        onClick={() => setCurrentView('dashboard')}
                        className="nav-back-btn"
                    >
                        ← Back to Dashboard
                    </button>
                    <div className="nav-title">
                        Sage Healthcare AI
                    </div>
                </div>
            )}

            {/* Main Content */}
            <main className="app-main">
                {renderCurrentView()}

                {/* Contextual Help */}
                {onboardingCompleted && (
                    <ContextualHelp
                        context={currentView}
                        userRole={userRole}
                        isFirstTime={isFirstTimeUser}
                    />
                )}
            </main>

            {/* Offline Indicator */}
            {isOffline && (
                <div className="offline-indicator">
                    <span>You're offline - Emergency resources still available</span>
                </div>
            )}
        </div>
    );
};

export default App;
