import React, { useState, useMemo } from 'react';
import {
    Calendar,
    Clock,
    Target,
    CheckCircle,
    AlertTriangle,
    Heart,
    Brain,
    TrendingUp,
    TrendingDown,
    MessageCircle,
    Award,
    Flag,
    Activity,
    Filter,
    ChevronDown,
    ChevronRight
} from 'lucide-react';
import './TreatmentTimeline.css';

const TreatmentTimeline = ({ sessions, milestones, metrics }) => {
    const [filterType, setFilterType] = useState('all');
    const [timeRange, setTimeRange] = useState('all');
    const [expandedItems, setExpandedItems] = useState(new Set());

    // Combine and sort all timeline events
    const timelineEvents = useMemo(() => {
        const events = [];

        // Add sessions
        sessions.forEach(session => {
            events.push({
                id: `session-${session.id}`,
                type: 'session',
                date: new Date(session.start_time),
                title: `${session.session_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} Session`,
                data: session,
                icon: <MessageCircle size={16} />,
                category: 'session'
            });
        });

        // Add milestones
        milestones.forEach(milestone => {
            events.push({
                id: `milestone-${milestone.id}`,
                type: 'milestone',
                date: new Date(milestone.created_at),
                title: milestone.title,
                data: milestone,
                icon: milestone.milestone_type === 'goal_achieved' ? <Award size={16} /> : <Target size={16} />,
                category: 'milestone'
            });

            // Add milestone achievements if different from creation
            if (milestone.achieved_date && milestone.achieved_date !== milestone.created_at) {
                events.push({
                    id: `achievement-${milestone.id}`,
                    type: 'achievement',
                    date: new Date(milestone.achieved_date),
                    title: `Achieved: ${milestone.title}`,
                    data: milestone,
                    icon: <CheckCircle size={16} />,
                    category: 'achievement'
                });
            }
        });

        // Add significant metric changes
        Object.entries(metrics).forEach(([metricType, values]) => {
            if (values.length >= 2) {
                // Find significant improvements or declines
                for (let i = 1; i < values.length; i++) {
                    const prev = values[i - 1];
                    const curr = values[i];
                    const change = curr.value - prev.value;
                    const percentChange = Math.abs(change / prev.value) * 100;

                    // Only add events for significant changes (>20%)
                    if (percentChange > 20) {
                        events.push({
                            id: `metric-${metricType}-${i}`,
                            type: 'metric_change',
                            date: new Date(curr.date),
                            title: `${metricType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} ${change > 0 ? 'Improvement' : 'Decline'}`,
                            data: { metricType, change, percentChange, value: curr.value },
                            icon: change > 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />,
                            category: 'metric'
                        });
                    }
                }
            }
        });

        // Sort by date (newest first)
        return events.sort((a, b) => b.date - a.date);
    }, [sessions, milestones, metrics]);

    // Filter events
    const filteredEvents = useMemo(() => {
        let filtered = timelineEvents;

        // Filter by type
        if (filterType !== 'all') {
            filtered = filtered.filter(event => event.category === filterType);
        }

        // Filter by time range
        if (timeRange !== 'all') {
            const now = new Date();
            const daysBack = parseInt(timeRange);
            const cutoffDate = new Date(now.getTime() - (daysBack * 24 * 60 * 60 * 1000));
            filtered = filtered.filter(event => event.date >= cutoffDate);
        }

        return filtered;
    }, [timelineEvents, filterType, timeRange]);

    // Group events by date
    const groupedEvents = useMemo(() => {
        const groups = {};
        filteredEvents.forEach(event => {
            const dateKey = event.date.toDateString();
            if (!groups[dateKey]) {
                groups[dateKey] = [];
            }
            groups[dateKey].push(event);
        });
        return groups;
    }, [filteredEvents]);

    const formatDate = (date) => {
        const today = new Date();
        const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000);
        
        if (date.toDateString() === today.toDateString()) {
            return 'Today';
        } else if (date.toDateString() === yesterday.toDateString()) {
            return 'Yesterday';
        } else {
            return date.toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        }
    };

    const formatTime = (date) => {
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const toggleItemExpansion = (itemId) => {
        const newExpanded = new Set(expandedItems);
        if (newExpanded.has(itemId)) {
            newExpanded.delete(itemId);
        } else {
            newExpanded.add(itemId);
        }
        setExpandedItems(newExpanded);
    };

    const renderEventDetails = (event) => {
        switch (event.type) {
            case 'session':
                return (
                    <div className="event-details session-details">
                        <div className="details-grid">
                            <div className="detail-item">
                                <Clock size={14} />
                                <span>Duration: {event.data.duration_minutes ? `${event.data.duration_minutes} min` : 'N/A'}</span>
                            </div>
                            <div className="detail-item">
                                <Heart size={14} />
                                <span>Pre-mood: {event.data.pre_session_mood || 'N/A'}</span>
                            </div>
                            <div className="detail-item">
                                <Heart size={14} />
                                <span>Post-mood: {event.data.post_session_mood || 'N/A'}</span>
                            </div>
                            <div className="detail-item">
                                <Brain size={14} />
                                <span>Engagement: {event.data.engagement_score ? `${(event.data.engagement_score * 100).toFixed(0)}%` : 'N/A'}</span>
                            </div>
                        </div>
                        {event.data.goals_discussed && event.data.goals_discussed.length > 0 && (
                            <div className="goals-section">
                                <h5>Goals Discussed:</h5>
                                <ul>
                                    {event.data.goals_discussed.map((goal, index) => (
                                        <li key={index}>{goal}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                );

            case 'milestone':
                return (
                    <div className="event-details milestone-details">
                        <p>{event.data.description}</p>
                        <div className="milestone-progress">
                            <div className="progress-bar">
                                <div 
                                    className="progress-fill"
                                    style={{ width: `${event.data.progress_percentage}%` }}
                                />
                            </div>
                            <span>{event.data.progress_percentage}% complete</span>
                        </div>
                        {event.data.target_date && (
                            <div className="target-date">
                                <Calendar size={14} />
                                <span>Target: {new Date(event.data.target_date).toLocaleDateString()}</span>
                            </div>
                        )}
                    </div>
                );

            case 'achievement':
                return (
                    <div className="event-details achievement-details">
                        <p>{event.data.description}</p>
                        <div className="achievement-badge">
                            <Award size={16} />
                            <span>Goal Achieved!</span>
                        </div>
                    </div>
                );

            case 'metric_change':
                return (
                    <div className="event-details metric-details">
                        <div className="metric-change">
                            <span className="change-value">
                                {event.data.change > 0 ? '+' : ''}{event.data.change.toFixed(1)}
                            </span>
                            <span className="change-percent">
                                ({event.data.percentChange.toFixed(1)}% change)
                            </span>
                        </div>
                        <div className="current-value">
                            Current value: {event.data.value.toFixed(1)}
                        </div>
                    </div>
                );

            default:
                return null;
        }
    };

    const getEventClassName = (event) => {
        const baseClass = 'timeline-event';
        const typeClass = `event-${event.type}`;
        const categoryClass = `category-${event.category}`;
        return `${baseClass} ${typeClass} ${categoryClass}`;
    };

    return (
        <div className="treatment-timeline">
            {/* Timeline Controls */}
            <div className="timeline-controls">
                <div className="filter-section">
                    <div className="filter-group">
                        <Filter size={16} />
                        <select 
                            value={filterType} 
                            onChange={(e) => setFilterType(e.target.value)}
                        >
                            <option value="all">All Events</option>
                            <option value="session">Sessions</option>
                            <option value="milestone">Milestones</option>
                            <option value="achievement">Achievements</option>
                            <option value="metric">Metric Changes</option>
                        </select>
                    </div>

                    <div className="filter-group">
                        <Calendar size={16} />
                        <select 
                            value={timeRange} 
                            onChange={(e) => setTimeRange(e.target.value)}
                        >
                            <option value="all">All Time</option>
                            <option value="7">Last 7 days</option>
                            <option value="30">Last 30 days</option>
                            <option value="90">Last 3 months</option>
                        </select>
                    </div>
                </div>

                <div className="timeline-stats">
                    <div className="stat-item">
                        <span className="stat-label">Total Events:</span>
                        <span className="stat-value">{filteredEvents.length}</span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-label">Sessions:</span>
                        <span className="stat-value">
                            {filteredEvents.filter(e => e.category === 'session').length}
                        </span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-label">Milestones:</span>
                        <span className="stat-value">
                            {filteredEvents.filter(e => e.category === 'milestone').length}
                        </span>
                    </div>
                </div>
            </div>

            {/* Timeline Content */}
            <div className="timeline-content">
                {Object.keys(groupedEvents).length === 0 ? (
                    <div className="no-events">
                        <Activity size={48} />
                        <h3>No Events Found</h3>
                        <p>No timeline events match your current filters.</p>
                    </div>
                ) : (
                    Object.entries(groupedEvents).map(([dateKey, events]) => (
                        <div key={dateKey} className="timeline-day">
                            <div className="day-header">
                                <h3>{formatDate(new Date(dateKey))}</h3>
                                <span className="event-count">{events.length} events</span>
                            </div>

                            <div className="day-events">
                                {events.map(event => (
                                    <div key={event.id} className={getEventClassName(event)}>
                                        <div className="event-timeline-marker">
                                            <div className="timeline-line" />
                                            <div className="timeline-dot">
                                                {event.icon}
                                            </div>
                                        </div>

                                        <div className="event-content">
                                            <div 
                                                className="event-header"
                                                onClick={() => toggleItemExpansion(event.id)}
                                            >
                                                <div className="event-main">
                                                    <h4>{event.title}</h4>
                                                    <span className="event-time">
                                                        {formatTime(event.date)}
                                                    </span>
                                                </div>
                                                <button className="expand-btn">
                                                    {expandedItems.has(event.id) ? 
                                                        <ChevronDown size={16} /> : 
                                                        <ChevronRight size={16} />
                                                    }
                                                </button>
                                            </div>

                                            {expandedItems.has(event.id) && renderEventDetails(event)}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default TreatmentTimeline;
