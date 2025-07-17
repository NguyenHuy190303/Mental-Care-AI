import React, { useState, useMemo } from 'react';
import {
    LineChart,
    Line,
    AreaChart,
    Area,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell
} from 'recharts';
import {
    TrendingUp,
    TrendingDown,
    BarChart3,
    PieChart as PieChartIcon,
    Activity,
    Heart,
    Brain,
    Target,
    Calendar,
    Filter
} from 'lucide-react';
import './ProgressMetricsChart.css';

const ProgressMetricsChart = ({ metrics, dateRange, detailed = false }) => {
    const [selectedMetrics, setSelectedMetrics] = useState(['mood_score', 'anxiety_level']);
    const [chartType, setChartType] = useState('line');
    const [timeGrouping, setTimeGrouping] = useState('daily');

    // Color scheme for different metrics
    const metricColors = {
        mood_score: '#10b981',
        anxiety_level: '#f59e0b',
        depression_score: '#ef4444',
        engagement_score: '#3b82f6',
        wellness_index: '#8b5cf6',
        coping_skills: '#06b6d4'
    };

    // Metric display names and icons
    const metricInfo = {
        mood_score: { name: 'Mood Score', icon: <Heart size={16} />, unit: '/10' },
        anxiety_level: { name: 'Anxiety Level', icon: <Brain size={16} />, unit: '/10' },
        depression_score: { name: 'Depression Score', icon: <Activity size={16} />, unit: '/10' },
        engagement_score: { name: 'Engagement Score', icon: <Target size={16} />, unit: '%' },
        wellness_index: { name: 'Wellness Index', icon: <TrendingUp size={16} />, unit: '/10' },
        coping_skills: { name: 'Coping Skills', icon: <Brain size={16} />, unit: '/10' }
    };

    // Process and group data by time period
    const processedData = useMemo(() => {
        if (!metrics || Object.keys(metrics).length === 0) return [];

        // Combine all metrics with timestamps
        const allDataPoints = [];
        Object.entries(metrics).forEach(([metricType, values]) => {
            values.forEach(point => {
                allDataPoints.push({
                    date: new Date(point.date),
                    metricType,
                    value: point.value,
                    context: point.context
                });
            });
        });

        // Sort by date
        allDataPoints.sort((a, b) => a.date - b.date);

        // Group by time period
        const groupedData = {};
        allDataPoints.forEach(point => {
            let groupKey;
            const date = point.date;
            
            switch (timeGrouping) {
                case 'daily':
                    groupKey = date.toISOString().split('T')[0];
                    break;
                case 'weekly':
                    const weekStart = new Date(date);
                    weekStart.setDate(date.getDate() - date.getDay());
                    groupKey = weekStart.toISOString().split('T')[0];
                    break;
                case 'monthly':
                    groupKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
                    break;
                default:
                    groupKey = date.toISOString().split('T')[0];
            }

            if (!groupedData[groupKey]) {
                groupedData[groupKey] = { date: groupKey };
            }

            // Average values for the same metric type in the same time period
            if (!groupedData[groupKey][point.metricType]) {
                groupedData[groupKey][point.metricType] = [];
            }
            groupedData[groupKey][point.metricType].push(point.value);
        });

        // Calculate averages and format for chart
        return Object.values(groupedData).map(group => {
            const result = { date: group.date };
            Object.entries(group).forEach(([key, values]) => {
                if (key !== 'date' && Array.isArray(values)) {
                    result[key] = values.reduce((sum, val) => sum + val, 0) / values.length;
                }
            });
            return result;
        }).sort((a, b) => new Date(a.date) - new Date(b.date));
    }, [metrics, timeGrouping]);

    // Calculate trend for each metric
    const metricTrends = useMemo(() => {
        const trends = {};
        Object.keys(metrics || {}).forEach(metricType => {
            const values = processedData.map(d => d[metricType]).filter(v => v !== undefined);
            if (values.length >= 2) {
                const firstHalf = values.slice(0, Math.floor(values.length / 2));
                const secondHalf = values.slice(Math.floor(values.length / 2));
                const firstAvg = firstHalf.reduce((sum, val) => sum + val, 0) / firstHalf.length;
                const secondAvg = secondHalf.reduce((sum, val) => sum + val, 0) / secondHalf.length;
                const change = ((secondAvg - firstAvg) / firstAvg) * 100;
                
                trends[metricType] = {
                    direction: change > 5 ? 'up' : change < -5 ? 'down' : 'stable',
                    percentage: Math.abs(change).toFixed(1)
                };
            }
        });
        return trends;
    }, [processedData, metrics]);

    // Format date for display
    const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        switch (timeGrouping) {
            case 'daily':
                return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            case 'weekly':
                return `Week of ${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
            case 'monthly':
                return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
            default:
                return date.toLocaleDateString();
        }
    };

    // Custom tooltip for charts
    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            return (
                <div className="chart-tooltip">
                    <p className="tooltip-label">{formatDate(label)}</p>
                    {payload.map((entry, index) => (
                        <p key={index} style={{ color: entry.color }}>
                            {metricInfo[entry.dataKey]?.name || entry.dataKey}: {entry.value.toFixed(1)}
                            {metricInfo[entry.dataKey]?.unit || ''}
                        </p>
                    ))}
                </div>
            );
        }
        return null;
    };

    // Render metric selection controls
    const renderMetricControls = () => (
        <div className="metric-controls">
            <div className="metric-selection">
                <h4>Select Metrics to Display:</h4>
                <div className="metric-checkboxes">
                    {Object.keys(metrics || {}).map(metricType => (
                        <label key={metricType} className="metric-checkbox">
                            <input
                                type="checkbox"
                                checked={selectedMetrics.includes(metricType)}
                                onChange={(e) => {
                                    if (e.target.checked) {
                                        setSelectedMetrics([...selectedMetrics, metricType]);
                                    } else {
                                        setSelectedMetrics(selectedMetrics.filter(m => m !== metricType));
                                    }
                                }}
                            />
                            <span className="checkbox-content">
                                {metricInfo[metricType]?.icon}
                                {metricInfo[metricType]?.name || metricType}
                            </span>
                        </label>
                    ))}
                </div>
            </div>

            <div className="chart-controls">
                <div className="control-group">
                    <label>Chart Type:</label>
                    <select value={chartType} onChange={(e) => setChartType(e.target.value)}>
                        <option value="line">Line Chart</option>
                        <option value="area">Area Chart</option>
                        <option value="bar">Bar Chart</option>
                    </select>
                </div>

                <div className="control-group">
                    <label>Time Grouping:</label>
                    <select value={timeGrouping} onChange={(e) => setTimeGrouping(e.target.value)}>
                        <option value="daily">Daily</option>
                        <option value="weekly">Weekly</option>
                        <option value="monthly">Monthly</option>
                    </select>
                </div>
            </div>
        </div>
    );

    // Render trend indicators
    const renderTrendIndicators = () => (
        <div className="trend-indicators">
            <h4>Trend Analysis</h4>
            <div className="trends-grid">
                {Object.entries(metricTrends).map(([metricType, trend]) => (
                    <div key={metricType} className="trend-item">
                        <div className="trend-header">
                            {metricInfo[metricType]?.icon}
                            <span>{metricInfo[metricType]?.name || metricType}</span>
                        </div>
                        <div className={`trend-indicator ${trend.direction}`}>
                            {trend.direction === 'up' && <TrendingUp size={16} />}
                            {trend.direction === 'down' && <TrendingDown size={16} />}
                            {trend.direction === 'stable' && <div className="stable-indicator">—</div>}
                            <span>{trend.percentage}%</span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );

    // Render main chart
    const renderChart = () => {
        if (!processedData || processedData.length === 0) {
            return (
                <div className="no-data">
                    <BarChart3 size={48} />
                    <h3>No Data Available</h3>
                    <p>No progress metrics data found for the selected time period.</p>
                </div>
            );
        }

        const chartProps = {
            width: '100%',
            height: 400,
            data: processedData,
            margin: { top: 5, right: 30, left: 20, bottom: 5 }
        };

        switch (chartType) {
            case 'area':
                return (
                    <ResponsiveContainer {...chartProps}>
                        <AreaChart data={processedData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="date" tickFormatter={formatDate} />
                            <YAxis />
                            <Tooltip content={<CustomTooltip />} />
                            <Legend />
                            {selectedMetrics.map(metric => (
                                <Area
                                    key={metric}
                                    type="monotone"
                                    dataKey={metric}
                                    stackId="1"
                                    stroke={metricColors[metric]}
                                    fill={metricColors[metric]}
                                    fillOpacity={0.3}
                                    name={metricInfo[metric]?.name || metric}
                                />
                            ))}
                        </AreaChart>
                    </ResponsiveContainer>
                );

            case 'bar':
                return (
                    <ResponsiveContainer {...chartProps}>
                        <BarChart data={processedData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="date" tickFormatter={formatDate} />
                            <YAxis />
                            <Tooltip content={<CustomTooltip />} />
                            <Legend />
                            {selectedMetrics.map(metric => (
                                <Bar
                                    key={metric}
                                    dataKey={metric}
                                    fill={metricColors[metric]}
                                    name={metricInfo[metric]?.name || metric}
                                />
                            ))}
                        </BarChart>
                    </ResponsiveContainer>
                );

            default: // line chart
                return (
                    <ResponsiveContainer {...chartProps}>
                        <LineChart data={processedData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="date" tickFormatter={formatDate} />
                            <YAxis />
                            <Tooltip content={<CustomTooltip />} />
                            <Legend />
                            {selectedMetrics.map(metric => (
                                <Line
                                    key={metric}
                                    type="monotone"
                                    dataKey={metric}
                                    stroke={metricColors[metric]}
                                    strokeWidth={2}
                                    dot={{ fill: metricColors[metric], strokeWidth: 2, r: 4 }}
                                    name={metricInfo[metric]?.name || metric}
                                />
                            ))}
                        </LineChart>
                    </ResponsiveContainer>
                );
        }
    };

    return (
        <div className="progress-metrics-chart">
            {detailed && renderMetricControls()}
            
            <div className="chart-container">
                <div className="chart-header">
                    <h3>Progress Metrics Over Time</h3>
                    <div className="chart-info">
                        <Calendar size={16} />
                        <span>Last {dateRange} days</span>
                    </div>
                </div>
                
                {renderChart()}
            </div>

            {detailed && renderTrendIndicators()}
        </div>
    );
};

export default ProgressMetricsChart;
