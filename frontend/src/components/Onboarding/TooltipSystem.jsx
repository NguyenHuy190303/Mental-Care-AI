import React, { useState, useEffect, useRef } from 'react';
import { HelpCircle, X, ChevronRight, ChevronLeft } from 'lucide-react';
import './TooltipSystem.css';

// Individual Tooltip Component
export const Tooltip = ({ 
    children, 
    content, 
    position = 'top', 
    trigger = 'hover',
    className = '',
    disabled = false 
}) => {
    const [isVisible, setIsVisible] = useState(false);
    const [actualPosition, setActualPosition] = useState(position);
    const tooltipRef = useRef(null);
    const triggerRef = useRef(null);

    useEffect(() => {
        if (isVisible && tooltipRef.current && triggerRef.current) {
            const tooltip = tooltipRef.current;
            const trigger = triggerRef.current;
            const rect = trigger.getBoundingClientRect();
            const tooltipRect = tooltip.getBoundingClientRect();
            
            // Check if tooltip would go off screen and adjust position
            let newPosition = position;
            
            if (position === 'top' && rect.top - tooltipRect.height < 10) {
                newPosition = 'bottom';
            } else if (position === 'bottom' && rect.bottom + tooltipRect.height > window.innerHeight - 10) {
                newPosition = 'top';
            } else if (position === 'left' && rect.left - tooltipRect.width < 10) {
                newPosition = 'right';
            } else if (position === 'right' && rect.right + tooltipRect.width > window.innerWidth - 10) {
                newPosition = 'left';
            }
            
            setActualPosition(newPosition);
        }
    }, [isVisible, position]);

    const handleMouseEnter = () => {
        if (trigger === 'hover' && !disabled) {
            setIsVisible(true);
        }
    };

    const handleMouseLeave = () => {
        if (trigger === 'hover' && !disabled) {
            setIsVisible(false);
        }
    };

    const handleClick = () => {
        if (trigger === 'click' && !disabled) {
            setIsVisible(!isVisible);
        }
    };

    if (disabled) {
        return children;
    }

    return (
        <div 
            className={`tooltip-container ${className}`}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
            onClick={handleClick}
            ref={triggerRef}
        >
            {children}
            {isVisible && (
                <div 
                    ref={tooltipRef}
                    className={`tooltip tooltip-${actualPosition}`}
                    role="tooltip"
                >
                    <div className="tooltip-content">
                        {content}
                    </div>
                    <div className="tooltip-arrow" />
                </div>
            )}
        </div>
    );
};

// Interactive Tutorial System
export const InteractiveTutorial = ({ 
    steps, 
    isActive, 
    onComplete, 
    onSkip,
    autoStart = false 
}) => {
    const [currentStep, setCurrentStep] = useState(0);
    const [isVisible, setIsVisible] = useState(isActive);
    const overlayRef = useRef(null);

    useEffect(() => {
        setIsVisible(isActive);
        if (isActive && autoStart) {
            setCurrentStep(0);
        }
    }, [isActive, autoStart]);

    const currentStepData = steps[currentStep];

    const handleNext = () => {
        if (currentStep < steps.length - 1) {
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
        setIsVisible(false);
        onComplete();
    };

    const handleSkip = () => {
        setIsVisible(false);
        onSkip();
    };

    if (!isVisible || !currentStepData) {
        return null;
    }

    return (
        <div className="tutorial-overlay" ref={overlayRef}>
            {/* Highlight target element */}
            {currentStepData.target && (
                <div 
                    className="tutorial-highlight"
                    style={{
                        top: currentStepData.target.top,
                        left: currentStepData.target.left,
                        width: currentStepData.target.width,
                        height: currentStepData.target.height
                    }}
                />
            )}
            
            {/* Tutorial popup */}
            <div 
                className={`tutorial-popup tutorial-${currentStepData.position || 'center'}`}
                style={currentStepData.popupStyle}
            >
                <div className="tutorial-header">
                    <div className="tutorial-progress">
                        Step {currentStep + 1} of {steps.length}
                    </div>
                    <button 
                        className="tutorial-close"
                        onClick={handleSkip}
                        aria-label="Close tutorial"
                    >
                        <X size={16} />
                    </button>
                </div>
                
                <div className="tutorial-content">
                    {currentStepData.icon && (
                        <div className="tutorial-icon">
                            {currentStepData.icon}
                        </div>
                    )}
                    <h3 className="tutorial-title">{currentStepData.title}</h3>
                    <p className="tutorial-description">{currentStepData.description}</p>
                    
                    {currentStepData.tips && (
                        <div className="tutorial-tips">
                            <h4>Tips:</h4>
                            <ul>
                                {currentStepData.tips.map((tip, index) => (
                                    <li key={index}>{tip}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
                
                <div className="tutorial-navigation">
                    <button 
                        className="tutorial-btn secondary"
                        onClick={handleSkip}
                    >
                        Skip Tutorial
                    </button>
                    
                    <div className="tutorial-nav-controls">
                        <button 
                            className="tutorial-btn"
                            onClick={handlePrevious}
                            disabled={currentStep === 0}
                        >
                            <ChevronLeft size={16} />
                            Previous
                        </button>
                        
                        <button 
                            className="tutorial-btn primary"
                            onClick={handleNext}
                        >
                            {currentStep === steps.length - 1 ? 'Finish' : 'Next'}
                            {currentStep !== steps.length - 1 && <ChevronRight size={16} />}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

// Help Button Component
export const HelpButton = ({ 
    helpContent, 
    position = 'bottom-right',
    className = '' 
}) => {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className={`help-button-container ${className}`}>
            <button 
                className="help-button"
                onClick={() => setIsOpen(!isOpen)}
                aria-label="Get help"
            >
                <HelpCircle size={20} />
            </button>
            
            {isOpen && (
                <div className={`help-popup help-${position}`}>
                    <div className="help-header">
                        <h4>Help</h4>
                        <button 
                            className="help-close"
                            onClick={() => setIsOpen(false)}
                        >
                            <X size={16} />
                        </button>
                    </div>
                    <div className="help-content">
                        {helpContent}
                    </div>
                </div>
            )}
        </div>
    );
};

// Contextual Help System
export const ContextualHelp = ({ 
    context, 
    userRole, 
    isFirstTime = false 
}) => {
    const getHelpContent = () => {
        const helpData = {
            dashboard: {
                patient: {
                    title: "Your Dashboard",
                    content: "This is your personal mental health dashboard. Here you can start new sessions, track your mood, and access resources.",
                    tips: [
                        "Start with a mood check-in to help Sage understand how you're feeling",
                        "Use the quick actions to access different features",
                        "Your recent sessions are saved for continuity"
                    ]
                },
                provider: {
                    title: "Provider Dashboard",
                    content: "Monitor patient progress, manage care plans, and access clinical tools.",
                    tips: [
                        "Review patient queue for upcoming sessions",
                        "Check alerts for patients requiring attention",
                        "Use analytics to track treatment outcomes"
                    ]
                }
            },
            chat: {
                patient: {
                    title: "Chat with Sage",
                    content: "Communicate openly with Sage about your mental health concerns. The AI is trained to provide supportive, evidence-based responses.",
                    tips: [
                        "Be specific about your feelings and situations",
                        "Ask for coping strategies or techniques",
                        "Let Sage know if suggestions are helpful"
                    ]
                },
                provider: {
                    title: "Clinical Chat Interface",
                    content: "Use this interface to demonstrate Sage's capabilities to patients or for clinical consultation.",
                    tips: [
                        "Review AI responses for clinical appropriateness",
                        "Use insights to inform treatment planning",
                        "Monitor for crisis indicators"
                    ]
                }
            }
        };

        return helpData[context]?.[userRole] || null;
    };

    const helpContent = getHelpContent();

    if (!helpContent) {
        return null;
    }

    return (
        <div className="contextual-help">
            {isFirstTime && (
                <div className="first-time-banner">
                    <div className="banner-content">
                        <HelpCircle size={20} />
                        <span>New to this feature? Click the help button for guidance.</span>
                    </div>
                </div>
            )}
            
            <HelpButton 
                helpContent={
                    <div>
                        <h5>{helpContent.title}</h5>
                        <p>{helpContent.content}</p>
                        {helpContent.tips && (
                            <div>
                                <strong>Tips:</strong>
                                <ul>
                                    {helpContent.tips.map((tip, index) => (
                                        <li key={index}>{tip}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                }
            />
        </div>
    );
};

// Quick Tips Component
export const QuickTips = ({ tips, onDismiss }) => {
    const [currentTip, setCurrentTip] = useState(0);
    const [isDismissed, setIsDismissed] = useState(false);

    const handleNext = () => {
        if (currentTip < tips.length - 1) {
            setCurrentTip(currentTip + 1);
        } else {
            handleDismiss();
        }
    };

    const handleDismiss = () => {
        setIsDismissed(true);
        onDismiss();
    };

    if (isDismissed || !tips || tips.length === 0) {
        return null;
    }

    return (
        <div className="quick-tips">
            <div className="tip-content">
                <div className="tip-header">
                    <span className="tip-label">Tip {currentTip + 1} of {tips.length}</span>
                    <button onClick={handleDismiss} className="tip-close">
                        <X size={14} />
                    </button>
                </div>
                <p className="tip-text">{tips[currentTip]}</p>
                <div className="tip-navigation">
                    <button onClick={handleNext} className="tip-next">
                        {currentTip === tips.length - 1 ? 'Got it!' : 'Next tip'}
                    </button>
                </div>
            </div>
        </div>
    );
};
