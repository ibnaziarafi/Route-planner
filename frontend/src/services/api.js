const API_BASE_URL = 'http://127.0.0.1:8000';

export async function fetchGraph() {
  const response = await fetch(`${API_BASE_URL}/graph`);
  if (!response.ok) {
    throw new Error('Failed to fetch graph data from backend server.');
  }
  return await response.json();
}

export async function calculateRoute(start, destination) {
  const response = await fetch(`${API_BASE_URL}/route`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ start, destination }),
  });
  
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to calculate route.');
  }
  return data;
}

export async function calculateMultiStopRoute(start, stops, destination) {
  const response = await fetch(`${API_BASE_URL}/route/multi-stop`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ start, stops, destination }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to calculate multi-stop route.');
  }
  return data;
}
