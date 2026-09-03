import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import RouteForm from './components/RouteForm';
import GraphCanvas from './components/GraphCanvas';
import RouteSummary from './components/RouteSummary';
import { fetchGraph, calculateRoute, calculateMultiStopRoute } from './services/api';

export default function App() {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [], positions: {} });
  const [isConnected, setIsConnected] = useState(false);

  // Form State initialized with prompt example defaults (A -> [D, C] -> F)
  const [startNode, setStartNode] = useState('A');
  const [destinationNode, setDestinationNode] = useState('F');
  const [stops, setStops] = useState(['D', 'C']);

  // Results State
  const [routeResult, setRouteResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load graph structure from FastAPI backend
  useEffect(() => {
    async function loadGraph() {
      try {
        const data = await fetchGraph();
        setGraphData(data);
        setIsConnected(true);
      } catch (err) {
        console.error('Failed to load graph:', err);
        setIsConnected(false);
        setError('Cannot connect to FastAPI backend server. Ensure backend is running on port 8000.');
      }
    }
    loadGraph();
  }, []);

  // Handle Route Calculation
  const handleCalculateRoute = useCallback(async () => {
    if (!startNode || !destinationNode) return;

    setLoading(true);
    setError(null);

    try {
      let result;
      if (stops.length > 0) {
        result = await calculateMultiStopRoute(startNode, stops, destinationNode);
      } else {
        result = await calculateRoute(startNode, destinationNode);
      }
      setRouteResult(result);
    } catch (err) {
      console.error('Route calculation error:', err);
      setError(err.message || 'Error computing route.');
      setRouteResult({ error: err.message });
    } finally {
      setLoading(false);
    }
  }, [startNode, destinationNode, stops]);

  // Automatically calculate initial route once graph is loaded
  useEffect(() => {
    if (isConnected && graphData.nodes.length > 0 && !routeResult) {
      handleCalculateRoute();
    }
  }, [isConnected, graphData, routeResult, handleCalculateRoute]);

  const handleReset = () => {
    setStartNode('A');
    setDestinationNode('F');
    setStops(['D', 'C']);
    setRouteResult(null);
  };

  return (
    <div className="app-container">
      <Header isConnected={isConnected} />

      {error && !routeResult && (
        <div className="error-banner" style={{ background: '#7f1d1d', color: '#fca5a5', padding: '12px 20px', borderRadius: '12px', marginBottom: '20px' }}>
          <strong>Error: </strong>{error}
        </div>
      )}

      <main className="app-grid">
        <aside className="sidebar-column">
          <RouteForm
            nodes={graphData.nodes}
            startNode={startNode}
            setStartNode={setStartNode}
            destinationNode={destinationNode}
            setDestinationNode={setDestinationNode}
            stops={stops}
            setStops={setStops}
            onSubmit={handleCalculateRoute}
            loading={loading}
            onReset={handleReset}
          />
        </aside>

        <section className="main-content-column">
          <GraphCanvas
            graphData={graphData}
            routePath={routeResult?.route || routeResult?.path}
            startNode={startNode}
            destinationNode={destinationNode}
            stops={stops}
          />

          <RouteSummary
            routeResult={routeResult}
            isMultiStop={stops.length > 0}
          />
        </section>
      </main>
    </div>
  );
}
