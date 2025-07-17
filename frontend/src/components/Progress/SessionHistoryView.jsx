import React, { useState, useMemo } from 'react';
import {
    Calendar,
    Clock,
    MessageCircle,
    TrendingUp,
    TrendingDown,
    Heart,
    Brain,
    AlertTriangle,
    CheckCircle,
    Filter,
    Search,
    ChevronDown,
    ChevronRight,
    Eye,
    FileText
} from 'lucide-react';
import './SessionHistoryView.css';

const SessionHistoryView = ({ sessions, onSessionSelect, userRole }) => {
    const [searchTerm, setSearchTerm] = useState('');
    const [filterType, setFilterType] = useState('all');
    const [sortBy, setSortBy] = useState('date_desc');
    const [expandedSession, setExpandedSession] = useState(null);
    const [selectedSessions, setSelectedSessions] = useState(new Set());

    // Filter and sort sessions
    const filteredSessions = useMemo(() => {
        let filtered = sessions.filter(session => {
            // Search filter
            if (searchTerm) {
                const searchLower = searchTerm.toLowerCase();
                return (
                    session.session_type.toLowerCase().includes(searchLower) ||
                    (session.goals_discussed && 
                     session.goals_discussed.some(goal => 
                         goal.toLowerCase().includes(searchLower)
                     ))
                );
            }
            return true;
        });

        // Type filter
        if (filterType !== 'all') {
            filtered = filtered.filter(session => session.session_type === filterType);
        }

        // Sort
        filtered.sort((a, b) => {
            switch (sortBy) {
                case 'date_desc':
                    return new Date(b.start_time) - new Date(a.start_time);
                case 'date_asc':
                    return new Date(a.start_time) - new Date(b.start_time);
                case 'duration_desc':
                    return (b.duration_minutes || 0) - (a.duration_minutes || 0);
                case 'mood_improvement':
                    return (b.mood_improvement || 0) - (a.mood_improvement || 0);
                default:
                    return 0;
            }
        });

        return filtered;
    }, [sessions, searchTerm, filterType, sortBy]);

    const sessionTypes = useMemo(() => {
        const types = new Set(sessions.map(s => s.session_type));
        return Array.from(types);
    }, [sessions]);

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const formatDuration = (minutes) => {
        if (!minutes) return 'N/A';
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
    };

    const getMoodIcon = (mood) => {
        switch (mood) {
            case 'very_good':
                return <Heart size={16} className="mood-very-good" />;
            case 'good':
                return <Heart size={16} className="mood-good" />;
            case 'neutral':
                return <Heart size={16} className="mood-neutral" />;
            case 'low':
                return <Heart size={16} className="mood-low" />;
            case 'very_low':
                return <Heart size={16} className="mood-very-low" />;
            default:
                return <Heart size={16} className="mood-unknown" />;
        }
    };

    const getMoodImprovementIcon = (improvement) => {
        if (improvement > 0) return <TrendingUp size={16} className="improvement-positive" />;
        if (improvement < 0) return <TrendingDown size={16} className="improvement-negative" />;
        return <div className="improvement-neutral">—</div>;
    };

    const getCrisisRiskBadge = (riskLevel) => {
        const levels = {
            1: { label: 'Low', className: 'risk-low' },
            2: { label: 'Low-Med', className: 'risk-low-med' },
            3: { label: 'Medium', className: 'risk-medium' },
            4: { label: 'High', className: 'risk-high' },
            5: { label: 'Critical', className: 'risk-critical' }
        };
        
        const risk = levels[riskLevel] || levels[1];
        return <span className={`risk-badge ${risk.className}`}>{risk.label}</span>;
    };

    const toggleSessionExpansion = (sessionId) => {
        setExpandedSession(expandedSession === sessionId ? null : sessionId);
    };

    const handleSessionSelection = (sessionId) => {
        const newSelected = new Set(selectedSessions);
        if (newSelected.has(sessionId)) {
            newSelected.delete(sessionId);
        } else {
            newSelected.add(sessionId);
        }
        setSelectedSessions(newSelected);
    };

    const renderSessionDetails = (session) => (
        <div className="session-details">
            <div className="details-grid">
                <div className="detail-section">
                    <h4>Session Metrics</h4>
                    <div className="metrics-list">
                        <div className="metric-item">
                            <MessageCircle size={16} />
                            <span>Messages: {session.message_count || 0}</span>
                        </div>
                        <div className="metric-item">
                            <Brain size={16} />
                            <span>Engagement: {session.engagement_score ? `${(session.engagement_score * 100).toFixed(0)}%` : 'N/A'}</span>
                        </div>
                        <div className="metric-item">
                            <AlertTriangle size={16} />
                            <span>Anxiety Level: {session.anxiety_level || 'N/A'}/10</span>
                        </div>
                        <div className="metric-item">
                            <Heart size={16} />
                            <span>Depression Score: {session.depression_indicators || 'N/A'}/10</span>
                        </div>
                    </div>
                </div>

                {session.goals_discussed && session.goals_discussed.length > 0 && (
                    <div className="detail-section">
                        <h4>Goals Discussed</h4>
                        <ul className="goals-list">
                            {session.goals_discussed.map((goal, index) => (
                                <li key={index}>{goal}</li>
                            ))}
                        </ul>
                    </div>
                )}

                {session.coping_strategies_used && session.coping_strategies_used.length > 0 && (
                    <div className="detail-section">
                        <h4>Coping Strategies Used</h4>
                        <ul className="strategies-list">
                            {session.coping_strategies_used.map((strategy, index) => (
                                <li key={index}>{strategy}</li>
                            ))}
                        </ul>
                    </div>
                )}

                {userRole === 'provider' && session.encrypted_clinical_notes && (
                    <div className="detail-section">
                        <h4>Clinical Notes</h4>
                        <div className="clinical-notes">
                            <FileText size={16} />
                            <span>Encrypted clinical notes available</span>
                            <button className="view-notes-btn">
                                <Eye size={14} />
                                View Notes
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );

    return (
        <div className="session-history-view">
            {/* Filters and Search */}
            <div className="history-controls">
                <div className="search-section">
                    <div className="search-box">
                        <Search size={16} />
                        <input
                            type="text"
                            placeholder="Search sessions..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                </div>

                <div className="filter-section">
                    <div className="filter-group">
                        <Filter size={16} />
                        <select 
                            value={filterType} 
                            onChange={(e) => setFilterType(e.target.value)}
                        >
                            <option value="all">All Types</option>
                            {sessionTypes.map(type => (
                                <option key={type} value={type}>
                                    {type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="sort-group">
                        <select 
                            value={sortBy} 
                            onChange={(e) => setSortBy(e.target.value)}
                        >
                            <option value="date_desc">Newest First</option>
                            <option value="date_asc">Oldest First</option>
                            <option value="duration_desc">Longest Duration</option>
                            <option value="mood_improvement">Best Mood Improvement</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* Session Statistics */}
            <div className="session-stats">
                <div className="stat-item">
                    <span className="stat-label">Total Sessions:</span>
                    <span className="stat-value">{filteredSessions.length}</span>
                </div>
                <div className="stat-item">
                    <span className="stat-label">Avg Duration:</span>
                    <span className="stat-value">
                        {filteredSessions.length > 0 
                            ? formatDuration(
                                filteredSessions.reduce((sum, s) => sum + (s.duration_minutes || 0), 0) / 
                                filteredSessions.length
                              )
                            : 'N/A'
                        }
                    </span>
                </div>
                <div className="stat-item">
                    <span className="stat-label">Completed:</span>
                    <span className="stat-value">
                        {filteredSessions.filter(s => s.end_time).length}/{filteredSessions.length}
                    </span>
                </div>
            </div>

            {/* Sessions List */}
            <div className="sessions-list">
                {filteredSessions.length === 0 ? (
                    <div className="no-sessions">
                        <Calendar size={48} />
                        <h3>No Sessions Found</h3>
                        <p>No sessions match your current filters.</p>
                    </div>
                ) : (
                    filteredSessions.map(session => (
                        <div 
                            key={session.id} 
                            className={`session-item ${expandedSession === session.id ? 'expanded' : ''}`}
                        >
                            <div className="session-header" onClick={() => toggleSessionExpansion(session.id)}>
                                <div className="session-main-info">
                                    <div className="session-title">
                                        <Calendar size={16} />
                                        <span className="session-type">
                                            {session.session_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                        </span>
                                        <span className="session-date">
                                            {formatDate(session.start_time)}
                                        </span>
                                    </div>
                                    
                                    <div className="session-metrics">
                                        <div className="metric">
                                            <Clock size={14} />
                                            <span>{formatDuration(session.duration_minutes)}</span>
                                        </div>
                                        
                                        {session.pre_session_mood && (
                                            <div className="metric mood-metric">
                                                {getMoodIcon(session.pre_session_mood)}
                                                <span>Pre: {session.pre_session_mood.replace('_', ' ')}</span>
                                            </div>
                                        )}
                                        
                                        {session.post_session_mood && (
                                            <div className="metric mood-metric">
                                                {getMoodIcon(session.post_session_mood)}
                                                <span>Post: {session.post_session_mood.replace('_', ' ')}</span>
                                            </div>
                                        )}
                                        
                                        {session.mood_improvement !== null && session.mood_improvement !== undefined && (
                                            <div className="metric improvement-metric">
                                                {getMoodImprovementIcon(session.mood_improvement)}
                                                <span>{session.mood_improvement > 0 ? '+' : ''}{session.mood_improvement}</span>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <div className="session-status">
                                    {getCrisisRiskBadge(session.crisis_risk_level)}
                                    
                                    {session.end_time ? (
                                        <CheckCircle size={16} className="status-completed" />
                                    ) : (
                                        <Clock size={16} className="status-ongoing" />
                                    )}
                                    
                                    <button className="expand-btn">
                                        {expandedSession === session.id ? 
                                            <ChevronDown size={16} /> : 
                                            <ChevronRight size={16} />
                                        }
                                    </button>
                                </div>
                            </div>

                            {expandedSession === session.id && renderSessionDetails(session)}
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default SessionHistoryView;
