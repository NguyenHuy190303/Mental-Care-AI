"""
Advanced Analytics Dashboard for Mental Health Agent
Real-time dashboard with comprehensive metrics visualization and reporting.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse

from .metrics_collector import AdvancedMetricsCollector, TimeRange, metrics_collector
from ..auth.dependencies import require_admin
from ..models.core import User
from ..monitoring.logging_config import get_logger

logger = get_logger("analytics.dashboard")

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard", response_class=HTMLResponse, summary="Analytics Dashboard")
async def get_analytics_dashboard(
    current_user: User = Depends(require_admin)
) -> str:
    """
    Serve the analytics dashboard HTML interface.
    
    Args:
        current_user: Current authenticated admin user
        
    Returns:
        HTML dashboard interface
    """
    dashboard_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mental Health Agent - Analytics Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            .metric-card { transition: transform 0.2s; }
            .metric-card:hover { transform: translateY(-2px); }
            .chart-container { position: relative; height: 300px; }
        </style>
    </head>
    <body class="bg-gray-100 min-h-screen">
        <div class="container mx-auto px-4 py-8">
            <!-- Header -->
            <div class="mb-8">
                <h1 class="text-3xl font-bold text-gray-800 mb-2">Mental Health Agent Analytics</h1>
                <p class="text-gray-600">Comprehensive system metrics and insights</p>
                <div class="mt-4 flex space-x-4">
                    <select id="timeRange" class="px-4 py-2 border rounded-lg">
                        <option value="day">Last 24 Hours</option>
                        <option value="week">Last Week</option>
                        <option value="month">Last Month</option>
                        <option value="quarter">Last Quarter</option>
                    </select>
                    <button onclick="refreshDashboard()" class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600">
                        Refresh Data
                    </button>
                </div>
            </div>

            <!-- Key Metrics Cards -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div class="metric-card bg-white p-6 rounded-lg shadow-md">
                    <h3 class="text-sm font-medium text-gray-500 mb-2">Active Users</h3>
                    <p id="activeUsers" class="text-3xl font-bold text-blue-600">-</p>
                    <p class="text-sm text-gray-500 mt-1">Unique users in period</p>
                </div>
                <div class="metric-card bg-white p-6 rounded-lg shadow-md">
                    <h3 class="text-sm font-medium text-gray-500 mb-2">Crisis Interventions</h3>
                    <p id="crisisInterventions" class="text-3xl font-bold text-red-600">-</p>
                    <p class="text-sm text-gray-500 mt-1">Emergency responses</p>
                </div>
                <div class="metric-card bg-white p-6 rounded-lg shadow-md">
                    <h3 class="text-sm font-medium text-gray-500 mb-2">Avg User Rating</h3>
                    <p id="avgRating" class="text-3xl font-bold text-green-600">-</p>
                    <p class="text-sm text-gray-500 mt-1">Out of 5 stars</p>
                </div>
                <div class="metric-card bg-white p-6 rounded-lg shadow-md">
                    <h3 class="text-sm font-medium text-gray-500 mb-2">Response Time</h3>
                    <p id="avgResponseTime" class="text-3xl font-bold text-purple-600">-</p>
                    <p class="text-sm text-gray-500 mt-1">Average seconds</p>
                </div>
            </div>

            <!-- Charts Section -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                <!-- User Engagement Chart -->
                <div class="bg-white p-6 rounded-lg shadow-md">
                    <h3 class="text-lg font-semibold mb-4">User Engagement Trends</h3>
                    <div class="chart-container">
                        <canvas id="engagementChart"></canvas>
                    </div>
                </div>

                <!-- Safety Metrics Chart -->
                <div class="bg-white p-6 rounded-lg shadow-md">
                    <h3 class="text-lg font-semibold mb-4">Safety Metrics</h3>
                    <div class="chart-container">
                        <canvas id="safetyChart"></canvas>
                    </div>
                </div>

                <!-- Quality Distribution Chart -->
                <div class="bg-white p-6 rounded-lg shadow-md">
                    <h3 class="text-lg font-semibold mb-4">Conversation Quality</h3>
                    <div class="chart-container">
                        <canvas id="qualityChart"></canvas>
                    </div>
                </div>

                <!-- RLHF Performance Chart -->
                <div class="bg-white p-6 rounded-lg shadow-md">
                    <h3 class="text-lg font-semibold mb-4">RLHF Performance</h3>
                    <div class="chart-container">
                        <canvas id="rlhfChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- Insights and Recommendations -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="bg-white p-6 rounded-lg shadow-md">
                    <h3 class="text-lg font-semibold mb-4">Key Insights</h3>
                    <ul id="insights" class="space-y-2">
                        <li class="text-gray-600">Loading insights...</li>
                    </ul>
                </div>
                <div class="bg-white p-6 rounded-lg shadow-md">
                    <h3 class="text-lg font-semibold mb-4">Recommendations</h3>
                    <ul id="recommendations" class="space-y-2">
                        <li class="text-gray-600">Loading recommendations...</li>
                    </ul>
                </div>
            </div>
        </div>

        <script>
            let charts = {};

            async function fetchAnalyticsData(timeRange = 'day') {
                try {
                    const response = await fetch(`/api/analytics/comprehensive-report?time_range=${timeRange}`, {
                        headers: {
                            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                        }
                    });
                    
                    if (!response.ok) {
                        throw new Error('Failed to fetch analytics data');
                    }
                    
                    return await response.json();
                } catch (error) {
                    console.error('Error fetching analytics:', error);
                    return null;
                }
            }

            function updateMetricCards(data) {
                const userEngagement = data.metrics?.user_engagement || {};
                const safetyIncidents = data.metrics?.safety_incidents || {};
                const conversationQuality = data.metrics?.conversation_quality || {};

                document.getElementById('activeUsers').textContent = userEngagement.active_users || 0;
                document.getElementById('crisisInterventions').textContent = safetyIncidents.crisis_interventions || 0;
                document.getElementById('avgRating').textContent = (conversationQuality.average_user_rating || 0).toFixed(1);
                document.getElementById('avgResponseTime').textContent = (safetyIncidents.avg_crisis_response_time_seconds || 0).toFixed(1);
            }

            function createEngagementChart(data) {
                const ctx = document.getElementById('engagementChart').getContext('2d');
                const userEngagement = data.metrics?.user_engagement || {};
                
                if (charts.engagement) charts.engagement.destroy();
                
                charts.engagement = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: Object.keys(userEngagement.hourly_usage_distribution || {}),
                        datasets: [{
                            label: 'Hourly Usage',
                            data: Object.values(userEngagement.hourly_usage_distribution || {}),
                            borderColor: 'rgb(59, 130, 246)',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: { beginAtZero: true }
                        }
                    }
                });
            }

            function createSafetyChart(data) {
                const ctx = document.getElementById('safetyChart').getContext('2d');
                const safetyIncidents = data.metrics?.safety_incidents || {};
                
                if (charts.safety) charts.safety.destroy();
                
                charts.safety = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: ['Crisis Interventions', 'Safety Warnings', 'Emergency Resources'],
                        datasets: [{
                            data: [
                                safetyIncidents.crisis_interventions || 0,
                                safetyIncidents.safety_warnings_issued || 0,
                                safetyIncidents.emergency_resources_provided || 0
                            ],
                            backgroundColor: ['#ef4444', '#f59e0b', '#10b981']
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });
            }

            function createQualityChart(data) {
                const ctx = document.getElementById('qualityChart').getContext('2d');
                const conversationQuality = data.metrics?.conversation_quality || {};
                
                if (charts.quality) charts.quality.destroy();
                
                charts.quality = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: Object.keys(conversationQuality.rating_distribution || {}),
                        datasets: [{
                            label: 'Rating Distribution',
                            data: Object.values(conversationQuality.rating_distribution || {}),
                            backgroundColor: 'rgba(34, 197, 94, 0.8)'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: { beginAtZero: true }
                        }
                    }
                });
            }

            function createRLHFChart(data) {
                const ctx = document.getElementById('rlhfChart').getContext('2d');
                const rlhfPerformance = data.metrics?.rlhf_performance || {};
                
                if (charts.rlhf) charts.rlhf.destroy();
                
                charts.rlhf = new Chart(ctx, {
                    type: 'pie',
                    data: {
                        labels: Object.keys(rlhfPerformance.quality_distribution || {}),
                        datasets: [{
                            data: Object.values(rlhfPerformance.quality_distribution || {}),
                            backgroundColor: ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6']
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });
            }

            function updateInsightsAndRecommendations(data) {
                const insights = data.insights || [];
                const recommendations = data.recommendations || [];

                const insightsElement = document.getElementById('insights');
                insightsElement.innerHTML = insights.map(insight => 
                    `<li class="flex items-start"><span class="text-blue-500 mr-2">•</span><span class="text-gray-700">${insight}</span></li>`
                ).join('');

                const recommendationsElement = document.getElementById('recommendations');
                recommendationsElement.innerHTML = recommendations.slice(0, 5).map(rec => 
                    `<li class="flex items-start"><span class="text-green-500 mr-2">•</span><span class="text-gray-700">${rec}</span></li>`
                ).join('');
            }

            async function refreshDashboard() {
                const timeRange = document.getElementById('timeRange').value;
                const data = await fetchAnalyticsData(timeRange);
                
                if (data) {
                    updateMetricCards(data);
                    createEngagementChart(data);
                    createSafetyChart(data);
                    createQualityChart(data);
                    createRLHFChart(data);
                    updateInsightsAndRecommendations(data);
                }
            }

            // Initialize dashboard
            document.addEventListener('DOMContentLoaded', function() {
                refreshDashboard();
                
                // Auto-refresh every 5 minutes
                setInterval(refreshDashboard, 5 * 60 * 1000);
                
                // Time range change handler
                document.getElementById('timeRange').addEventListener('change', refreshDashboard);
            });
        </script>
    </body>
    </html>
    """
    
    return dashboard_html


@router.get("/comprehensive-report", summary="Get Comprehensive Analytics Report")
async def get_comprehensive_analytics_report(
    time_range: TimeRange = Query(TimeRange.DAY, description="Time range for analytics"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get comprehensive analytics report.
    
    Args:
        time_range: Time range for analytics
        current_user: Current authenticated admin user
        
    Returns:
        Comprehensive analytics report
    """
    try:
        logger.info(f"Comprehensive analytics report requested for {time_range.value}", user_id=current_user.id)
        
        report = await metrics_collector.generate_comprehensive_analytics_report(time_range)
        
        return {
            "report_id": report.report_id,
            "time_range": report.time_range.value,
            "start_date": report.start_date.isoformat(),
            "end_date": report.end_date.isoformat(),
            "metrics": report.metrics,
            "insights": report.insights,
            "recommendations": report.recommendations,
            "generated_at": report.generated_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate comprehensive analytics report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate analytics report")


@router.get("/user-engagement", summary="Get User Engagement Metrics")
async def get_user_engagement_metrics(
    time_range: TimeRange = Query(TimeRange.DAY, description="Time range for metrics"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get user engagement metrics.
    
    Args:
        time_range: Time range for metrics
        current_user: Current authenticated admin user
        
    Returns:
        User engagement metrics
    """
    try:
        metrics = await metrics_collector.collect_user_engagement_metrics(time_range)
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get user engagement metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user engagement metrics")


@router.get("/safety-incidents", summary="Get Safety Incident Metrics")
async def get_safety_incident_metrics(
    time_range: TimeRange = Query(TimeRange.DAY, description="Time range for metrics"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get safety incident metrics.
    
    Args:
        time_range: Time range for metrics
        current_user: Current authenticated admin user
        
    Returns:
        Safety incident metrics
    """
    try:
        metrics = await metrics_collector.collect_safety_incident_metrics(time_range)
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get safety incident metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve safety incident metrics")


@router.get("/conversation-quality", summary="Get Conversation Quality Metrics")
async def get_conversation_quality_metrics(
    time_range: TimeRange = Query(TimeRange.DAY, description="Time range for metrics"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get conversation quality metrics.
    
    Args:
        time_range: Time range for metrics
        current_user: Current authenticated admin user
        
    Returns:
        Conversation quality metrics
    """
    try:
        metrics = await metrics_collector.collect_conversation_quality_metrics(time_range)
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get conversation quality metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation quality metrics")


@router.get("/rlhf-performance", summary="Get RLHF Performance Metrics")
async def get_rlhf_performance_metrics(
    time_range: TimeRange = Query(TimeRange.WEEK, description="Time range for metrics"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get RLHF performance metrics.
    
    Args:
        time_range: Time range for metrics
        current_user: Current authenticated admin user
        
    Returns:
        RLHF performance metrics
    """
    try:
        metrics = await metrics_collector.collect_rlhf_performance_metrics(time_range)
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get RLHF performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve RLHF performance metrics")


@router.post("/export-report", summary="Export Analytics Report")
async def export_analytics_report(
    time_range: TimeRange = Query(TimeRange.MONTH, description="Time range for report"),
    format: str = Query("json", regex="^(json|csv|pdf)$", description="Export format"),
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Export comprehensive analytics report.
    
    Args:
        time_range: Time range for report
        format: Export format (json, csv, pdf)
        background_tasks: Background task handler
        current_user: Current authenticated admin user
        
    Returns:
        Export status
    """
    try:
        logger.info(f"Analytics report export requested", user_id=current_user.id, format=format, time_range=time_range.value)
        
        # Generate report in background
        background_tasks.add_task(
            _export_analytics_report_background,
            time_range,
            format,
            current_user.id
        )
        
        return {
            "message": "Analytics report export started",
            "time_range": time_range.value,
            "format": format,
            "estimated_completion": "2-5 minutes",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start analytics report export: {e}")
        raise HTTPException(status_code=500, detail="Failed to start report export")


async def _export_analytics_report_background(
    time_range: TimeRange,
    format: str,
    user_id: str
):
    """Background task to export analytics report."""
    try:
        logger.info(f"Starting background analytics report export for user {user_id}")
        
        # Generate comprehensive report
        report = await metrics_collector.generate_comprehensive_analytics_report(time_range)
        
        # Export based on format
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        if format == "json":
            filename = f"./reports/analytics_report_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(asdict(report), f, indent=2, default=str)
        
        elif format == "csv":
            filename = f"./reports/analytics_report_{timestamp}.csv"
            # Convert to CSV format
            import pandas as pd
            
            # Flatten metrics for CSV
            flattened_data = []
            for metric_type, metrics in report.metrics.items():
                if isinstance(metrics, dict):
                    for key, value in metrics.items():
                        if isinstance(value, (int, float, str)):
                            flattened_data.append({
                                'metric_type': metric_type,
                                'metric_name': key,
                                'value': value,
                                'timestamp': report.generated_at.isoformat()
                            })
            
            df = pd.DataFrame(flattened_data)
            df.to_csv(filename, index=False)
        
        elif format == "pdf":
            filename = f"./reports/analytics_report_{timestamp}.pdf"
            # For PDF generation, you would use a library like reportlab
            # For now, create a simple text file
            with open(filename.replace('.pdf', '.txt'), 'w', encoding='utf-8') as f:
                f.write(f"Mental Health Agent Analytics Report\n")
                f.write(f"Generated: {report.generated_at}\n")
                f.write(f"Time Range: {report.time_range.value}\n\n")
                
                f.write("INSIGHTS:\n")
                for insight in report.insights:
                    f.write(f"- {insight}\n")
                
                f.write("\nRECOMMENDATIONS:\n")
                for rec in report.recommendations:
                    f.write(f"- {rec}\n")
        
        logger.info(f"Analytics report export completed for user {user_id}: {filename}")
        
    except Exception as e:
        logger.error(f"Analytics report export failed for user {user_id}: {e}")


# Include analytics router in main application
analytics_router = router
