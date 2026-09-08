import React, { useState } from 'react';
import Header from './Header';
import RealMapCanvas from './RealMapCanvas';
import { calculateRealMapRoute } from '../services/realMapApi';
import './RealMapPage.css';

const DEFAULT_START = { lat: -42.881, lon: 147.327 };
const DEFAULT_END = { lat: -42.874, lon: 147.327 };

export default function RealMapPage() {
  const [start, setStart] = useState(DEFAULT_START);
  const [end, setEnd] = useState(DEFAULT_END);
  const [activeTarget, setActiveTarget] = useState('start');
  const [algorithm, setAlgorithm] = useState('dijkstra_v2');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const updateLocation = (target, field, value) => {
    const setter = target === 'start' ? setStart : setEnd;
    setter((current) => ({ ...current, [field]: Number(value) }));
    setResult(null);
  };

  const handleMapSelect = (target, location) => {
    const setter = target === 'start' ? setStart : setEnd;
    setter(location);
    setResult(null);
  };

  const calculateRoute = async () => {
    setLoading(true);
    setError(null);
    try {
      setResult(await calculateRealMapRoute({ start, end, algorithm }));
    } catch (requestError) {
      setError(requestError.message);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container real-map-page">
      <Header isConnected />
      <div className="page-switcher">
        <a href="/">Single Route Planner</a>
        <a href="/pdp">Pickup &amp; Delivery</a>
        <strong>Real Map</strong>
      </div>
      <main className="real-map-layout">
        <section className="real-map-panel">
          <div className="real-map-heading">
            <p className="real-map-kicker">Hobart, Tasmania</p>
            <h1>Real Map Routing</h1>
            <p>Select two locations on the map or enter coordinates, then run the existing routing algorithms on the OpenStreetMap road graph.</p>
          </div>
          <div className="location-control">
            <div className="location-control-header"><span className="map-marker-dot start-dot" /> <strong>Start location</strong><button type="button" className={activeTarget === 'start' ? 'target-button active' : 'target-button'} onClick={() => setActiveTarget('start')}>Pick on map</button></div>
            <div className="coordinate-grid">
              <label>Latitude<input type="number" step="0.000001" value={start.lat} onChange={(event) => updateLocation('start', 'lat', event.target.value)} /></label>
              <label>Longitude<input type="number" step="0.000001" value={start.lon} onChange={(event) => updateLocation('start', 'lon', event.target.value)} /></label>
            </div>
          </div>
          <div className="location-control">
            <div className="location-control-header"><span className="map-marker-dot end-dot" /> <strong>Destination</strong><button type="button" className={activeTarget === 'end' ? 'target-button active' : 'target-button'} onClick={() => setActiveTarget('end')}>Pick on map</button></div>
            <div className="coordinate-grid">
              <label>Latitude<input type="number" step="0.000001" value={end.lat} onChange={(event) => updateLocation('end', 'lat', event.target.value)} /></label>
              <label>Longitude<input type="number" step="0.000001" value={end.lon} onChange={(event) => updateLocation('end', 'lon', event.target.value)} /></label>
            </div>
          </div>
          <label className="algorithm-control">Algorithm<select value={algorithm} onChange={(event) => { setAlgorithm(event.target.value); setResult(null); }}><option value="dijkstra">Dijkstra</option><option value="dijkstra_v2">Dijkstra V2</option><option value="a_star">A*</option></select></label>
          <button type="button" className="btn-primary real-map-submit" onClick={calculateRoute} disabled={loading}>{loading ? 'Calculating route...' : 'Calculate Route'}</button>
          {error && <div className="error-banner real-map-error">{error}</div>}
          {result && <div className="real-map-result"><span>Route status</span><strong>{result.algorithm} complete</strong><span>Distance</span><strong>{result.distance.toLocaleString()} metres</strong><small>Snapped to {result.start_node} → {result.end_node} · {result.path.length} road nodes</small></div>}
        </section>
        <section className="real-map-view-panel">
          <div className="map-instruction">Click the map to set the {activeTarget === 'start' ? 'start' : 'destination'} location.</div>
          <RealMapCanvas start={start} end={end} route={result?.path || []} activeTarget={activeTarget} onSelect={handleMapSelect} />
        </section>
      </main>
    </div>
  );
}
