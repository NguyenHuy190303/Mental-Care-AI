import React, { useState, useEffect } from 'react';
import {
    TrendingUp,
    TrendingDown,
    Activity,
    Calendar,
    AlertTriangle,
    Heart,
    Brain,
    Clock,
    Target,
    BarChart3,
    LineChart,
    PieChart,
    Filter,
    Download,
    RefreshCw,
    Eye,
    Shield
} from 'lucide-react';
import SessionHistoryView from './SessionHistoryView';
import ProgressMetricsChart from './ProgressMetricsChart';
import TreatmentTimeline from './TreatmentTimeline';
import ProviderOverview from './ProviderOverview';
import './PatientProgressDashboard.css';

const PatientProgressDashboard = ({ userRole, patientId, onNavigate }) => {
    const [activeTab, setActiveTab] = useState('overview');
    const [progressData, setProgressData] = useState(null);
    const [sessionHistory, setSessionHistory] = useState([]);
    const [progressMetrics, setProgressMetrics] = useState({});
    const [treatmentMilestones, setTreatmentMilestones] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [dateRange, setDateRange] = useState('30'); // days
    const [refreshing, setRefreshing] = useState(false);

    useEffect(() => {
        loadProgressData();
    }, [patientId, dateRange]);

    const loadProgressData = async () => {
        try {
            setLoading(true);
            setError(null);

            // Load progress summary
            const summaryResponse = await fetch(`/api/patient-progress/summary?days_back=${dateRange}`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            });
            
            if (!summaryResponse.ok) {
                throw new Error('Failed to load progress data');
            }
            
            const summary = await summaryResponse.json();
            setProgressData(summary);

            // Load session history
            const sessionsResponse = await fetch(`/api/patient-progress/sessions?limit=50`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            });
            
            if (sessionsResponse.ok) {
                const sessions = await sessionsResponse.json();
                setSessionHistory(sessions);
            }

            // Load progress metrics
            const metricsResponse = await fetch(`/api/patient-progress/metrics?limit=100`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            });
            
            if (metricsResponse.ok) {
                const metrics = await metricsResponse.json();
                
                // Group metrics by type
                const groupedMetrics = {};
                metrics.forEach(metric => {
                    if (!groupedMetrics[metric.metric_type]) {
                        groupedMetrics[metric.metric_type] = [];
                    }
                    groupedMetrics[metric.metric_type].push({
                        value: metric.metric_value,
                        date: metric.recorded_at,
                        context: metric.measurement_context
                    });
                });
                setProgressMetrics(groupedMetrics);
            }

            // Load treatment milestones
            const milestonesResponse = await fetch(`/api/patient-progress/milestones`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            });
            
            if (milestonesResponse.ok) {
                const milestones = await milestonesResponse.json();
                setTreatmentMilestones(milestones);
            }

            // Load alerts
            const alertsResponse = await fetch(`/api/patient-progress/alerts`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            });
            
            if (alertsResponse.ok) {
                const alertsData = await alertsResponse.json();
                setAlerts(alertsData);
            }

        } catch (err) {
            console.error('Error loading progress data:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleRefresh = async () => {
        setRefreshing(true);
        await loadProgressData();
        setRefreshing(false);
    };

    const handleExportData = () => {
        // Implement data export functionality
        const exportData = {
            summary: progressData,
            sessions: sessionHistory,
            metrics: progressMetrics,
            milestones: treatmentMilestones,
            exportDate: new Date().toISOString()
        };
        
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `patient-progress-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    const renderOverviewTab = () => (
        <div className="overview-tab">
            {/* Key Metrics Cards */}
            <div className="metrics-grid">
                <div className="metric-card">
                    <div className="metric-header">
                        <Activity size={24} />
                        <h3>Total Sessions</h3>
                    </div>
                    <div className="metric-value">{progressData?.total_sessions || 0}</div>
                    <div className="metric-subtitle">
                        Last {dateRange} days
                    </div>
                </div>

                <div className="metric-card">
                    <div className="metric-header">
                        <Heart size={24} />
                        <h3>Wellness Score</h3>
                    </div>
                    <div className="metric-value">
                        {progressData?.wellness_score ? `${progressData.wellness_score}/10` : 'N/A'}
                    </div>
                    <div className={`metric-trend ${progressData?.current_mood_trend || ''}`}>
                        {progressData?.current_mood_trend === 'improving' && <TrendingUp size={16} />}
                        {progressData?.current_mood_trend === 'declining' && <TrendingDown size={16} />}
                        {progressData?.current_mood_trend || 'No trend data'}
                    </div>
                </div>

                <div className="metric-card">
                    <div className="metric-header">
                        <Clock size={24} />
                        <h3>Avg Session Duration</h3>
                    </div>
                    <div className="metric-value">
                        {progressData?.avg_session_duration ? 
                            `${Math.round(progressData.avg_session_duration)} min` : 'N/A'}
                    </div>
                    <div className="metric-subtitle">
                        Per session average
                    </div>
                </div>

                <div className="metric-card alert-card">
                    <div className="metric-header">
                        <AlertTriangle size={24} />
                        <h3>Active Alerts</h3>
                    </div>
                    <div className="metric-value">{progressData?.active_alerts || 0}</div>
                    <div className="metric-subtitle">
                        Requiring attention
                    </div>
                </div>
            </div>

            {/* Progress Charts */}
            <div className="charts-section">
                <div className="chart-container">
                    <h3>Progress Metrics Overview</h3>
                    <ProgressMetricsChart 
                        metrics={progressMetrics}
                        dateRange={dateRange}
                    />
                </div>
            </div>

            {/* Recent Milestones */}
            <div className="milestones-section">
                <h3>Recent Treatment Milestones</h3>
                <div className="milestones-list">
                    {progressData?.recent_milestones?.slice(0, 3).map(milestone => (
                        <div key={milestone.id} className="milestone-item">
                            <div className="milestone-icon">
                                <Target size={20} />
                            </div>
                            <div className="milestone-content">
                                <h4>{milestone.title}</h4>
                                <p>{milestone.description}</p>
                                <div className="milestone-progress">
                                    <div className="progress-bar">
                                        <div 
                                            className="progress-fill"
                                            style={{ width: `${milestone.progress_percentage}%` }}
                                        />
                                    </div>
                                    <span>{milestone.progress_percentage}%</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Active Alerts */}
            {alerts.length > 0 && (
                <div className="alerts-section">
                    <h3>Active Alerts</h3>
                    <div className="alerts-list">
                        {alerts.slice(0, 3).map(alert => (
                            <div key={alert.id} className={`alert-item ${alert.alert_level}`}>
                                <AlertTriangle size={20} />
                                <div className="alert-content">
                                    <h4>{alert.title}</h4>
                                    <p>{alert.description}</p>
                                    <span className="alert-time">
                                        {new Date(alert.created_at).toLocaleDateString()}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );

    const renderTabContent = () => {
        switch (activeTab) {
            case 'overview':
                return renderOverviewTab();
            case 'sessions':
                return (
                    <SessionHistoryView 
                        sessions={sessionHistory}
                        onSessionSelect={(session) => console.log('Selected session:', session)}
                        userRole={userRole}
                    />
                );
            case 'metrics':
                return (
                    <ProgressMetricsChart 
                        metrics={progressMetrics}
                        dateRange={dateRange}
                        detailed={true}
                    />
                );
            case 'timeline':
                return (
                    <TreatmentTimeline 
                        sessions={sessionHistory}
                        milestones={treatmentMilestones}
                        metrics={progressMetrics}
                    />
                );
            case 'provider':
                return userRole === 'provider' ? (
                    <ProviderOverview 
                        progressData={progressData}
                        alerts={alerts}
                        patientId={patientId}
                    />
                ) : (
                    <div className="access-denied">
                        <Shield size={48} />
                        <h3>Provider Access Required</h3>
                        <p>This section is only available to healthcare providers.</p>
                    </div>
                );
            default:
                return renderOverviewTab();
        }
    };

    if (loading) {
        return (
            <div className="progress-dashboard loading">
                <div className="loading-spinner">
                    <RefreshCw size={32} className="spinning" />
                    <p>Loading progress data...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="progress-dashboard error">
                <div className="error-message">
                    <AlertTriangle size={32} />
                    <h3>Error Loading Progress Data</h3>
                    <p>{error}</p>
                    <button onClick={loadProgressData} className="retry-btn">
                        Try Again
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="progress-dashboard">
            {/* Dashboard Header */}
            <div className="dashboard-header">
                <div className="header-content">
                    <h1>
                        <Brain size={28} />
                        Patient Progress Dashboard
                    </h1>
                    <p>Comprehensive mental health progress tracking and analytics</p>
                </div>
                
                <div className="header-actions">
                    <div className="date-range-selector">
                        <Filter size={16} />
                        <select 
                            value={dateRange} 
                            onChange={(e) => setDateRange(e.target.value)}
                        >
                            <option value="7">Last 7 days</option>
                            <option value="30">Last 30 days</option>
                            <option value="90">Last 3 months</option>
                            <option value="365">Last year</option>
                        </select>
                    </div>
                    
                    <button 
                        onClick={handleRefresh}
                        className={`refresh-btn ${refreshing ? 'refreshing' : ''}`}
                        disabled={refreshing}
                    >
                        <RefreshCw size={16} className={refreshing ? 'spinning' : ''} />
                        Refresh
                    </button>
                    
                    <button onClick={handleExportData} className="export-btn">
                        <Download size={16} />
                        Export Data
                    </button>
                </div>
            </div>

            {/* Navigation Tabs */}
            <div className="dashboard-tabs">
                <button 
                    className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
                    onClick={() => setActiveTab('overview')}
                >
                    <BarChart3 size={16} />
                    Overview
                </button>
                <button 
                    className={`tab ${activeTab === 'sessions' ? 'active' : ''}`}
                    onClick={() => setActiveTab('sessions')}
                >
                    <Calendar size={16} />
                    Session History
                </button>
                <button 
                    className={`tab ${activeTab === 'metrics' ? 'active' : ''}`}
                    onClick={() => setActiveTab('metrics')}
                >
                    <LineChart size={16} />
                    Progress Metrics
                </button>
                <button 
                    className={`tab ${activeTab === 'timeline' ? 'active' : ''}`}
                    onClick={() => setActiveTab('timeline')}
                >
                    <Clock size={16} />
                    Treatment Timeline
                </button>
                {userRole === 'provider' && (
                    <button 
                        className={`tab ${activeTab === 'provider' ? 'active' : ''}`}
                        onClick={() => setActiveTab('provider')}
                    >
                        <Eye size={16} />
                        Provider Overview
                    </button>
                )}
            </div>

            {/* Tab Content */}
            <div className="dashboard-content">
                {renderTabContent()}
            </div>
        </div>
    );
};

export default PatientProgressDashboard;
