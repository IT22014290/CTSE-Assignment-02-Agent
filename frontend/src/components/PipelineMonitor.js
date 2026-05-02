import React from 'react';
import './PipelineMonitor.css';

// Agent pipeline order — must match LangGraph node names
const AGENT_STEPS = [
  { key: 'coordinator',      label: 'Coordinator',      icon: '🤝' },
  { key: 'code_analysis',    label: 'Code Analysis',    icon: '🔍' },
  { key: 'security_audit',   label: 'Security Audit',   icon: '🔒' },
  { key: 'report_generator', label: 'Report Generator', icon: '📋' },
];

function getAgentStatus(agentKey, currentAgent, overallStatus) {
  if (overallStatus === 'completed') return 'completed';
  if (overallStatus === 'error')     return 'error';

  const currentIdx = AGENT_STEPS.findIndex(a => a.key === currentAgent);
  const agentIdx   = AGENT_STEPS.findIndex(a => a.key === agentKey);

  if (currentIdx === -1) return 'pending';          // not started yet
  if (agentIdx < currentIdx)  return 'completed';   // already done
  if (agentIdx === currentIdx) return 'running';    // currently running
  return 'pending';                                 // not yet reached
}

export default function PipelineMonitor({ status, result }) {
  const overall     = status?.status;
  const currentAgent = status?.current_agent;

  return (
    <div className="monitor-container">
      <div className="status-card">

        {/* ── Header ── */}
        <div className="status-header">
          <h2>Pipeline Execution</h2>
          <div className={`status-badge badge-${overall}`}>
            <span>
              {overall === 'completed' ? '✅'
               : overall === 'running'  ? '⏳'
               : overall === 'error'    ? '❌'
               : '⏰'}
            </span>
            <span>{overall?.toUpperCase()}</span>
          </div>
        </div>

        {/* ── Progress bar ── */}
        <div className="progress-section">
          <div className="progress-info">
            <span>Progress</span>
            <span className="progress-percent">
              {Math.round((status?.progress ?? 0) * 100)}%
            </span>
          </div>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${(status?.progress ?? 0) * 100}%` }}
            />
          </div>
        </div>

        {/* ── Per-agent timeline ── */}
        <div className="timeline">
          {AGENT_STEPS.map((agent) => {
            const agentStatus = getAgentStatus(agent.key, currentAgent, overall);
            return (
              <div key={agent.key} className={`timeline-item item-${agentStatus}`}>
                <div className="timeline-marker">
                  <span className="marker-icon">
                    {agentStatus === 'completed' ? '✅'
                     : agentStatus === 'running'  ? '⏳'
                     : agentStatus === 'error'    ? '❌'
                     : agent.icon}
                  </span>
                </div>
                <div className="timeline-content">
                  <h3>{agent.label}</h3>
                  <p className={`agent-status status-${agentStatus}`}>
                    {agentStatus === 'completed' ? '✓ Complete'
                     : agentStatus === 'running'  ? '⧗ Processing...'
                     : agentStatus === 'error'    ? '✗ Failed'
                     : '○ Waiting'}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* ── Results summary (shown when done) ── */}
        {result && (
          <div className="results-summary">
            <h3>Results</h3>
            <div className="result-stats">
              <div className="stat">
                <span className="stat-value">{result.files_analyzed}</span>
                <span className="stat-label">Files Analyzed</span>
              </div>
              {result.report_path && (
                <a
                  href={`http://localhost:8000/api/report/${result.report_path.split('/').pop()}`}
                  className="btn-download"
                  target="_blank"
                  rel="noreferrer"
                >
                  📄 Download Report
                </a>
              )}
              {result.trace_log_path && (
                <a
                  href={`http://localhost:8000/api/log/${result.trace_log_path.split('/').pop()}`}
                  className="btn-download"
                  target="_blank"
                  rel="noreferrer"
                >
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

        {/* ── Error details ── */}
        {overall === 'error' && status?.error && (
          <div className="error-details">
            <h3>Error</h3>
            <p>{status.error}</p>
          </div>
        )}

      </div>
    </div>
  );
}
