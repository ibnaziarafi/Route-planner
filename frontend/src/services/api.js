const API_BASE_URL = 'http://127.0.0.1:8000';

export async function fetchGraph(graphType = 'small') {
  const response = await fetch(`${API_BASE_URL}/graph?graph_type=${graphType}`);
  if (!response.ok) {
    throw new Error('Failed to fetch graph data from backend server.');
  }
  return await response.json();
}

export async function calculateRoute(start, destination, graphType = 'small') {
  const response = await fetch(`${API_BASE_URL}/route`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ start, destination, graph_type: graphType }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to calculate route.');
  }
  return data;
}

export async function calculateRouteV2(start, destination, graphType = 'small') {
  const response = await fetch(`${API_BASE_URL}/route/v2`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ start, destination, graph_type: graphType }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to calculate route V2.');
  }
  return data;
}

export async function calculateRouteAStar(start, destination, graphType = 'small') {
  const response = await fetch(`${API_BASE_URL}/route/astar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ start, destination, graph_type: graphType }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to calculate A* route.');
  }
  return data;
}

export async function calculateMultiStopRoute(start, stops, destination, graphType = 'small') {
  const response = await fetch(`${API_BASE_URL}/route/multi-stop`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ start, stops, destination, graph_type: graphType }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to calculate multi-stop route.');
  }
  return data;
}

export async function solvePDP(drivers, orders, graphType = 'medium', algorithm = 'scratch', timeLimitSeconds = 5) {
  const response = await fetch(`${API_BASE_URL}/pdp/solve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ graph_type: graphType, algorithm, time_limit_seconds: timeLimitSeconds, drivers, orders }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to optimize pickup and delivery routes.');
  }
  return data;
}
