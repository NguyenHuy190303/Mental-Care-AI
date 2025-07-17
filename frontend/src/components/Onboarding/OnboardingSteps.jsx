import React from 'react';
import { 
    AlertTriangle, 
    Shield, 
    Phone, 
    Info, 
    BookOpen, 
    Brain,
    Users,
    Target,
    CheckCircle,
    XCircle,
    Clock,
    Heart,
    FileText
} from 'lucide-react';

// Safety Guidelines Step
export const SafetyGuidelinesStep = ({ userAgreements, onAgreementChange }) => (
    <div className="step-safety">
        <div className="step-header">
            <Shield size={48} className="step-icon" />
            <h2>Safety Guidelines</h2>
            <p>Please review these important safety guidelines before using Sage</p>
        </div>
        
        <div className="safety-content">
            <div className="safety-section">
                <h3><AlertTriangle size={20} /> Emergency Situations</h3>
                <div className="safety-list">
                    <div className="safety-item">
                        <strong>Immediate Danger:</strong> If you are in immediate danger or having thoughts of self-harm, 
                        call 911 or go to your nearest emergency room immediately.
                    </div>
                    <div className="safety-item">
                        <strong>Crisis Support:</strong> For mental health crises, contact the 988 Suicide & Crisis Lifeline 
                        by calling or texting 988, available 24/7.
                    </div>
                    <div className="safety-item">
                        <strong>Text Support:</strong> Text HOME to 741741 for the Crisis Text Line, 
                        available 24/7 for crisis support via text.
                    </div>
                </div>
            </div>

            <div className="safety-section">
                <h3><Heart size={20} /> When to Seek Professional Help</h3>
                <div className="safety-list">
                    <div className="safety-item">
                        • Persistent thoughts of self-harm or suicide
                    </div>
                    <div className="safety-item">
                        • Severe depression or anxiety that interferes with daily life
                    </div>
                    <div className="safety-item">
                        • Substance abuse or addiction concerns
                    </div>
                    <div className="safety-item">
                        • Symptoms of psychosis or severe mental health episodes
                    </div>
                    <div className="safety-item">
                        • Any situation requiring immediate medical attention
                    </div>
                </div>
            </div>

            <div className="safety-section">
                <h3><Shield size={20} /> Privacy & Confidentiality</h3>
                <div className="safety-list">
                    <div className="safety-item">
                        • Your conversations are encrypted and HIPAA-compliant
                    </div>
                    <div className="safety-item">
                        • We may need to break confidentiality if there's imminent danger
                    </div>
                    <div className="safety-item">
                        • Your data is never shared without your explicit consent
                    </div>
                    <div className="safety-item">
                        • You can request data deletion at any time
                    </div>
                </div>
            </div>
        </div>

        <div className="agreement-section">
            <label className="agreement-checkbox">
                <input
                    type="checkbox"
                    checked={userAgreements.safetyGuidelines}
                    onChange={(e) => onAgreementChange('safetyGuidelines', e.target.checked)}
                />
                <span className="checkmark"></span>
                I have read and understand the safety guidelines above
            </label>
        </div>
    </div>
);

// System Limitations Step
export const SystemLimitationsStep = ({ userAgreements, onAgreementChange }) => (
    <div className="step-limitations">
        <div className="step-header">
            <Info size={48} className="step-icon" />
            <h2>Understanding System Limitations</h2>
            <p>It's important to understand what Sage can and cannot do</p>
        </div>
        
        <div className="limitations-content">
            <div className="limitations-grid">
                <div className="limitation-card can-do">
                    <CheckCircle size={24} className="card-icon" />
                    <h3>What Sage CAN Do</h3>
                    <ul>
                        <li>Provide emotional support and coping strategies</li>
                        <li>Help you track mood and mental health patterns</li>
                        <li>Offer evidence-based mental health information</li>
                        <li>Guide you through relaxation and mindfulness exercises</li>
                        <li>Help you prepare for therapy sessions</li>
                        <li>Provide crisis resources and emergency contacts</li>
                        <li>Support between therapy appointments</li>
                    </ul>
                </div>

                <div className="limitation-card cannot-do">
                    <XCircle size={24} className="card-icon" />
                    <h3>What Sage CANNOT Do</h3>
                    <ul>
                        <li>Diagnose mental health conditions</li>
                        <li>Prescribe medications or medical treatments</li>
                        <li>Replace professional therapy or counseling</li>
                        <li>Provide emergency crisis intervention</li>
                        <li>Make decisions about your medical care</li>
                        <li>Guarantee specific therapeutic outcomes</li>
                        <li>Handle complex trauma without professional support</li>
                    </ul>
                </div>
            </div>

            <div className="important-notice">
                <AlertTriangle size={24} />
                <div>
                    <h4>Important Notice</h4>
                    <p>
                        Sage is an AI-powered support tool designed to complement professional mental health care. 
                        It is not a substitute for professional medical advice, diagnosis, or treatment. 
                        Always seek the advice of qualified healthcare providers with any questions you may have 
                        regarding a medical condition or mental health concern.
                    </p>
                </div>
            </div>
        </div>

        <div className="agreement-section">
            <label className="agreement-checkbox">
                <input
                    type="checkbox"
                    checked={userAgreements.systemLimitations}
                    onChange={(e) => onAgreementChange('systemLimitations', e.target.checked)}
                />
                <span className="checkmark"></span>
                I understand the limitations of this AI system and will seek professional help when needed
            </label>
        </div>
    </div>
);

// Crisis Support Step
export const CrisisSupportStep = ({ userAgreements, onAgreementChange }) => (
    <div className="step-crisis">
        <div className="step-header">
            <Phone size={48} className="step-icon" />
            <h2>Crisis Support Resources</h2>
            <p>Know where to get help when you need it most</p>
        </div>
        
        <div className="crisis-content">
            <div className="crisis-resources">
                <div className="resource-card emergency">
                    <div className="resource-header">
                        <AlertTriangle size={24} />
                        <h3>Immediate Emergency</h3>
                    </div>
                    <div className="resource-contact">
                        <strong>Call 911</strong>
                        <p>For immediate danger or medical emergencies</p>
                    </div>
                </div>

                <div className="resource-card crisis">
                    <div className="resource-header">
                        <Phone size={24} />
                        <h3>Crisis Support</h3>
                    </div>
                    <div className="resource-contact">
                        <strong>988 Suicide & Crisis Lifeline</strong>
                        <p>Call or text 988 • Available 24/7</p>
                        <p>Free, confidential support for people in distress</p>
                    </div>
                </div>

                <div className="resource-card text">
                    <div className="resource-header">
                        <FileText size={24} />
                        <h3>Text Support</h3>
                    </div>
                    <div className="resource-contact">
                        <strong>Crisis Text Line</strong>
                        <p>Text HOME to 741741 • Available 24/7</p>
                        <p>Free crisis support via text message</p>
                    </div>
                </div>

                <div className="resource-card online">
                    <div className="resource-header">
                        <Heart size={24} />
                        <h3>Online Support</h3>
                    </div>
                    <div className="resource-contact">
                        <strong>National Suicide Prevention Lifeline</strong>
                        <p>suicidepreventionlifeline.org</p>
                        <p>Online chat and additional resources</p>
                    </div>
                </div>
            </div>

            <div className="crisis-notice">
                <h4>How Sage Helps in Crisis</h4>
                <p>
                    If Sage detects language indicating a mental health crisis, it will:
                </p>
                <ul>
                    <li>Immediately display crisis resources and emergency contacts</li>
                    <li>Encourage you to reach out to professional help</li>
                    <li>Provide immediate coping strategies while you seek help</li>
                    <li>Never replace emergency services or professional crisis intervention</li>
                </ul>
            </div>
        </div>

        <div className="agreement-section">
            <label className="agreement-checkbox">
                <input
                    type="checkbox"
                    checked={userAgreements.medicalDisclaimer}
                    onChange={(e) => onAgreementChange('medicalDisclaimer', e.target.checked)}
                />
                <span className="checkmark"></span>
                I understand the crisis support resources and will use them when needed
            </label>
        </div>
    </div>
);

// Patient Guide Step
export const PatientGuideStep = ({ userAgreements, onAgreementChange }) => (
    <div className="step-patient-guide">
        <div className="step-header">
            <BookOpen size={48} className="step-icon" />
            <h2>How to Use Sage Effectively</h2>
            <p>Learn how to get the most out of your mental health support</p>
        </div>
        
        <div className="guide-content">
            <div className="guide-section">
                <h3><Brain size={20} /> Getting Started</h3>
                <div className="guide-steps">
                    <div className="guide-step">
                        <span className="step-number">1</span>
                        <div>
                            <h4>Start with Check-ins</h4>
                            <p>Begin each session by sharing how you're feeling today</p>
                        </div>
                    </div>
                    <div className="guide-step">
                        <span className="step-number">2</span>
                        <div>
                            <h4>Be Honest and Open</h4>
                            <p>The more honest you are, the better Sage can support you</p>
                        </div>
                    </div>
                    <div className="guide-step">
                        <span className="step-number">3</span>
                        <div>
                            <h4>Ask Specific Questions</h4>
                            <p>Ask about coping strategies, techniques, or specific concerns</p>
                        </div>
                    </div>
                </div>
            </div>

            <div className="guide-section">
                <h3><Heart size={20} /> Best Practices</h3>
                <div className="best-practices">
                    <div className="practice-item">
                        <strong>Regular Use:</strong> Use Sage consistently for better support and tracking
                    </div>
                    <div className="practice-item">
                        <strong>Combine with Therapy:</strong> Use Sage between therapy sessions for continued support
                    </div>
                    <div className="practice-item">
                        <strong>Track Progress:</strong> Use mood tracking features to monitor your mental health
                    </div>
                    <div className="practice-item">
                        <strong>Practice Techniques:</strong> Try the coping strategies and exercises Sage suggests
                    </div>
                </div>
            </div>
        </div>
    </div>
);

// Provider Guide Step
export const ProviderGuideStep = ({ userAgreements, onAgreementChange }) => (
    <div className="step-provider-guide">
        <div className="step-header">
            <Users size={48} className="step-icon" />
            <h2>Clinical Integration Guide</h2>
            <p>How to integrate Sage into your clinical practice</p>
        </div>
        
        <div className="guide-content">
            <div className="guide-section">
                <h3><Target size={20} /> Clinical Applications</h3>
                <div className="clinical-applications">
                    <div className="application-item">
                        <h4>Patient Monitoring</h4>
                        <p>Track patient progress between sessions and identify concerning patterns</p>
                    </div>
                    <div className="application-item">
                        <h4>Treatment Support</h4>
                        <p>Provide patients with 24/7 access to coping strategies and support</p>
                    </div>
                    <div className="application-item">
                        <h4>Crisis Prevention</h4>
                        <p>Early detection of crisis indicators and automatic resource provision</p>
                    </div>
                    <div className="application-item">
                        <h4>Documentation</h4>
                        <p>Generate session summaries and progress reports for clinical records</p>
                    </div>
                </div>
            </div>

            <div className="guide-section">
                <h3><Shield size={20} /> Professional Standards</h3>
                <div className="standards-list">
                    <div className="standard-item">
                        • Always maintain professional oversight of AI-assisted care
                    </div>
                    <div className="standard-item">
                        • Review AI recommendations before implementing in treatment plans
                    </div>
                    <div className="standard-item">
                        • Use Sage as a supplement to, not replacement for, clinical judgment
                    </div>
                    <div className="standard-item">
                        • Ensure patients understand the role of AI in their care
                    </div>
                </div>
            </div>
        </div>
    </div>
);

// Interaction Guide Step
export const InteractionGuideStep = () => (
    <div className="step-interaction">
        <div className="step-header">
            <Brain size={48} className="step-icon" />
            <h2>Interacting with AI</h2>
            <p>Tips for effective communication with Sage</p>
        </div>
        
        <div className="interaction-content">
            <div className="interaction-tips">
                <div className="tip-card">
                    <h4>Be Specific</h4>
                    <p>Instead of "I feel bad," try "I'm feeling anxious about my upcoming presentation"</p>
                </div>
                <div className="tip-card">
                    <h4>Ask for Examples</h4>
                    <p>Request specific coping strategies or ask for step-by-step guidance</p>
                </div>
                <div className="tip-card">
                    <h4>Provide Context</h4>
                    <p>Share relevant background information to help Sage understand your situation</p>
                </div>
                <div className="tip-card">
                    <h4>Follow Up</h4>
                    <p>Let Sage know if suggestions are helpful or if you need different approaches</p>
                </div>
            </div>
        </div>
    </div>
);

// Workflow Integration Step
export const WorkflowIntegrationStep = () => (
    <div className="step-workflow">
        <div className="step-header">
            <Target size={48} className="step-icon" />
            <h2>Workflow Integration</h2>
            <p>Seamlessly integrate Sage into your clinical workflow</p>
        </div>
        
        <div className="workflow-content">
            <div className="workflow-steps">
                <div className="workflow-step">
                    <Clock size={24} />
                    <h4>Pre-Session</h4>
                    <p>Review patient's AI interactions and mood tracking data</p>
                </div>
                <div className="workflow-step">
                    <Clock size={24} />
                    <h4>During Session</h4>
                    <p>Reference AI-generated insights and patient progress reports</p>
                </div>
                <div className="workflow-step">
                    <Clock size={24} />
                    <h4>Post-Session</h4>
                    <p>Update treatment plans and configure AI support for between sessions</p>
                </div>
            </div>
        </div>
    </div>
);
