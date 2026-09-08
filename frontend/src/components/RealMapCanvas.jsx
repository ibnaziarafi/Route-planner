import React from 'react';
import { CircleMarker, MapContainer, Polyline, TileLayer, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

function MapClickHandler({ activeTarget, onSelect }) {
  useMapEvents({
    click(event) {
      onSelect(activeTarget, { lat: event.latlng.lat, lon: event.latlng.lng });
    },
  });
  return null;
}

export default function RealMapCanvas({ start, end, route, activeTarget, onSelect }) {
  const center = start ? [start.lat, start.lon] : [-42.8826, 147.3257];
  const routeCoordinates = route.map((point) => [point.lat, point.lon]);

  return (
    <div className="real-map-canvas">
      <MapContainer center={center} zoom={13} scrollWheelZoom className="real-map-leaflet">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapClickHandler activeTarget={activeTarget} onSelect={onSelect} />
        {start && <CircleMarker center={[start.lat, start.lon]} radius={9} pathOptions={{ color: '#38bdf8', fillColor: '#0ea5e9', fillOpacity: 0.9 }} />}
        {end && <CircleMarker center={[end.lat, end.lon]} radius={9} pathOptions={{ color: '#fb7185', fillColor: '#e11d48', fillOpacity: 0.9 }} />}
        {routeCoordinates.length > 1 && <Polyline positions={routeCoordinates} pathOptions={{ color: '#34d399', weight: 6, opacity: 0.9 }} />}
      </MapContainer>
    </div>
  );
}
