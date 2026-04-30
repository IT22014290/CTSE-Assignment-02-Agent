import React from 'react';
import './Header.css';

export default function Header({ config }) {
  return (
    <header className="header">
      <div className="header-content">
        <div className="header-left">
          <div className="logo">
            <span className="logo-icon">🤖</span>
            <div className="logo-text">
              <h1>MAS Code Review</h1>
              <p>Multi-Agent System for Python Analysis</p>
            </div>
          </div>
        </div>
        <div className="header-right">
          {config && (
            <div className="model-badge">
              <span className="badge-icon">🧠</span>
              <span className="badge-text">{config.ollama_model}</span>
            </div>
          )}
        </div>
      </div>
      <div className="header-gradient"></div>
    </header>
  );
}
