import React from 'react';
import './PipelineMonitor.css';

export default function PipelineMonitor({ status, result }) {
  const getStatusColor = (st) => {
    switch (st) {
      case 'completed':
        return '#10b981';
      case 'running':
        return '#38bdf8';
      case 'error':
        return '#ef4444';
      case 'pending':
        return '#f59e0b';
      default:
        return '#94a3b8';
    }
  };

  const getStatusIcon = (st) => {
    switch (st) {
      case 'completed':
        return '✅';
      case 'running':
        return '⏳';
      case 'error':
        return '❌';
      case 'pending':
        return '⏰';
      default:
        return '❓';
    }
  };

  const agents = [
    { name: 'Coordinator', status: status?.status, icon: '🤝' },
    { name: 'Code Analysis', status: status?.status, icon: '🔍' },
    { name: 'Security Audit', status: status?.status, icon: '🔒' },
    { name: 'Report Generator', status: status?.status, icon: '📋' },
  ];

  return (
    <div className="monitor-container">
      <div className="status-card">
        <div className="status-header">
          <h2>Pipeline Execution</h2>
          <div className="status-badge" style={{ borderColor: getStatusColor(status.status) }}>
            <span>{getStatusIcon(status.status)}</span>
            <span>{status.status.toUpperCase()}</span>
          </div>
        </div>

        <div className="progress-section">
          <div className="progress-info">
            <span>Progress</span>
            <span className="progress-percent">{Math.round(status.progress * 100)}%</span>
          </div>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${status.progress * 100}%` }}
            ></div>
          </div>
        </div>

        <div className="timeline">
          {agents.map((agent, idx) => (
            <div key={idx} className="timeline-item">
              <div className="timeline-marker">
                <span className="marker-icon">{agent.icon}</span>
              </div>
              <div className="timeline-content">
                <h3>{agent.name}</h3>
                <p className={`status ${agent.status}`}>
                  {agent.status === 'completed'
                    ? '✓ Complete'
                    : agent.status === 'running'
                    ? '⧗ Processing...'
                    : agent.status === 'pending'
                    ? '⏱ Waiting...'
                    : '? Unknown'}
                </p>
              </div>
            </div>
          ))}
        </div>

        {result && (
          <div className="results-summary">
            <h3>Results</h3>
            <div className="result-stats">
              <div className="stat">
                <span className="stat-value">{result.files_analyzed}</span>
                <span className="stat-label">Files Analyzed</span>
              </div>
              {result.report_path && (
                <a href={`/api/report/${result.report_path.split('/').pop()}`} className="btn-download">
                  📄 Download Report
                </a>
              )}
              {result.trace_log_path && (
                <a href={`/api/log/${result.trace_log_path.split('/').pop()}`} className="btn-download">
                  📊 Download Trace
                </a>
              )}
            </div>

            {result.summary && (
              <div className="summary-text">
                <p>{result.summary}...</p>
              </div>
            )}
          </div>
        )}

        {status.status === 'error' && status.error && (
          <div className="error-details">
            <h3>Error</h3>
            <p>{status.error}</p>
          </div>
        )}
      </div>
    </div>
  );
}
