import React from 'react';
import './ResultsPanel.css';

export default function ResultsPanel({ result }) {
  const getReportUrl = () => {
    if (!result.report_path) return null;
    const filename = result.report_path.split('/').pop();
    return `/api/report/${filename}`;
  };

  const getLogUrl = () => {
    if (!result.trace_log_path) return null;
    const filename = result.trace_log_path.split('/').pop();
    return `/api/log/${filename}`;
  };

  return (
    <div className="results-panel">
      <div className="results-card">
        <div className="results-header">
          <h2>✅ Review Complete!</h2>
          <p>Your code has been analyzed by the multi-agent system</p>
        </div>

        <div className="results-grid">
          <div className="result-box">
            <div className="result-icon">📁</div>
            <div className="result-info">
              <span className="label">Files Analyzed</span>
              <span className="value">{result.files_analyzed}</span>
            </div>
          </div>

          {result.report_path && (
            <div className="result-box clickable">
              <a href={getReportUrl()} className="download-link">
                <div className="result-icon">📄</div>
                <div className="result-info">
                  <span className="label">Full Report</span>
                  <span className="value">Available</span>
                </div>
              </a>
            </div>
          )}

          {result.trace_log_path && (
            <div className="result-box clickable">
              <a href={getLogUrl()} className="download-link">
                <div className="result-icon">📊</div>
                <div className="result-info">
                  <span className="label">Trace Log</span>
                  <span className="value">JSON</span>
                </div>
              </a>
            </div>
          )}
        </div>

        {result.summary && (
          <div className="summary-section">
            <h3>Summary</h3>
            <div className="summary-content">
              <p>{result.summary}</p>
            </div>
          </div>
        )}

        <div className="action-buttons">
          <button onClick={() => window.location.reload()} className="btn-new">
            🔄 Start New Review
          </button>
        </div>
      </div>
    </div>
  );
}
