import React, { useState } from 'react';
import './ReviewForm.css';

export default function ReviewForm({ onSubmit, loading }) {
  const [inputPath, setInputPath] = useState('');
  const [model, setModel] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    if (!inputPath.trim()) {
      setError('Please enter a directory path');
      return;
    }

    onSubmit(inputPath, model);
  };

  return (
    <div className="review-form-container">
      <div className="form-card">
        <div className="form-header">
          <h2>Start Code Review</h2>
          <p>Analyze Python code for quality and security issues</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="inputPath">Directory Path *</label>
            <div className="input-wrapper">
              <span className="input-icon">📁</span>
              <input
                id="inputPath"
                type="text"
                placeholder="e.g., /path/to/project or ./tests/sample_code"
                value={inputPath}
                onChange={(e) => setInputPath(e.target.value)}
                disabled={loading}
              />
            </div>
            <p className="hint">Provide absolute or relative path to Python source directory</p>
          </div>

          <div className="form-group">
            <label htmlFor="model">Ollama Model (Optional)</label>
            <select
              id="model"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              disabled={loading}
            >
              <option value="">Use Default</option>
              <option value="llama3">llama3:8b</option>
              <option value="phi3">phi3</option>
              <option value="mistral">mistral</option>
              <option value="qwen2">qwen2</option>
            </select>
          </div>

          {error && <div className="error-message">{error}</div>}

          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? (
                <>
                  <span className="spinner"></span> Starting Review...
                </>
              ) : (
                <>
                  <span>🚀</span> Start Review
                </>
              )}
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setInputPath('tests/sample_code')}
              disabled={loading}
            >
              📋 Use Sample
            </button>
          </div>
        </form>

        <div className="features">
          <h3>Features</h3>
          <div className="features-grid">
            <div className="feature">
              <span className="feature-icon">🔍</span>
              <span>Code Quality Analysis</span>
            </div>
            <div className="feature">
              <span className="feature-icon">🔒</span>
              <span>Security Audits</span>
            </div>
            <div className="feature">
              <span className="feature-icon">📊</span>
              <span>Detailed Reports</span>
            </div>
            <div className="feature">
              <span className="feature-icon">⚡</span>
              <span>Local & Fast</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
