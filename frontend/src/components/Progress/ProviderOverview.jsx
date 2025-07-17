import React, { useState, useEffect } from 'react';
import {
    AlertTriangle,
    Eye,
    FileText,
    TrendingUp,
    TrendingDown,
    Heart,
    Brain,
    Shield,
    Clock,
    Target,
    CheckCircle,
    XCircle,
    Calendar,
    User,
    Activity,
    Bell,
    Download,
    Edit,
    Plus
} from 'lucide-react';
import './ProviderOverview.css';

const ProviderOverview = ({ progressData, alerts, patientId }) => {
    const [activeSection, setActiveSection] = useState('overview');
    const [clinicalNotes, setClinicalNotes] = useState([]);
    const [newNote, setNewNote] = useState('');
    const [showNoteForm, setShowNoteForm] = useState(false);
    const [riskAssessment, setRiskAssessment] = useState(null);
    const [treatmentPlan, setTreatmentPlan] = useState(null);

    useEffect(() => {
        loadClinicalData();
    }, [patientId]);

    const loadClinicalData = async () => {
        try {
            // Load clinical notes (placeholder - would need actual API)
            setClinicalNotes([
                {
                    id: '1',
                    date: new Date().toISOString(),
                    type: 'progress_note',
                    title: 'Weekly Progress Review',
                    content: 'Patient showing consistent improvement in mood scores...',
                    provider: 'Dr. Smith'
                }
            ]);

            // Load risk assessment
            setRiskAssessment({
                overall_risk: 'low',
                crisis_indicators: 0,
                protective_factors: ['strong support system', 'medication compliance'],
                risk_factors: ['work stress'],
                last_assessment: new Date().toISOString()
            });

            // Load treatment plan
            setTreatmentPlan({
                goals: [
                    { id: '1', goal: 'Reduce anxiety levels', target: 'Below 5/10', progress: 70 },
                    { id: '2', goal: 'Improve sleep quality', target: '7+ hours nightly', progress: 45 }
                ],
                interventions: ['CBT techniques', 'Mindfulness exercises', 'Medication management'],
                next_review: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()
            });

        } catch (error) {
            console.error('Error loading clinical data:', error);
        }
    };

    const handleAddNote = async () => {
        if (!newNote.trim()) return;

        try {
            const note = {
                id: Date.now().toString(),
                date: new Date().toISOString(),
                type: 'clinical_note',
                title: 'Clinical Note',
                content: newNote,
                provider: 'Current Provider'
            };

            setClinicalNotes([note, ...clinicalNotes]);
            setNewNote('');
            setShowNoteForm(false);

            // Here you would make an API call to save the note
            console.log('Saving clinical note:', note);

        } catch (error) {
            console.error('Error saving clinical note:', error);
        }
    };

    const getRiskLevelColor = (level) => {
        switch (level) {
            case 'low': return '#10b981';
            case 'medium': return '#f59e0b';
            case 'high': return '#ef4444';
            case 'critical': return '#dc2626';
            default: return '#6b7280';
        }
    };

    const renderOverviewSection = () => (
        <div className="provider-overview-section">
            {/* Risk Assessment Card */}
            <div className="clinical-card risk-assessment">
                <div className="card-header">
                    <Shield size={20} />
                    <h3>Risk Assessment</h3>
                    <span 
                        className="risk-badge"
                        style={{ backgroundColor: getRiskLevelColor(riskAssessment?.overall_risk) }}
                    >
                        {riskAssessment?.overall_risk?.toUpperCase() || 'UNKNOWN'}
                    </span>
                </div>
                <div className="card-content">
                    <div className="risk-indicators">
                        <div className="indicator-item">
                            <AlertTriangle size={16} />
                            <span>Crisis Indicators: {riskAssessment?.crisis_indicators || 0}</span>
                        </div>
                        <div className="indicator-item">
                            <CheckCircle size={16} />
                            <span>Protective Factors: {riskAssessment?.protective_factors?.length || 0}</span>
                        </div>
                        <div className="indicator-item">
                            <XCircle size={16} />
                            <span>Risk Factors: {riskAssessment?.risk_factors?.length || 0}</span>
                        </div>
                    </div>
                    
                    {riskAssessment?.protective_factors && (
                        <div className="factors-section">
                            <h4>Protective Factors:</h4>
                            <ul>
                                {riskAssessment.protective_factors.map((factor, index) => (
                                    <li key={index}>{factor}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                    
                    {riskAssessment?.risk_factors && (
                        <div className="factors-section">
                            <h4>Risk Factors:</h4>
                            <ul>
                                {riskAssessment.risk_factors.map((factor, index) => (
                                    <li key={index}>{factor}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            </div>

            {/* Active Alerts */}
            <div className="clinical-card alerts-summary">
                <div className="card-header">
                    <Bell size={20} />
                    <h3>Active Alerts</h3>
                    <span className="alert-count">{alerts.length}</span>
                </div>
                <div className="card-content">
                    {alerts.length === 0 ? (
                        <p className="no-alerts">No active alerts</p>
                    ) : (
                        <div className="alerts-list">
                            {alerts.slice(0, 3).map(alert => (
                                <div key={alert.id} className={`alert-item ${alert.alert_level}`}>
                                    <AlertTriangle size={16} />
                                    <div className="alert-content">
                                        <h4>{alert.title}</h4>
                                        <p>{alert.description}</p>
                                        <span className="alert-time">
                                            {new Date(alert.created_at).toLocaleDateString()}
                                        </span>
                                    </div>
                                    <button className="acknowledge-btn">
                                        Acknowledge
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Treatment Progress */}
            <div className="clinical-card treatment-progress">
                <div className="card-header">
                    <Target size={20} />
                    <h3>Treatment Progress</h3>
                </div>
                <div className="card-content">
                    <div className="progress-metrics">
                        <div className="metric-item">
                            <Heart size={16} />
                            <span>Wellness Score: {progressData?.wellness_score || 'N/A'}/10</span>
                            <div className={`trend ${progressData?.current_mood_trend || ''}`}>
                                {progressData?.current_mood_trend === 'improving' && <TrendingUp size={14} />}
                                {progressData?.current_mood_trend === 'declining' && <TrendingDown size={14} />}
                            </div>
                        </div>
                        <div className="metric-item">
                            <Activity size={16} />
                            <span>Sessions: {progressData?.total_sessions || 0}</span>
                        </div>
                        <div className="metric-item">
                            <Clock size={16} />
                            <span>Avg Duration: {progressData?.avg_session_duration ? `${Math.round(progressData.avg_session_duration)}min` : 'N/A'}</span>
                        </div>
                    </div>

                    {treatmentPlan?.goals && (
                        <div className="treatment-goals">
                            <h4>Treatment Goals:</h4>
                            {treatmentPlan.goals.map(goal => (
                                <div key={goal.id} className="goal-item">
                                    <div className="goal-header">
                                        <span className="goal-text">{goal.goal}</span>
                                        <span className="goal-progress">{goal.progress}%</span>
                                    </div>
                                    <div className="progress-bar">
                                        <div 
                                            className="progress-fill"
                                            style={{ width: `${goal.progress}%` }}
                                        />
                                    </div>
                                    <span className="goal-target">Target: {goal.target}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );

    const renderClinicalNotesSection = () => (
        <div className="clinical-notes-section">
            <div className="notes-header">
                <h3>Clinical Notes</h3>
                <button 
                    className="add-note-btn"
                    onClick={() => setShowNoteForm(true)}
                >
                    <Plus size={16} />
                    Add Note
                </button>
            </div>

            {showNoteForm && (
                <div className="note-form">
                    <textarea
                        value={newNote}
                        onChange={(e) => setNewNote(e.target.value)}
                        placeholder="Enter clinical note..."
                        rows={4}
                    />
                    <div className="form-actions">
                        <button onClick={handleAddNote} className="save-btn">
                            Save Note
                        </button>
                        <button 
                            onClick={() => {
                                setShowNoteForm(false);
                                setNewNote('');
                            }}
                            className="cancel-btn"
                        >
                            Cancel
                        </button>
                    </div>
                </div>
            )}

            <div className="notes-list">
                {clinicalNotes.map(note => (
                    <div key={note.id} className="note-item">
                        <div className="note-header">
                            <div className="note-info">
                                <FileText size={16} />
                                <span className="note-title">{note.title}</span>
                                <span className="note-type">{note.type.replace('_', ' ')}</span>
                            </div>
                            <div className="note-meta">
                                <span className="note-provider">{note.provider}</span>
                                <span className="note-date">
                                    {new Date(note.date).toLocaleDateString()}
                                </span>
                            </div>
                        </div>
                        <div className="note-content">
                            <p>{note.content}</p>
                        </div>
                        <div className="note-actions">
                            <button className="edit-note-btn">
                                <Edit size={14} />
                                Edit
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );

    const renderTreatmentPlanSection = () => (
        <div className="treatment-plan-section">
            <div className="plan-header">
                <h3>Treatment Plan</h3>
                <button className="edit-plan-btn">
                    <Edit size={16} />
                    Edit Plan
                </button>
            </div>

            {treatmentPlan && (
                <div className="plan-content">
                    <div className="plan-goals">
                        <h4>Treatment Goals</h4>
                        {treatmentPlan.goals.map(goal => (
                            <div key={goal.id} className="plan-goal">
                                <div className="goal-header">
                                    <Target size={16} />
                                    <span>{goal.goal}</span>
                                </div>
                                <div className="goal-details">
                                    <span>Target: {goal.target}</span>
                                    <span>Progress: {goal.progress}%</span>
                                </div>
                                <div className="progress-bar">
                                    <div 
                                        className="progress-fill"
                                        style={{ width: `${goal.progress}%` }}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>

                    <div className="plan-interventions">
                        <h4>Interventions</h4>
                        <ul>
                            {treatmentPlan.interventions.map((intervention, index) => (
                                <li key={index}>{intervention}</li>
                            ))}
                        </ul>
                    </div>

                    <div className="plan-schedule">
                        <h4>Next Review</h4>
                        <div className="review-date">
                            <Calendar size={16} />
                            <span>{new Date(treatmentPlan.next_review).toLocaleDateString()}</span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );

    return (
        <div className="provider-overview">
            <div className="provider-header">
                <div className="header-content">
                    <h2>
                        <Eye size={24} />
                        Provider Clinical Overview
                    </h2>
                    <p>Comprehensive clinical monitoring and oversight tools</p>
                </div>
                <div className="header-actions">
                    <button className="export-btn">
                        <Download size={16} />
                        Export Report
                    </button>
                </div>
            </div>

            <div className="provider-tabs">
                <button 
                    className={`tab ${activeSection === 'overview' ? 'active' : ''}`}
                    onClick={() => setActiveSection('overview')}
                >
                    <Activity size={16} />
                    Overview
                </button>
                <button 
                    className={`tab ${activeSection === 'notes' ? 'active' : ''}`}
                    onClick={() => setActiveSection('notes')}
                >
                    <FileText size={16} />
                    Clinical Notes
                </button>
                <button 
                    className={`tab ${activeSection === 'plan' ? 'active' : ''}`}
                    onClick={() => setActiveSection('plan')}
                >
                    <Target size={16} />
                    Treatment Plan
                </button>
            </div>

            <div className="provider-content">
                {activeSection === 'overview' && renderOverviewSection()}
                {activeSection === 'notes' && renderClinicalNotesSection()}
                {activeSection === 'plan' && renderTreatmentPlanSection()}
            </div>
        </div>
    );
};

export default ProviderOverview;
