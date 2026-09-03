import React from 'react';

export default function Header({ isConnected }) {
  return (
    <header className="app-header">
      <div className="header-brand">
        <div className="logo-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M12 2a8 8 0 0 0-8 8c0 5.25 8 12 8 12s8-6.75 8-12a8 8 0 0 0-8-8z" />
            <circle cx="12" cy="10" r="3" />
          </svg>
        </div>
        <div>
          <h1 className="header-title">Route Planner</h1>
          <p className="header-subtitle">Graph • Dijkstra Shortest Path • Doubly Linked List</p>
        </div>
      </div>
      <div className="connection-badge">
        <span className={`status-dot ${isConnected ? 'online' : 'offline'}`}></span>
        <span>{isConnected ? 'FastAPI Connected' : 'Connecting to Server...'}</span>
      </div>
    </header>
  );
}
