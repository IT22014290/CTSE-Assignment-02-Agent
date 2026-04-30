import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Header from './components/Header';
import ReviewForm from './components/ReviewForm';
import PipelineMonitor from './components/PipelineMonitor';
import ResultsPanel from './components/ResultsPanel';
import ReportsHistory from './components/ReportsHistory';
import './App.css';

const API_BASE = 'http://localhost:8000/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('review');
  const [runId, setRunId] = useState(null);
  const [pipelineStatus, setPipelineStatus] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [config, setConfig] = useState(null);

  // Fetch configuration on mount
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await axios.get(`${API_BASE}/config`);
        setConfig(response.data);
      } catch (err) {
        console.error('Failed to fetch config:', err);
      }
    };
    fetchConfig();
  }, []);

  // Poll pipeline status
  useEffect(() => {
    if (!runId) return;

    const pollStatus = async () => {
      try {
        const statusResponse = await axios.get(`${API_BASE}/status/${runId}`);
        setPipelineStatus(statusResponse.data);

        if (statusResponse.data.status === 'completed') {
          try {
            const resultResponse = await axios.get(`${API_BASE}/result/${runId}`);
            setResult(resultResponse.data);
          } catch (err) {
            console.error('Failed to fetch result:', err);
          }
        }
      } catch (err) {
        console.error('Failed to poll status:', err);
      }
    };

    const interval = setInterval(pollStatus, 1000);
    return () => clearInterval(interval);
  }, [runId]);

  const handleStartReview = async (inputPath, model) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setPipelineStatus(null);

    try {
      const response = await axios.post(`${API_BASE}/review`, {
        input_path: inputPath,
        model: model,
      });

      setRunId(response.data.run_id);
      setActiveTab('monitor');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start review');
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <Header config={config} />
      
      <div className="container">
        <nav className="tabs">
          <button
            className={`tab-button ${activeTab === 'review' ? 'active' : ''}`}
            onClick={() => setActiveTab('review')}
          >
            <span className="tab-icon">🔍</span> New Review
          </button>
          <button
            className={`tab-button ${activeTab === 'monitor' ? 'active' : ''}`}
            onClick={() => setActiveTab('monitor')}
          >
            <span className="tab-icon">📊</span> Monitor
          </button>
          <button
            className={`tab-button ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            <span className="tab-icon">📋</span> History
          </button>
        </nav>

        <div className="content">
          {error && (
            <div className="error-banner">
              <span>⚠️ {error}</span>
              <button onClick={() => setError(null)}>×</button>
            </div>
          )}

          {activeTab === 'review' && (
            <ReviewForm onSubmit={handleStartReview} loading={loading} />
          )}

          {activeTab === 'monitor' && pipelineStatus && (
            <PipelineMonitor status={pipelineStatus} result={result} />
          )}

          {activeTab === 'history' && (
            <ReportsHistory />
          )}

          {result && activeTab === 'review' && (
            <ResultsPanel result={result} />
          )}
        </div>
      </div>
    </div>
  );
}
