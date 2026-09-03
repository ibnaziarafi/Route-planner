import React from 'react';

export default function RouteSummary({ routeResult, isMultiStop }) {
  if (!routeResult) {
    return (
      <div className="route-summary-card placeholder">
        <div className="placeholder-content">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <polygon points="12 2 2 7 12 12 22 7 12 2" />
            <polyline points="2 17 12 22 22 17" />
            <polyline points="2 12 12 17 22 12" />
          </svg>
          <h3>Ready to Calculate Route</h3>
          <p>Select your start point, intermediate stops, and destination, then click <strong>FIND ROUTE</strong>.</p>
        </div>
      </div>
    );
  }

  const { path, route, distance, error } = routeResult;
  const pathNodes = route || path || [];

  if (error) {
    return (
      <div className="route-summary-card error-card">
        <h3>Route Calculation Error</h3>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="route-summary-card">
      <div className="card-header">
        <h2 className="card-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="9 11 12 14 22 4" />
            <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
          </svg>
          Calculated Route Results
        </h2>
        <span className="badge-type">{isMultiStop ? 'Multi-Stop Route' : 'Direct Route'}</span>
      </div>

      <div className="results-grid">
        {/* Total Distance Card */}
        <div className="metric-card">
          <span className="metric-label">Total Route Distance</span>
          <div className="metric-value">
            {distance} <span className="metric-unit">km</span>
          </div>
        </div>

        {/* Total Stops Count Card */}
        <div className="metric-card">
          <span className="metric-label">Nodes Visited</span>
          <div className="metric-value">
            {pathNodes.length} <span className="metric-unit">stops</span>
          </div>
        </div>
      </div>

      {/* Path Display */}
      <div className="path-display-section">
        <h3 className="section-subtitle">Calculated Path</h3>
        <div className="path-pills-row">
          {pathNodes.map((node, index) => (
            <React.Fragment key={index}>
              <div className="path-pill">
                <span className="pill-index">{index + 1}</span>
                <span className="pill-name">Node {node}</span>
              </div>
              {index < pathNodes.length - 1 && (
                <span className="path-arrow">➔</span>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Doubly Linked List Structural Demonstration */}
      <div className="linked-list-structure-section">
        <h3 className="section-subtitle">
          Doubly Linked List Structure (RouteLinkedList)
        </h3>
        <div className="linked-list-viz">
          <span className="node-terminal">HEAD</span>
          <span className="pointer-arrow">➔</span>
          {pathNodes.map((node, index) => (
            <React.Fragment key={`ll-${index}`}>
              <div className="ll-node-box">
                <div className="ll-node-header">RouteNode</div>
                <div className="ll-node-value">{node}</div>
                <div className="ll-node-pointers">
                  <span title="prev pointer">← prev</span>
                  <span title="next pointer">next →</span>
                </div>
              </div>
              <span className="pointer-arrow">&lt;➔&gt;</span>
            </React.Fragment>
          ))}
          <span className="node-terminal">NULL</span>
        </div>
      </div>
    </div>
  );
}
