import React, { useState, useEffect } from 'react';
import {
    Activity,
    Users,
    Calendar,
    FileText,
    AlertTriangle,
    Shield,
    Heart,
    Brain,
    TrendingUp,
    Clock,
    User,
    Settings,
    BookOpen,
    HelpCircle,
    BarChart3
} from 'lucide-react';
import './HealthcareDashboard.css';

const HealthcareDashboard = ({ userRole = 'patient', patientData, onNavigate }) => {
    const [activeTab, setActiveTab] = useState('overview');
    const [notifications, setNotifications] = useState([]);
    const [recentSessions, setRecentSessions] = useState([]);

    useEffect(() => {
        // Load dashboard data based on user role
        loadDashboardData();
    }, [userRole]);

    const loadDashboardData = async () => {
        try {
            // Fetch notifications and recent sessions
            // This would connect to your backend API
            setNotifications([
                {
                    id: 1,
                    type: 'appointment',
                    message: 'Upcoming session scheduled for tomorrow at 2:00 PM',
                    priority: 'medium',
                    timestamp: new Date()
                },
                {
                    id: 2,
                    type: 'progress',
                    message: 'Weekly progress report is ready for review',
                    priority: 'low',
                    timestamp: new Date()
                }
            ]);

            setRecentSessions([
                {
                    id: 1,
                    date: '2024-01-15',
                    duration: '45 min',
                    mood: 'positive',
                    notes: 'Good progress on anxiety management techniques'
                },
                {
                    id: 2,
                    date: '2024-01-12',
                    duration: '30 min',
                    mood: 'neutral',
                    notes: 'Discussed coping strategies for work stress'
                }
            ]);
        } catch (error) {
            console.error('Error loading dashboard data:', error);
        }
    };

    const PatientOverview = () => (
        <div className="dashboard-section">
            <div className="section-header">
                <h2>Your Mental Health Journey</h2>
                <p>Track your progress and access support resources</p>
            </div>

            <div className="stats-grid">
                <div className="stat-card primary">
                    <div className="stat-icon">
                        <Heart size={24} />
                    </div>
                    <div className="stat-content">
                        <h3>Wellness Score</h3>
                        <div className="stat-value">7.2/10</div>
                        <div className="stat-trend positive">
                            <TrendingUp size={16} />
                            +0.5 this week
                        </div>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon">
                        <Calendar size={24} />
                    </div>
                    <div className="stat-content">
                        <h3>Sessions This Month</h3>
                        <div className="stat-value">8</div>
                        <div className="stat-subtitle">4 remaining</div>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon">
                        <Clock size={24} />
                    </div>
                    <div className="stat-content">
                        <h3>Total Time</h3>
                        <div className="stat-value">6.5 hrs</div>
                        <div className="stat-subtitle">This month</div>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon">
                        <Brain size={24} />
                    </div>
                    <div className="stat-content">
                        <h3>Mood Trend</h3>
                        <div className="stat-value">Improving</div>
                        <div className="stat-trend positive">
                            <TrendingUp size={16} />
                            Stable pattern
                        </div>
                    </div>
                </div>
            </div>

            <div className="dashboard-grid">
                <div className="dashboard-card">
                    <h3>Recent Sessions</h3>
                    <div className="sessions-list">
                        {recentSessions.map(session => (
                            <div key={session.id} className="session-item">
                                <div className="session-date">{session.date}</div>
                                <div className="session-details">
                                    <span className="session-duration">{session.duration}</span>
                                    <span className={`mood-indicator ${session.mood}`}>
                                        {session.mood}
                                    </span>
                                </div>
                                <div className="session-notes">{session.notes}</div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="dashboard-card">
                    <h3>Quick Actions</h3>
                    <div className="quick-actions">
                        <button
                            className="action-btn primary"
                            onClick={() => onNavigate('chat')}
                        >
                            <Brain size={20} />
                            Start Session
                        </button>
                        <button
                            className="action-btn"
                            onClick={() => onNavigate('progress')}
                        >
                            <BarChart3 size={20} />
                            Progress Dashboard
                        </button>
                        <button 
                            className="action-btn"
                            onClick={() => onNavigate('mood-tracker')}
                        >
                            <Heart size={20} />
                            Log Mood
                        </button>
                        <button
                            className="action-btn"
                            onClick={() => onNavigate('resources')}
                        >
                            <FileText size={20} />
                            Resources
                        </button>
                        <button
                            className="action-btn"
                            onClick={() => onNavigate('user-guide')}
                        >
                            <BookOpen size={20} />
                            User Guide
                        </button>
                        <button
                            className="action-btn emergency"
                            onClick={() => onNavigate('emergency')}
                        >
                            <AlertTriangle size={20} />
                            Crisis Support
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );

    const ProviderOverview = () => (
        <div className="dashboard-section">
            <div className="section-header">
                <h2>Provider Dashboard</h2>
                <p>Monitor patient progress and manage care plans</p>
            </div>

            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-icon">
                        <Users size={24} />
                    </div>
                    <div className="stat-content">
                        <h3>Active Patients</h3>
                        <div className="stat-value">24</div>
                        <div className="stat-subtitle">3 new this week</div>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon">
                        <Calendar size={24} />
                    </div>
                    <div className="stat-content">
                        <h3>Sessions Today</h3>
                        <div className="stat-value">8</div>
                        <div className="stat-subtitle">2 completed</div>
                    </div>
                </div>

                <div className="stat-card alert">
                    <div className="stat-icon">
                        <AlertTriangle size={24} />
                    </div>
                    <div className="stat-content">
                        <h3>Priority Alerts</h3>
                        <div className="stat-value">2</div>
                        <div className="stat-subtitle">Requires attention</div>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon">
                        <TrendingUp size={24} />
                    </div>
                    <div className="stat-content">
                        <h3>Avg. Progress</h3>
                        <div className="stat-value">+15%</div>
                        <div className="stat-subtitle">This month</div>
                    </div>
                </div>
            </div>

            <div className="dashboard-grid">
                <div className="dashboard-card">
                    <h3>Patient Queue</h3>
                    <div className="patient-queue">
                        <div className="queue-item priority-high">
                            <div className="patient-info">
                                <span className="patient-name">Patient #1247</span>
                                <span className="patient-status">Crisis Alert</span>
                            </div>
                            <button className="btn-urgent">Review</button>
                        </div>
                        <div className="queue-item">
                            <div className="patient-info">
                                <span className="patient-name">Patient #1156</span>
                                <span className="patient-status">Session Complete</span>
                            </div>
                            <button className="btn-secondary">Notes</button>
                        </div>
                    </div>
                </div>

                <div className="dashboard-card">
                    <h3>System Status</h3>
                    <div className="system-status">
                        <div className="status-item">
                            <Shield size={16} />
                            <span>HIPAA Compliance: Active</span>
                            <div className="status-indicator green"></div>
                        </div>
                        <div className="status-item">
                            <Activity size={16} />
                            <span>AI Model: Operational</span>
                            <div className="status-indicator green"></div>
                        </div>
                        <div className="status-item">
                            <FileText size={16} />
                            <span>Data Backup: Complete</span>
                            <div className="status-indicator green"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );

    return (
        <div className="healthcare-dashboard">
            <div className="dashboard-header">
                <div className="header-content">
                    <div className="header-title">
                        <h1>Sage Healthcare AI</h1>
                        <span className="user-role">{userRole === 'provider' ? 'Healthcare Provider' : 'Patient'} Portal</span>
                    </div>
                    <div className="header-actions">
                        <button className="notification-btn">
                            <AlertTriangle size={20} />
                            {notifications.length > 0 && (
                                <span className="notification-badge">{notifications.length}</span>
                            )}
                        </button>
                        <button
                            className="help-btn"
                            onClick={() => onNavigate('user-guide')}
                            title="Open User Guide"
                        >
                            <HelpCircle size={20} />
                        </button>
                        <button className="settings-btn">
                            <Settings size={20} />
                        </button>
                        <div className="user-avatar">
                            <User size={20} />
                        </div>
                    </div>
                </div>
            </div>

            <div className="dashboard-nav">
                <button 
                    className={`nav-btn ${activeTab === 'overview' ? 'active' : ''}`}
                    onClick={() => setActiveTab('overview')}
                >
                    Overview
                </button>
                <button 
                    className={`nav-btn ${activeTab === 'sessions' ? 'active' : ''}`}
                    onClick={() => setActiveTab('sessions')}
                >
                    Sessions
                </button>
                <button 
                    className={`nav-btn ${activeTab === 'progress' ? 'active' : ''}`}
                    onClick={() => setActiveTab('progress')}
                >
                    Progress
                </button>
                {userRole === 'provider' && (
                    <button 
                        className={`nav-btn ${activeTab === 'patients' ? 'active' : ''}`}
                        onClick={() => setActiveTab('patients')}
                    >
                        Patients
                    </button>
                )}
            </div>

            <div className="dashboard-content">
                {activeTab === 'overview' && (
                    userRole === 'provider' ? <ProviderOverview /> : <PatientOverview />
                )}
                {/* Additional tab content would be implemented here */}
            </div>
        </div>
    );
};

export default HealthcareDashboard;
