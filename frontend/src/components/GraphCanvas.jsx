import React from 'react';

export default function GraphCanvas({ graphData, routePath, startNode, destinationNode, stops }) {
  if (!graphData || !graphData.nodes) {
    return (
      <div className="graph-canvas-card loading">
        <div className="spinner"></div>
        <p>Loading road network graph...</p>
      </div>
    );
  }

  const { nodes, edges, positions } = graphData;

  // Determine which edges are in the active route path
  const routeEdgesSet = new Set();
  if (routePath && routePath.length > 1) {
    for (let i = 0; i < routePath.length - 1; i++) {
      const u = routePath[i];
      const v = routePath[i + 1];
      const key = [u, v].sort().join('-');
      routeEdgesSet.add(key);
    }
  }

  // Determine node step indexes in path
  const nodeSequenceMap = {};
  if (routePath) {
    routePath.forEach((node, idx) => {
      if (nodeSequenceMap[node] === undefined) {
        nodeSequenceMap[node] = idx + 1;
      }
    });
  }

  return (
    <div className="graph-canvas-card">
      <div className="card-header">
        <h2 className="card-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="18" cy="5" r="3" />
            <circle cx="6" cy="12" r="3" />
            <circle cx="18" cy="19" r="3" />
            <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
            <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
          </svg>
          Interactive Road Network Graph
        </h2>
        <div className="graph-legend">
          <span className="legend-item"><span className="legend-dot active-edge"></span> Route Path</span>
          <span className="legend-item"><span className="legend-dot default-edge"></span> Road Weight</span>
        </div>
      </div>

      <div className="svg-container">
        <svg viewBox="0 0 700 400" className="graph-svg">
          {/* Defs for gradients & filters */}
          <defs>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
            <linearGradient id="activeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="100%" stopColor="#059669" />
            </linearGradient>
          </defs>

          {/* Render Edges */}
          {edges.map((edge, idx) => {
            const posU = positions[edge.u];
            const posV = positions[edge.v];
            if (!posU || !posV) return null;

            const edgeKey = [edge.u, edge.v].sort().join('-');
            const isHighlighted = routeEdgesSet.has(edgeKey);

            // Midpoint for weight badge
            const midX = (posU.x + posV.x) / 2;
            const midY = (posU.y + posV.y) / 2;

            return (
              <g key={`edge-${idx}`} className={`edge-group ${isHighlighted ? 'active' : ''}`}>
                <line
                  x1={posU.x}
                  y1={posU.y}
                  x2={posV.x}
                  y2={posV.y}
                  className={`graph-edge ${isHighlighted ? 'active-line' : ''}`}
                  filter={isHighlighted ? 'url(#glow)' : undefined}
                />
                
                {/* Weight badge background & text */}
                <rect
                  x={midX - 14}
                  y={midY - 12}
                  width="28"
                  height="24"
                  rx="6"
                  className={`weight-badge-bg ${isHighlighted ? 'active-badge' : ''}`}
                />
                <text
                  x={midX}
                  y={midY + 4}
                  textAnchor="middle"
                  className={`weight-badge-text ${isHighlighted ? 'active-text' : ''}`}
                >
                  {edge.weight}
                </text>
              </g>
            );
          })}

          {/* Render Nodes */}
          {nodes.map((node) => {
            const pos = positions[node];
            if (!pos) return null;

            const isStart = node === startNode;
            const isDestination = node === destinationNode;
            const isStop = stops && stops.includes(node);
            const isInRoute = routePath && routePath.includes(node);
            const sequenceNum = nodeSequenceMap[node];

            let nodeClass = 'graph-node';
            if (isStart) nodeClass += ' node-start';
            else if (isDestination) nodeClass += ' node-dest';
            else if (isStop) nodeClass += ' node-stop';
            else if (isInRoute) nodeClass += ' node-route';

            return (
              <g key={`node-${node}`} className="node-group" transform={`translate(${pos.x}, ${pos.y})`}>
                {/* Pulse ring for active route nodes */}
                {isInRoute && (
                  <circle r="28" className="node-pulse-ring" />
                )}

                {/* Main Node Circle */}
                <circle
                  r="22"
                  className={nodeClass}
                  filter={isInRoute ? 'url(#glow)' : undefined}
                />

                {/* Node Identifier Letter */}
                <text y="5" textAnchor="middle" className="node-label">
                  {node}
                </text>

                {/* Sequence badge if in route */}
                {sequenceNum && (
                  <g transform="translate(14, -14)">
                    <circle r="9" className="sequence-badge-bg" />
                    <text y="3" textAnchor="middle" className="sequence-badge-text">
                      {sequenceNum}
                    </text>
                  </g>
                )}
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
