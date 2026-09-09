const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export async function solveRealMapPDP(payload) {
  const response = await fetch(`${API_BASE_URL}/api/real-map-pdp/solve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Unable to optimize real-map delivery routes.');
  return data;
}
