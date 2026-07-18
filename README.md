# SupplyChainAI Control Tower

Five specialised AI agents collaborate, negotiate, and produce explainable supply chain
risk recommendations with traceable evidence chains for **Orbital Manufacturing Pte Ltd**
(Singapore) during the March 2026 Middle East crisis — the first simultaneous Strait of
Hormuz closure and Red Sea blockade in modern history.

Built for the Global AI Hackathon Series, Track 3: **Agent Society**.

## Architecture

- **LangGraph** orchestrates six nodes: Monitoring → Risk → Planning → Finance →
  (Negotiation loop) → Operations Manager, with a human-in-the-loop interrupt
  (`interrupt_before=["ops_manager"]`) before the final recommendation is published.
- **Qwen** (qwen-plus/qwen-max) powers every agent via the OpenAI-compatible client
  pointed at `QWEN_BASE_URL` (DashScope compatible mode).
- **MCP server** (`backend/mcp_server/server.py`, fastmcp) exposes the Neo4j digital twin
  as four tools: `assess_supplier_risk`, `find_alternative_suppliers`,
  `calculate_inventory_runway`, `evaluate_mitigation_cost`.
- **Neo4j AuraDB** holds the digital twin: 1 company, 6 materials, 24 suppliers,
  16 ports, 13 shipping routes, 14 regions, 5 disruption events.
- **FastAPI + SSE** streams each agent's output live to the frontend.
- **React + Cytoscape.js + Tailwind** renders the supply network, agent trace,
  evidence chain, inventory runway bars, and the HITL approval modal.

## Quick start

### 1. Configure environment

```bash
cp backend/.env.example backend/.env
# fill in NEO4J_URI / NEO4J_PASSWORD (AuraDB Free) and QWEN_API_KEY
```

### 2. Seed the digital twin (once, idempotent — MERGE only)

```bash
cd backend
pip install -r requirements.txt
python -m database.seed
```

### 3. Run with Docker

```bash
docker-compose up --build
# frontend: http://localhost:3000   backend: http://localhost:8000
```

### 3b. Or run locally

```bash
# terminal 1 — backend
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000

# terminal 2 — MCP server (optional, tools also run in-process)
cd backend && python -m mcp_server.server

# terminal 3 — frontend
cd frontend && npm install && npm start
```

### 4. Demo flow

1. Open the UI, pick a scenario (e.g. **March 2026 Middle East Crisis — Full Impact**).
2. Watch the agent trace stream: Monitoring detects events → Risk scores suppliers and
   inventory runways → Planning proposes mitigations → Finance evaluates costs →
   rejected strategies trigger a Planning↔Finance negotiation round → the Operations
   Manager arbitrates with a weighted score and drafts the final recommendation.
3. The HITL modal opens with the full evidence chain — approve or reject.
4. The Cytoscape digital twin re-colours disrupted suppliers, ports, and routes.

## API

| Endpoint | Description |
|---|---|
| `POST /api/scenario/trigger` | Start a scenario run (`{scenario_id, session_id}`) |
| `GET /api/scenario/stream/{session_id}` | SSE stream of agent messages, `hitl_required`, `complete` |
| `GET /api/digital-twin/state` | Full graph state for the Cytoscape view |
| `POST /api/decision/{session_id}` | Approve/reject the recommendation (resumes the graph) |
| `GET /api/scenarios` | List canned scenarios |

## Evaluation

```bash
python eval/run_eval.py
```

Runs the Risk Agent's tools against `eval/synthetic_events.json` ground truth and
reports precision/recall for unavailable suppliers, critical suppliers, and materials
at stockout risk across all three scenarios.

## Project layout

See the build spec (Section 3) — `backend/` (FastAPI, agents, MCP server, Neo4j seed),
`frontend/` (React dual-panel control tower), `eval/` (ground-truth harness),
`docker-compose.yml` (backend + frontend for Alibaba Cloud ECS deployment).
