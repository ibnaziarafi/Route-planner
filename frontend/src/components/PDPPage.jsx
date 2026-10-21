import React, { useEffect, useMemo, useRef, useState } from 'react';
import Header from './Header';
import GraphCanvas from './GraphCanvas';
import { fetchGraph, solvePDP } from '../services/api';

const makeDriver = (id, startNode = 'A') => ({ driver_id: id, start_node: startNode, capacity: 5 });
const makeOrder = (id, pickupNode = 'B', dropoffNode = 'H') => ({
  order_id: id,
  pickup_node: pickupNode,
  dropoff_node: dropoffNode,
  demand: 1,
});

export default function PDPPage() {
  const [graphType, setGraphType] = useState('medium');
  const [algorithm, setAlgorithm] = useState('scratch');
  const [graphData, setGraphData] = useState({ nodes: [], edges: [], positions: {} });
  const [drivers, setDrivers] = useState([makeDriver(1, 'A')]);
  const [orders, setOrders] = useState([makeOrder(1, 'B', 'H')]);
  const [result, setResult] = useState(null);
  const [selectedDriverId, setSelectedDriverId] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [mode, setMode] = useState('save');
  const [activationCost, setActivationCost] = useState(20);
  const [costPerKm, setCostPerKm] = useState(0.5);
  const [speedKph, setSpeedKph] = useState(30);
  const [serviceMinutes, setServiceMinutes] = useState(1);
  const requestVersion = useRef(0);

  const invalidate = () => { requestVersion.current += 1; setResult(null); setError(null); setLoading(false); };

  useEffect(() => {
    fetchGraph(graphType)
      .then(setGraphData)
      .catch(() => setError('Cannot connect to FastAPI backend server.'));
  }, [graphType]);

  const selectedRoute = useMemo(
    () => result?.routes?.find((route) => route.driver_id === selectedDriverId),
    [result, selectedDriverId],
  );

  const updateDriver = (driverId, field, value) => {
    invalidate();
    setDrivers((current) => current.map((driver) => (
      driver.driver_id === driverId ? { ...driver, [field]: field === 'capacity' ? Number(value) : value } : driver
    )));
  };

  const updateOrder = (orderId, field, value) => {
    invalidate();
    setOrders((current) => current.map((order) => (
      order.order_id === orderId ? { ...order, [field]: field === 'demand' ? Number(value) : value } : order
    )));
  };

  const addDriver = () => {
    invalidate();
    const id = Math.max(0, ...drivers.map((driver) => driver.driver_id)) + 1;
    setDrivers([...drivers, makeDriver(id, graphData.nodes[0] || 'A')]);
  };

  const addOrder = () => {
    invalidate();
    const id = Math.max(0, ...orders.map((order) => order.order_id)) + 1;
    const nodeCount = graphData.nodes.length;
    const pickupIndex = nodeCount > 1 ? id % nodeCount : 0;
    const dropoffIndex = nodeCount > 1 ? (id * 3 + 1) % nodeCount : 0;
    const first = graphData.nodes[pickupIndex] || 'B';
    const last = graphData.nodes[dropoffIndex] || 'C';
    if (first === last && nodeCount > 1) {
      setOrders([...orders, makeOrder(id, first, graphData.nodes[(dropoffIndex + 1) % nodeCount])]);
      return;
    }
    setOrders([...orders, makeOrder(id, first, last)]);
  };

  const optimize = async () => {
    const version = ++requestVersion.current;
    setLoading(true);
    setError(null);
    try {
      const nextResult = await solvePDP(drivers, orders, graphType, algorithm, 5, { mode, activation_cost: Number(activationCost), cost_per_km: Number(costPerKm), speed_kph: Number(speedKph), service_minutes_per_stop: Number(serviceMinutes) });
      if (version === requestVersion.current) {
        setResult(nextResult);
        if (nextResult.routes?.length) setSelectedDriverId(nextResult.routes[0].driver_id);
      }
    } catch (err) {
      if (version === requestVersion.current) { setError(err.message); setResult(null); }
    } finally {
      if (version === requestVersion.current) setLoading(false);
    }
  };

  const routePath = selectedRoute?.full_path || [];
  const routeStops = selectedRoute?.stops?.map((stop) => stop.node) || [];

  return (
    <div className="app-container">
      <Header isConnected={graphData.nodes.length > 0} />
      {error && <div className="error-banner">{error}</div>}

      <main className="app-grid pdp-grid">
        <aside className="sidebar-column">
          <section className="route-form-card pdp-form-card">
            <div className="card-header">
              <h2 className="card-title">PDP setup</h2>
              <div className="pdp-header-controls">
                <select className="form-select compact-select" value={graphType} onChange={(event) => { invalidate(); setGraphType(event.target.value); }}>
                  <option value="small">Small graph</option>
                  <option value="medium">Medium graph</option>
                </select>
                <select className="form-select compact-select" value={algorithm} onChange={(event) => { invalidate(); setAlgorithm(event.target.value); }} aria-label="PDP algorithm">
                  <option value="scratch">From-scratch heuristic</option>
                  <option value="ortools">Google OR-Tools</option>
                  <option value="pyvrp">PyVRP hybrid genetic search</option>
                  <option value="learned">Locally trained linear RL</option>
                </select>
              </div>
            </div>

            <div className="pdp-section">
              <label className="form-label">Objective mode<select className="form-select" value={mode} onChange={e=>{setMode(e.target.value);invalidate();}}><option value="save">Save · minimize economic fleet cost</option><option value="time">Time · use all drivers, minimize makespan</option></select></label>
              <div className="pdp-header-controls"><label className="form-label">Fleet activation<input className="pdp-number" type="number" min="0" value={activationCost} onChange={e=>{setActivationCost(e.target.value);invalidate();}} /></label><label className="form-label">Cost / km<input className="pdp-number" type="number" min="0" step="0.1" value={costPerKm} onChange={e=>{setCostPerKm(e.target.value);invalidate();}} /></label><label className="form-label">Speed km/h<input className="pdp-number" type="number" min="1" value={speedKph} onChange={e=>{setSpeedKph(e.target.value);invalidate();}} /></label><label className="form-label">Service / stop<input className="pdp-number" type="number" min="0" step="0.5" value={serviceMinutes} onChange={e=>{setServiceMinutes(e.target.value);invalidate();}} /></label></div>
            </div>

            <div className="pdp-section">
              <div className="label-with-action">
                <label className="form-label">Drivers</label>
                <button className="btn-text" type="button" onClick={addDriver}>+ Add driver</button>
              </div>
              {drivers.map((driver) => (
                <div className="pdp-row" key={driver.driver_id}>
                  <span className="pdp-row-title">D{driver.driver_id}</span>
                  <select className="form-select" value={driver.start_node} onChange={(event) => updateDriver(driver.driver_id, 'start_node', event.target.value)}>
                    {graphData.nodes.map((node) => <option key={node}>{node}</option>)}
                  </select>
                  <input className="pdp-number" type="number" min="1" value={driver.capacity} aria-label={`Driver ${driver.driver_id} capacity`} onChange={(event) => updateDriver(driver.driver_id, 'capacity', event.target.value)} />
                  {drivers.length > 1 && <button className="btn-icon danger" type="button" onClick={() => { invalidate(); setDrivers(drivers.filter((item) => item.driver_id !== driver.driver_id)); }} aria-label={`Remove driver ${driver.driver_id}`}>×</button>}
                </div>
              ))}
            </div>

            <div className="pdp-section">
              <div className="label-with-action">
                <label className="form-label">Parcel requests</label>
                <button className="btn-text" type="button" onClick={addOrder}>+ Add parcel</button>
              </div>
              {orders.map((order) => (
                <div className="pdp-order" key={order.order_id}>
                  <div className="pdp-order-heading"><span>Parcel {order.order_id}</span><button className="btn-icon danger" type="button" onClick={() => { invalidate(); setOrders(orders.filter((item) => item.order_id !== order.order_id)); }} aria-label={`Remove parcel ${order.order_id}`}>×</button></div>
                  <div className="pdp-row">
                    <select className="form-select" value={order.pickup_node} onChange={(event) => updateOrder(order.order_id, 'pickup_node', event.target.value)} aria-label={`Parcel ${order.order_id} pickup`}>
                      {graphData.nodes.map((node) => <option key={node}>{node}</option>)}
                    </select>
                    <span className="pdp-arrow">→</span>
                    <select className="form-select" value={order.dropoff_node} onChange={(event) => updateOrder(order.order_id, 'dropoff_node', event.target.value)} aria-label={`Parcel ${order.order_id} dropoff`}>
                      {graphData.nodes.map((node) => <option key={node}>{node}</option>)}
                    </select>
                  </div>
                </div>
              ))}
            </div>

            <button className="btn-primary" type="button" onClick={optimize} disabled={loading || graphData.nodes.length === 0}>
              {loading ? 'Optimizing...' : 'Optimize fleet routes'}
            </button>
          </section>
        </aside>

        <section className="main-content-column">
          <GraphCanvas graphData={graphData} routePath={routePath} startNode={selectedRoute?.start_node} stops={routeStops} />
          <section className="route-form-card pdp-results">
            <div className="card-header"><h2 className="card-title">Driver routes</h2><span className="pdp-total">{result ? `${result.algorithm} · ${result.total_distance} km · ${mode} mode` : 'Not optimized'}</span></div>
            {result?.routes?.length ? (
              <>
                <div className="driver-tabs">
                  {result.routes.map((route) => <button className={route.driver_id === selectedDriverId ? 'driver-tab active' : 'driver-tab'} type="button" key={route.driver_id} onClick={() => setSelectedDriverId(route.driver_id)}>Driver {route.driver_id}</button>)}
                </div>
                <div className="route-detail"><strong>{mode === 'save' ? 'Save objective · economic fleet cost' : 'Time objective · parallel makespan'}</strong><span>{result.objective_value != null ? `${Number(result.objective_value).toFixed(2)} ${mode === 'save' ? 'cost units' : 'min max'}` : `No complete feasible ${mode} objective · ${result.status || 'see validation'}`}</span><p>Assumptions: {speedKph} km/h · {serviceMinutes} min per stop · open routes · graph units use the API&apos;s configured scale.</p></div>
                {selectedRoute && <div className="route-detail"><strong>Driver {selectedRoute.driver_id}</strong><span>{selectedRoute.total_distance} km</span><p>{selectedRoute.stops.length ? selectedRoute.stops.map((stop) => `${stop.type === 'pickup' ? 'Pick' : 'Drop'} ${stop.order_id} at ${stop.node}`).join('  •  ') : 'No assigned parcels'}</p></div>}
                {result.unassigned_orders.length > 0 && <p className="pdp-warning">Unassigned parcels: {result.unassigned_orders.join(', ')}</p>}
              </>
            ) : <p className="empty-stops-hint">Add drivers and parcels, then optimize to inspect each driver&apos;s route.</p>}
          </section>
        </section>
      </main>
    </div>
  );
}
