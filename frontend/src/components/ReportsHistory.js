import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './ReportsHistory.css';

const API_BASE = 'http://localhost:8000/api';

export default function ReportsHistory() {
  const [reports, setReports] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('reports');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [reportsRes, logsRes] = await Promise.all([
          axios.get(`${API_BASE}/reports`),
          axios.get(`${API_BASE}/logs`),
        ]);
        setReports(reportsRes.data.reports || []);
        setLogs(logsRes.data.logs || []);
      } catch (err) {
        console.error('Failed to fetch history:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleString();
  };

  const formatSize = (bytes) => {
    const kb = bytes / 1024;
    return kb < 1024 ? `${kb.toFixed(1)} KB` : `${(kb / 1024).toFixed(1)} MB`;
  };

  return (
    <div className="history-container">
      <div className="history-tabs">
        <button
          className={`history-tab ${activeTab === 'reports' ? 'active' : ''}`}
          onClick={() => setActiveTab('reports')}
        >
          📋 Reports ({reports.length})
        </button>
        <button
          className={`history-tab ${activeTab === 'logs' ? 'active' : ''}`}
          onClick={() => setActiveTab('logs')}
        >
          📊 Trace Logs ({logs.length})
        </button>
      </div>

      {loading ? (
        <div className="loading">Loading history...</div>
      ) : (
        <div className="history-content">
          {activeTab === 'reports' && (
            <div className="history-list">
              {reports.length === 0 ? (
                <p className="empty-state">No reports yet. Start a review to generate reports!</p>
              ) : (
                reports.map((report, idx) => (
                  <div key={idx} className="history-item">
                    <div className="item-info">
                      <h3>{report.filename}</h3>
                      <p>{formatDate(report.created_at)}</p>
                    </div>
                    <div className="item-meta">
                      <span className="size">{formatSize(report.size)}</span>
                      <a href={`${API_BASE}/report/${report.filename}`} className="download-btn">
                        📥 Download
                      </a>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'logs' && (
            <div className="history-list">
              {logs.length === 0 ? (
                <p className="empty-state">No trace logs yet.</p>
              ) : (
                logs.map((log, idx) => (
                  <div key={idx} className="history-item">
                    <div className="item-info">
                      <h3>{log.filename}</h3>
                      <p>{formatDate(log.created_at)}</p>
                    </div>
                    <div className="item-meta">
                      <span className="size">{formatSize(log.size)}</span>
                      <a href={`${API_BASE}/log/${log.filename}`} className="download-btn">
                        📥 Download
                      </a>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
