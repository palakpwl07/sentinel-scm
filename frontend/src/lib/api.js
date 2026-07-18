const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const apiUrl = API_URL;

export async function fetchScenarios() {
  const res = await fetch(`${API_URL}/api/scenarios`);
  if (!res.ok) throw new Error(`Failed to fetch scenarios: ${res.status}`);
  return res.json();
}

export async function fetchDigitalTwinState() {
  const res = await fetch(`${API_URL}/api/digital-twin/state`);
  if (!res.ok) throw new Error(`Failed to fetch digital twin state: ${res.status}`);
  return res.json();
}

export async function triggerScenario(scenarioId, sessionId) {
  const res = await fetch(`${API_URL}/api/scenario/trigger`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario_id: scenarioId, session_id: sessionId }),
  });
  if (!res.ok) throw new Error(`Failed to trigger scenario: ${res.status}`);
  return res.json();
}

export async function submitDecision(sessionId, decision, notes) {
  const res = await fetch(`${API_URL}/api/decision/${sessionId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision, notes: notes || null }),
  });
  if (!res.ok) throw new Error(`Failed to submit decision: ${res.status}`);
  return res.json();
}

export function streamUrl(sessionId) {
  return `${API_URL}/api/scenario/stream/${sessionId}`;
}
