import React, { useState } from 'react';
import Header from './Header';
import RealMapPDPMap from './RealMapPDPMap';
import { solveRealMapPDP } from '../services/realMapPdpApi';
import './RealMapPDPPage.css';

const LOCATIONS = [{ lat: -42.881, lon: 147.327 }, { lat: -42.874, lon: 147.327 }, { lat: -42.881, lon: 147.315 }, { lat: -42.875, lon: 147.32 }, { lat: -42.888, lon: 147.315 }];
const driverDefaults = (id) => ({ driver_id: id, start_lat: LOCATIONS[(id - 1) % LOCATIONS.length].lat, start_lon: LOCATIONS[(id - 1) % LOCATIONS.length].lon, capacity: 3 });
const orderDefaults = (id) => { const pickup = LOCATIONS[(id + 1) % LOCATIONS.length]; const dropoff = LOCATIONS[(id + 2) % LOCATIONS.length]; return { order_id: id, pickup_lat: pickup.lat, pickup_lon: pickup.lon, dropoff_lat: dropoff.lat, dropoff_lon: dropoff.lon, demand: 1 }; };

export default function RealMapPDPPage() {
  const [drivers, setDrivers] = useState([driverDefaults(1)]);
  const [orders, setOrders] = useState([orderDefaults(1)]);
  const [algorithm, setAlgorithm] = useState('dijkstra_v2');
  const [solver, setSolver] = useState('scratch');
  const [target, setTarget] = useState({ type: 'driver', driverId: 1 });
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const updateLocation = (targetInfo, location) => {
    if (targetInfo.type === 'driver') setDrivers((items) => items.map((item) => item.driver_id === targetInfo.driverId ? { ...item, start_lat: location.lat, start_lon: location.lon } : item));
    if (targetInfo.type === 'pickup') setOrders((items) => items.map((item) => item.order_id === targetInfo.orderId ? { ...item, pickup_lat: location.lat, pickup_lon: location.lon } : item));
    if (targetInfo.type === 'dropoff') setOrders((items) => items.map((item) => item.order_id === targetInfo.orderId ? { ...item, dropoff_lat: location.lat, dropoff_lon: location.lon } : item));
    setResult(null);
  };
  const updateDriver = (id, field, value) => setDrivers((items) => items.map((item) => item.driver_id === id ? { ...item, [field]: Number(value) } : item));
  const addDriver = () => { const id = Math.max(...drivers.map((item) => item.driver_id), 0) + 1; setDrivers([...drivers, driverDefaults(id)]); };
  const addOrder = () => { const id = Math.max(...orders.map((item) => item.order_id), 0) + 1; setOrders([...orders, orderDefaults(id)]); };
  const optimize = async () => { setLoading(true); setError(null); try { setResult(await solveRealMapPDP({ drivers, orders, algorithm, solver })); } catch (requestError) { setError(requestError.message); setResult(null); } finally { setLoading(false); } };

  return <div className="app-container real-map-pdp-page">
    <Header isConnected />
    <div className="page-switcher"><a href="/">Single Route Planner</a><a href="/pdp">Pickup &amp; Delivery</a><a href="/real-map">Real Map</a><strong>Real Map PDP</strong></div>
    <main className="real-map-pdp-layout">
      <section className="real-map-pdp-panel">
        <div className="real-map-heading"><p className="real-map-kicker">OpenStreetMap · Hobart</p><h1>Real-World Delivery Optimizer</h1><p>Set real locations, then let the PDP solver choose the stop order while the selected routing algorithm follows actual roads.</p></div>
        <div className="pdp-control-section"><div className="section-title"><strong>Drivers</strong><button className="btn-text" type="button" onClick={addDriver}>+ Add driver</button></div>{drivers.map((driver) => <div className="real-pdp-driver" key={driver.driver_id}><div><strong>Driver {driver.driver_id}</strong><button className={target.type === 'driver' && target.driverId === driver.driver_id ? 'target-button active' : 'target-button'} type="button" onClick={() => setTarget({ type: 'driver', driverId: driver.driver_id })}>Select on map</button></div><label>Capacity<input type="number" min="1" value={driver.capacity} onChange={(event) => updateDriver(driver.driver_id, 'capacity', event.target.value)} /></label></div>)}</div>
        <div className="pdp-control-section"><div className="section-title"><strong>Orders</strong><button className="btn-text" type="button" onClick={addOrder}>+ Add order</button></div>{orders.map((order) => <div className="real-pdp-order" key={order.order_id}><div className="order-title"><strong>Order {order.order_id}</strong></div><div className="order-actions"><button className={target.type === 'pickup' && target.orderId === order.order_id ? 'target-button active pickup-button' : 'target-button pickup-button'} type="button" onClick={() => setTarget({ type: 'pickup', orderId: order.order_id })}>Pickup on map</button><button className={target.type === 'dropoff' && target.orderId === order.order_id ? 'target-button active dropoff-button' : 'target-button dropoff-button'} type="button" onClick={() => setTarget({ type: 'dropoff', orderId: order.order_id })}>Dropoff on map</button></div></div>)}</div>
        <div className="real-pdp-selects"><label>Shortest path<select value={algorithm} onChange={(event) => setAlgorithm(event.target.value)}><option value="dijkstra">Dijkstra</option><option value="dijkstra_v2">Dijkstra V2</option><option value="a_star">A*</option></select></label><label>PDP solver<select value={solver} onChange={(event) => setSolver(event.target.value)}><option value="scratch">From-scratch heuristic</option><option value="ortools">Google OR-Tools</option><option value="pyvrp">PyVRP</option></select></label></div>
        <button className="btn-primary real-map-submit" type="button" onClick={optimize} disabled={loading}>{loading ? 'Optimizing routes...' : 'Optimize Route'}</button>
        {error && <div className="error-banner real-map-error">{error}</div>}
        {result && <div className="real-pdp-stats"><strong>Optimization Result</strong><span>Drivers: {drivers.length} · Orders: {orders.length}</span><span>Assigned: {orders.length - result.unassigned_orders.length} · Unassigned: {result.unassigned_orders.length}</span><b>{result.total_distance_km.toFixed(3)} km</b><small>Shortest path: {result.algorithm} · PDP solver: {result.solver}</small>{result.routes.map((route) => <div className="route-stat" key={route.driver_id}><div className="route-stat-header"><strong>Driver {route.driver_id}</strong><span>{route.total_distance_km.toFixed(3)} km · {route.stops.length} stops</span></div><div className="stop-sequence">{route.stops.length ? route.stops.map((stop, index) => <div className="stop-sequence-row" key={`${route.driver_id}-${stop.order_id}-${stop.type}-${index}`}><span className="stop-sequence-number">{index + 1}</span><span className={stop.type === 'pickup' ? 'stop-type pickup-text' : 'stop-type dropoff-text'}>{stop.type === 'pickup' ? 'Pickup' : 'Dropoff'} order {stop.order_id}</span><span className="stop-node">{stop.node}</span><span className="stop-distance">+{stop.distance_km.toFixed(3)} km</span></div>) : <span>No assigned stops</span>}</div></div>)}</div>}
      </section>
      <section className="real-map-pdp-view"><div className="map-instruction">Select: {target.type === 'driver' ? `Driver ${target.driverId} start` : `Order ${target.orderId} ${target.type}`}</div><RealMapPDPMap drivers={drivers} orders={orders} routes={result?.routes || []} target={target} onSelect={updateLocation} /></section>
    </main>
  </div>;
}
