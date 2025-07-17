import React, { useState, useEffect } from 'react';
import {
    ChevronRight,
    ChevronLeft,
    Check,
    AlertTriangle,
    Shield,
    Heart,
    Brain,
    Users,
    FileText,
    Phone,
    Info,
    BookOpen,
    Target,
    Clock
} from 'lucide-react';
import {
    SafetyGuidelinesStep,
    SystemLimitationsStep,
    CrisisSupportStep,
    PatientGuideStep,
    ProviderGuideStep,
    InteractionGuideStep,
    WorkflowIntegrationStep
} from './OnboardingSteps';
import './HealthcareOnboarding.css';

const HealthcareOnboarding = ({ userRole, onComplete, onSkip }) => {
    const [currentStep, setCurrentStep] = useState(0);
    const [completedSteps, setCompletedSteps] = useState(new Set());
    const [userAgreements, setUserAgreements] = useState({
        medicalDisclaimer: false,
        privacyPolicy: false,
        safetyGuidelines: false,
        systemLimitations: false
    });

    // Define onboarding steps based on user role
    const getOnboardingSteps = () => {
        const commonSteps = [
            {
                id: 'welcome',
                title: 'Welcome to Sage Healthcare AI',
                icon: <Heart size={32} />,
                component: WelcomeStep
            },
            {
                id: 'safety',
                title: 'Safety Guidelines',
                icon: <Shield size={32} />,
                component: SafetyGuidelinesStep
            },
            {
                id: 'limitations',
                title: 'System Limitations',
                icon: <Info size={32} />,
                component: SystemLimitationsStep
            },
            {
                id: 'crisis',
                title: 'Crisis Support',
                icon: <Phone size={32} />,
                component: CrisisSupportStep
            }
        ];

        const patientSteps = [
            ...commonSteps,
            {
                id: 'patient-guide',
                title: 'How to Use Sage',
                icon: <BookOpen size={32} />,
                component: PatientGuideStep
            },
            {
                id: 'interaction',
                title: 'Interacting with AI',
                icon: <Brain size={32} />,
                component: InteractionGuideStep
            }
        ];

        const providerSteps = [
            ...commonSteps,
            {
                id: 'provider-guide',
                title: 'Clinical Integration',
                icon: <Users size={32} />,
                component: ProviderGuideStep
            },
            {
                id: 'workflow',
                title: 'Workflow Integration',
                icon: <Target size={32} />,
                component: WorkflowIntegrationStep
            }
        ];

        return userRole === 'provider' ? providerSteps : patientSteps;
    };

    const steps = getOnboardingSteps();

    const handleNext = () => {
        if (currentStep < steps.length - 1) {
            setCompletedSteps(prev => new Set([...prev, currentStep]));
            setCurrentStep(currentStep + 1);
        } else {
            handleComplete();
        }
    };

    const handlePrevious = () => {
        if (currentStep > 0) {
            setCurrentStep(currentStep - 1);
        }
    };

    const handleComplete = () => {
        // Check if all required agreements are checked
        const allAgreed = Object.values(userAgreements).every(agreed => agreed);
        if (allAgreed) {
            setCompletedSteps(prev => new Set([...prev, currentStep]));
            onComplete({
                completedSteps: [...completedSteps, currentStep],
                userAgreements,
                completedAt: new Date().toISOString()
            });
        } else {
            alert('Please review and accept all safety guidelines and disclaimers before proceeding.');
        }
    };

    const handleAgreementChange = (agreementType, value) => {
        setUserAgreements(prev => ({
            ...prev,
            [agreementType]: value
        }));
    };

    const CurrentStepComponent = steps[currentStep]?.component;

    return (
        <div className="healthcare-onboarding">
            <div className="onboarding-container">
                {/* Progress Bar */}
                <div className="onboarding-progress">
                    <div className="progress-bar">
                        <div 
                            className="progress-fill"
                            style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
                        />
                    </div>
                    <div className="progress-text">
                        Step {currentStep + 1} of {steps.length}
                    </div>
                </div>

                {/* Step Indicators */}
                <div className="step-indicators">
                    {steps.map((step, index) => (
                        <div 
                            key={step.id}
                            className={`step-indicator ${
                                index === currentStep ? 'active' : 
                                completedSteps.has(index) ? 'completed' : ''
                            }`}
                        >
                            <div className="step-icon">
                                {completedSteps.has(index) ? <Check size={20} /> : step.icon}
                            </div>
                            <div className="step-title">{step.title}</div>
                        </div>
                    ))}
                </div>

                {/* Current Step Content */}
                <div className="step-content">
                    {CurrentStepComponent && (
                        <CurrentStepComponent
                            userRole={userRole}
                            userAgreements={userAgreements}
                            onAgreementChange={handleAgreementChange}
                            onNext={handleNext}
                            onPrevious={handlePrevious}
                            isFirstStep={currentStep === 0}
                            isLastStep={currentStep === steps.length - 1}
                        />
                    )}
                </div>

                {/* Navigation */}
                <div className="onboarding-navigation">
                    <button 
                        className="nav-btn secondary"
                        onClick={onSkip}
                    >
                        Skip Tutorial
                    </button>
                    
                    <div className="nav-controls">
                        <button 
                            className="nav-btn"
                            onClick={handlePrevious}
                            disabled={currentStep === 0}
                        >
                            <ChevronLeft size={20} />
                            Previous
                        </button>
                        
                        <button 
                            className="nav-btn primary"
                            onClick={handleNext}
                        >
                            {currentStep === steps.length - 1 ? 'Complete' : 'Next'}
                            {currentStep !== steps.length - 1 && <ChevronRight size={20} />}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

// Welcome Step Component
const WelcomeStep = ({ userRole, onNext }) => (
    <div className="step-welcome">
        <div className="welcome-header">
            <Heart size={64} className="welcome-icon" />
            <h1>Welcome to Sage Healthcare AI</h1>
            <p className="welcome-subtitle">
                {userRole === 'provider' 
                    ? 'Professional mental health support for healthcare providers'
                    : 'Your personal mental health companion'
                }
            </p>
        </div>
        
        <div className="welcome-content">
            <div className="feature-grid">
                <div className="feature-item">
                    <Brain size={24} />
                    <h3>AI-Powered Support</h3>
                    <p>Advanced AI trained on mental health best practices</p>
                </div>
                <div className="feature-item">
                    <Shield size={24} />
                    <h3>HIPAA Compliant</h3>
                    <p>Your privacy and data security are our top priority</p>
                </div>
                <div className="feature-item">
                    <Phone size={24} />
                    <h3>Crisis Support</h3>
                    <p>24/7 access to emergency mental health resources</p>
                </div>
                <div className="feature-item">
                    <Clock size={24} />
                    <h3>Available Anytime</h3>
                    <p>Get support whenever you need it, day or night</p>
                </div>
            </div>
            
            <div className="welcome-disclaimer">
                <AlertTriangle size={20} />
                <p>
                    <strong>Important:</strong> Sage is a support tool designed to complement, 
                    not replace, professional medical care. In case of emergency, please contact 
                    911 or your local emergency services immediately.
                </p>
            </div>
        </div>
    </div>
);

export default HealthcareOnboarding;
