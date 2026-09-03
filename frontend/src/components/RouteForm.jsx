import React from 'react';

export default function RouteForm({
  nodes,
  startNode,
  setStartNode,
  destinationNode,
  setDestinationNode,
  stops,
  setStops,
  onSubmit,
  loading,
  onReset
}) {
  const handleAddStop = () => {
    // Pick first available node that isn't already used, or default to first node
    const defaultNode = nodes.find(n => n !== startNode && n !== destinationNode && !stops.includes(n)) || nodes[0];
    setStops([...stops, defaultNode]);
  };

  const handleRemoveStop = (index) => {
    const updated = stops.filter((_, i) => i !== index);
    setStops(updated);
  };

  const handleStopChange = (index, value) => {
    const updated = [...stops];
    updated[index] = value;
    setStops(updated);
  };

  const handleMoveStop = (index, direction) => {
    const newIndex = index + direction;
    if (newIndex < 0 || newIndex >= stops.length) return;
    const updated = [...stops];
    const temp = updated[index];
    updated[index] = updated[newIndex];
    updated[newIndex] = temp;
    setStops(updated);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit();
  };

  return (
    <form className="route-form-card" onSubmit={handleSubmit}>
      <h2 className="card-title">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 20h9M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
        </svg>
        Configure Trip
      </h2>

      {/* Start Selection */}
      <div className="form-group">
        <label className="form-label">
          <span className="node-indicator start"></span> Start Point
        </label>
        <select
          className="form-select"
          value={startNode}
          onChange={(e) => setStartNode(e.target.value)}
          disabled={loading}
        >
          {nodes.map((node) => (
            <option key={node} value={node}>
              Node {node}
            </option>
          ))}
        </select>
      </div>

      {/* Intermediate Stops */}
      <div className="form-group">
        <div className="label-with-action">
          <label className="form-label">
            <span className="node-indicator stop"></span> Intermediate Stops ({stops.length})
          </label>
          <button
            type="button"
            className="btn-text"
            onClick={handleAddStop}
            disabled={loading || nodes.length === 0}
          >
            + Add Stop
          </button>
        </div>

        {stops.length === 0 ? (
          <div className="empty-stops-hint">
            No stops added. Add intermediate destinations to test Linked List insertion.
          </div>
        ) : (
          <div className="stops-list">
            {stops.map((stop, index) => (
              <div key={index} className="stop-item-row">
                <span className="stop-number">{index + 1}</span>
                <select
                  className="form-select"
                  value={stop}
                  onChange={(e) => handleStopChange(index, e.target.value)}
                  disabled={loading}
                >
                  {nodes.map((node) => (
                    <option key={node} value={node}>
                      Node {node}
                    </option>
                  ))}
                </select>
                <div className="stop-actions">
                  <button
                    type="button"
                    className="btn-icon"
                    title="Move Up"
                    onClick={() => handleMoveStop(index, -1)}
                    disabled={index === 0 || loading}
                  >
                    ▲
                  </button>
                  <button
                    type="button"
                    className="btn-icon"
                    title="Move Down"
                    onClick={() => handleMoveStop(index, 1)}
                    disabled={index === stops.length - 1 || loading}
                  >
                    ▼
                  </button>
                  <button
                    type="button"
                    className="btn-icon danger"
                    title="Remove Stop"
                    onClick={() => handleRemoveStop(index)}
                    disabled={loading}
                  >
                    ✕
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Destination Selection */}
      <div className="form-group">
        <label className="form-label">
          <span className="node-indicator destination"></span> Destination
        </label>
        <select
          className="form-select"
          value={destinationNode}
          onChange={(e) => setDestinationNode(e.target.value)}
          disabled={loading}
        >
          {nodes.map((node) => (
            <option key={node} value={node}>
              Node {node}
            </option>
          ))}
        </select>
      </div>

      {/* Form Buttons */}
      <div className="form-actions">
        <button
          type="submit"
          className="btn-primary"
          disabled={loading}
        >
          {loading ? (
            <>
              <span className="spinner"></span> Calculating...
            </>
          ) : (
            <>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
              FIND ROUTE
            </>
          )}
        </button>

        {onReset && (
          <button
            type="button"
            className="btn-secondary"
            onClick={onReset}
            disabled={loading}
          >
            Reset
          </button>
        )}
      </div>
    </form>
  );
}
