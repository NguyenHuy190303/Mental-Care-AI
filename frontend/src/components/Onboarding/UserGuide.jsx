import React, { useState } from 'react';
import { 
    Book, 
    Shield, 
    AlertTriangle, 
    Heart, 
    Brain, 
    Users, 
    Phone, 
    FileText,
    CheckCircle,
    XCircle,
    Info,
    Target,
    Clock,
    Search,
    ChevronRight,
    ChevronDown,
    X
} from 'lucide-react';
import './UserGuide.css';

const UserGuide = ({ userRole, onClose }) => {
    const [activeSection, setActiveSection] = useState('getting-started');
    const [searchTerm, setSearchTerm] = useState('');
    const [expandedItems, setExpandedItems] = useState(new Set());

    const toggleExpanded = (itemId) => {
        const newExpanded = new Set(expandedItems);
        if (newExpanded.has(itemId)) {
            newExpanded.delete(itemId);
        } else {
            newExpanded.add(itemId);
        }
        setExpandedItems(newExpanded);
    };

    const guideContent = {
        'getting-started': {
            title: 'Getting Started',
            icon: <Book size={20} />,
            content: userRole === 'patient' ? (
                <div className="guide-section">
                    <h3>Welcome to Sage Healthcare AI</h3>
                    <p>Sage is your personal mental health companion, designed to provide support, guidance, and resources whenever you need them.</p>
                    
                    <div className="step-by-step">
                        <h4>Your First Steps:</h4>
                        <div className="step-item">
                            <span className="step-number">1</span>
                            <div>
                                <h5>Complete Your Profile</h5>
                                <p>Share basic information to help Sage provide personalized support</p>
                            </div>
                        </div>
                        <div className="step-item">
                            <span className="step-number">2</span>
                            <div>
                                <h5>Start with a Check-in</h5>
                                <p>Begin by sharing how you're feeling today - be honest and specific</p>
                            </div>
                        </div>
                        <div className="step-item">
                            <span className="step-number">3</span>
                            <div>
                                <h5>Explore Features</h5>
                                <p>Try mood tracking, coping strategies, and resource library</p>
                            </div>
                        </div>
                        <div className="step-item">
                            <span className="step-number">4</span>
                            <div>
                                <h5>Set Regular Check-ins</h5>
                                <p>Use Sage consistently for better support and progress tracking</p>
                            </div>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="guide-section">
                    <h3>Clinical Integration Guide</h3>
                    <p>Learn how to effectively integrate Sage into your clinical practice for enhanced patient care.</p>
                    
                    <div className="clinical-workflow">
                        <h4>Clinical Workflow Integration:</h4>
                        <div className="workflow-step">
                            <Clock size={16} />
                            <div>
                                <h5>Pre-Session Preparation</h5>
                                <p>Review patient's AI interactions, mood patterns, and progress reports</p>
                            </div>
                        </div>
                        <div className="workflow-step">
                            <Clock size={16} />
                            <div>
                                <h5>During Sessions</h5>
                                <p>Reference AI-generated insights and patient self-reported data</p>
                            </div>
                        </div>
                        <div className="workflow-step">
                            <Clock size={16} />
                            <div>
                                <h5>Post-Session</h5>
                                <p>Update treatment plans and configure AI support parameters</p>
                            </div>
                        </div>
                    </div>
                </div>
            )
        },
        'safety': {
            title: 'Safety Guidelines',
            icon: <Shield size={20} />,
            content: (
                <div className="guide-section">
                    <h3>Safety & Crisis Support</h3>
                    
                    <div className="safety-alert">
                        <AlertTriangle size={24} />
                        <div>
                            <h4>Emergency Situations</h4>
                            <p>If you are in immediate danger or having thoughts of self-harm, call 911 or go to your nearest emergency room immediately.</p>
                        </div>
                    </div>

                    <div className="crisis-resources">
                        <h4>Crisis Support Resources</h4>
                        <div className="resource-grid">
                            <div className="resource-item">
                                <Phone size={20} />
                                <h5>988 Suicide & Crisis Lifeline</h5>
                                <p>Call or text 988 • Available 24/7</p>
                            </div>
                            <div className="resource-item">
                                <FileText size={20} />
                                <h5>Crisis Text Line</h5>
                                <p>Text HOME to 741741 • Available 24/7</p>
                            </div>
                        </div>
                    </div>

                    <div className="when-to-seek-help">
                        <h4>When to Seek Professional Help</h4>
                        <ul>
                            <li>Persistent thoughts of self-harm or suicide</li>
                            <li>Severe depression or anxiety affecting daily life</li>
                            <li>Substance abuse concerns</li>
                            <li>Symptoms of psychosis or severe mental health episodes</li>
                            <li>Any situation requiring immediate medical attention</li>
                        </ul>
                    </div>
                </div>
            )
        },
        'features': {
            title: 'Features & Tools',
            icon: <Brain size={20} />,
            content: (
                <div className="guide-section">
                    <h3>Sage Features & Tools</h3>
                    
                    <div className="feature-list">
                        <div className="feature-item">
                            <Heart size={20} />
                            <div>
                                <h4>AI Chat Support</h4>
                                <p>24/7 conversational support with evidence-based responses</p>
                                <div className="feature-tips">
                                    <strong>Tips:</strong>
                                    <ul>
                                        <li>Be specific about your feelings and situations</li>
                                        <li>Ask for coping strategies or techniques</li>
                                        <li>Provide feedback on suggestions</li>
                                    </ul>
                                </div>
                            </div>
                        </div>

                        <div className="feature-item">
                            <Target size={20} />
                            <div>
                                <h4>Mood Tracking</h4>
                                <p>Track your emotional patterns and identify triggers</p>
                                <div className="feature-tips">
                                    <strong>Tips:</strong>
                                    <ul>
                                        <li>Log your mood daily for better insights</li>
                                        <li>Note activities and events that affect your mood</li>
                                        <li>Review patterns with your healthcare provider</li>
                                    </ul>
                                </div>
                            </div>
                        </div>

                        <div className="feature-item">
                            <FileText size={20} />
                            <div>
                                <h4>Resource Library</h4>
                                <p>Access evidence-based mental health resources and exercises</p>
                                <div className="feature-tips">
                                    <strong>Tips:</strong>
                                    <ul>
                                        <li>Explore different coping strategies</li>
                                        <li>Practice mindfulness and relaxation exercises</li>
                                        <li>Save resources that work for you</li>
                                    </ul>
                                </div>
                            </div>
                        </div>

                        {userRole === 'provider' && (
                            <div className="feature-item">
                                <Users size={20} />
                                <div>
                                    <h4>Patient Monitoring</h4>
                                    <p>Track patient progress and identify concerning patterns</p>
                                    <div className="feature-tips">
                                        <strong>Clinical Use:</strong>
                                        <ul>
                                            <li>Review patient interaction summaries</li>
                                            <li>Monitor crisis detection alerts</li>
                                            <li>Track treatment outcome metrics</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )
        },
        'limitations': {
            title: 'System Limitations',
            icon: <Info size={20} />,
            content: (
                <div className="guide-section">
                    <h3>Understanding Sage's Limitations</h3>
                    
                    <div className="limitations-grid">
                        <div className="limitation-card can-do">
                            <CheckCircle size={24} />
                            <h4>What Sage CAN Do</h4>
                            <ul>
                                <li>Provide emotional support and coping strategies</li>
                                <li>Help track mood and mental health patterns</li>
                                <li>Offer evidence-based mental health information</li>
                                <li>Guide through relaxation exercises</li>
                                <li>Support between therapy appointments</li>
                                <li>Provide crisis resources and emergency contacts</li>
                            </ul>
                        </div>

                        <div className="limitation-card cannot-do">
                            <XCircle size={24} />
                            <h4>What Sage CANNOT Do</h4>
                            <ul>
                                <li>Diagnose mental health conditions</li>
                                <li>Prescribe medications or treatments</li>
                                <li>Replace professional therapy or counseling</li>
                                <li>Provide emergency crisis intervention</li>
                                <li>Make medical decisions about your care</li>
                                <li>Handle complex trauma without professional support</li>
                            </ul>
                        </div>
                    </div>

                    <div className="important-reminder">
                        <AlertTriangle size={20} />
                        <div>
                            <h4>Important Reminder</h4>
                            <p>Sage is designed to complement, not replace, professional mental health care. Always consult with qualified healthcare providers for medical advice, diagnosis, or treatment.</p>
                        </div>
                    </div>
                </div>
            )
        },
        'privacy': {
            title: 'Privacy & Security',
            icon: <Shield size={20} />,
            content: (
                <div className="guide-section">
                    <h3>Your Privacy & Data Security</h3>
                    
                    <div className="privacy-section">
                        <h4>HIPAA Compliance</h4>
                        <p>Sage is designed to meet HIPAA standards for protecting your health information:</p>
                        <ul>
                            <li>All conversations are encrypted in transit and at rest</li>
                            <li>Your data is stored securely and never shared without consent</li>
                            <li>Access is limited to authorized healthcare providers only</li>
                            <li>You can request data deletion at any time</li>
                        </ul>
                    </div>

                    <div className="privacy-section">
                        <h4>Data Usage</h4>
                        <p>Here's how your data is used:</p>
                        <ul>
                            <li><strong>Personalization:</strong> To provide tailored support and recommendations</li>
                            <li><strong>Progress Tracking:</strong> To monitor your mental health journey</li>
                            <li><strong>Safety:</strong> To detect crisis situations and provide appropriate resources</li>
                            <li><strong>Quality Improvement:</strong> Anonymized data may be used to improve Sage's capabilities</li>
                        </ul>
                    </div>

                    <div className="privacy-section">
                        <h4>Your Rights</h4>
                        <ul>
                            <li>Access your personal data and conversation history</li>
                            <li>Request corrections to inaccurate information</li>
                            <li>Delete your account and associated data</li>
                            <li>Opt out of data sharing for research purposes</li>
                        </ul>
                    </div>
                </div>
            )
        }
    };

    const sidebarItems = Object.keys(guideContent).map(key => ({
        id: key,
        ...guideContent[key]
    }));

    const filteredItems = sidebarItems.filter(item =>
        item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.content.props.children.some(child => 
            typeof child === 'string' && child.toLowerCase().includes(searchTerm.toLowerCase())
        )
    );

    return (
        <div className="user-guide-overlay">
            <div className="user-guide-container">
                <div className="guide-header">
                    <div className="header-content">
                        <h2>Sage User Guide</h2>
                        <span className="user-role-badge">{userRole === 'provider' ? 'Healthcare Provider' : 'Patient'} Guide</span>
                    </div>
                    <button className="close-guide" onClick={onClose}>
                        <X size={24} />
                    </button>
                </div>

                <div className="guide-content">
                    <div className="guide-sidebar">
                        <div className="search-box">
                            <Search size={16} />
                            <input
                                type="text"
                                placeholder="Search guide..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </div>

                        <nav className="guide-nav">
                            {filteredItems.map(item => (
                                <button
                                    key={item.id}
                                    className={`nav-item ${activeSection === item.id ? 'active' : ''}`}
                                    onClick={() => setActiveSection(item.id)}
                                >
                                    {item.icon}
                                    <span>{item.title}</span>
                                    <ChevronRight size={16} />
                                </button>
                            ))}
                        </nav>
                    </div>

                    <div className="guide-main">
                        {guideContent[activeSection]?.content}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default UserGuide;
