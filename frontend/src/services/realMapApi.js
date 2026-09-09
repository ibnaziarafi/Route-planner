const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export async function calculateRealMapRoute({ start, end, algorithm }) {
  const response = await fetch(`${API_BASE_URL}/api/real-map/route`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      start_lat: start.lat,
      start_lon: start.lon,
      end_lat: end.lat,
      end_lon: end.lon,
      algorithm,
    }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Unable to calculate the real road route.');
  }
  return data;
}
