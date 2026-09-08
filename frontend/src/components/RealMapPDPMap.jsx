import React from 'react';
import { CircleMarker, MapContainer, Polyline, TileLayer, Tooltip, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

function MapClickHandler({ target, onSelect }) {
  useMapEvents({ click: (event) => onSelect(target, { lat: event.latlng.lat, lon: event.latlng.lng }) });
  return null;
}

export default function RealMapPDPMap({ drivers, orders, routes, target, onSelect }) {
  const center = [-42.8826, 147.3257];
  return (
    <div className="real-map-pdp-map">
      <MapContainer center={center} zoom={13} scrollWheelZoom className="real-map-leaflet">
        <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <MapClickHandler target={target} onSelect={onSelect} />
        {drivers.map((driver) => driver.start_lat && <CircleMarker key={`driver-${driver.driver_id}`} center={[driver.start_lat, driver.start_lon]} radius={9} pathOptions={{ color: '#38bdf8', fillColor: '#0284c7', fillOpacity: 0.95 }}><Tooltip>Driver {driver.driver_id} start</Tooltip></CircleMarker>)}
        {orders.map((order) => <React.Fragment key={`order-${order.order_id}`}><CircleMarker center={[order.pickup_lat, order.pickup_lon]} radius={7} pathOptions={{ color: '#fbbf24', fillColor: '#d97706', fillOpacity: 0.95 }}><Tooltip>Order {order.order_id} pickup</Tooltip></CircleMarker><CircleMarker center={[order.dropoff_lat, order.dropoff_lon]} radius={7} pathOptions={{ color: '#fb7185', fillColor: '#e11d48', fillOpacity: 0.95 }}><Tooltip>Order {order.order_id} dropoff</Tooltip></CircleMarker></React.Fragment>)}
        {routes.map((route) => <Polyline key={`route-${route.driver_id}`} positions={route.full_path.map((point) => [point.lat, point.lon])} pathOptions={{ color: ['#34d399', '#a78bfa', '#f97316', '#22d3ee'][route.driver_id % 4], weight: 5, opacity: 0.82 }} />)}
      </MapContainer>
    </div>
  );
}
