const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const errorDetail = detail => Array.isArray(detail) ? detail.map(item => `${(item.loc || []).filter(x=>x!=='body').join('.')}: ${item.msg || 'Invalid value'}`).join('; ') : typeof detail === 'string' ? detail : detail ? JSON.stringify(detail) : ''; 

async function getJson(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);
  const data = await response.json();
  if (!response.ok) throw new Error(errorDetail(data.detail) || `Request failed (${response.status})`);
  return data;
}

export const fetchBenchmarkModel = () => getJson('/api/benchmarks/model');
export const fetchBenchmarkReport = () => getJson('/api/benchmarks/report');
export const comparePaths = ({ graphType, repeats }) => getJson(`/api/benchmarks/paths?graph_type=${encodeURIComponent(graphType)}&repeats=${encodeURIComponent(repeats)}`);

export async function compareBenchmarks(request) {
  const response = await fetch(`${API_BASE_URL}/api/benchmarks/compare`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(request),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(errorDetail(data.detail) || `Comparison failed (${response.status})`);
  return data;
}
