# Amped Up

Field operations dashboard for utility pole inspection and risk tracking. Field technicians submit reports with drone photos; the backend scores poles by severity and broadcasts live updates to all connected dashboards via WebSocket.

## Stack

- **Backend** — Python 3.11+ · FastAPI · Pydantic · Uvicorn
- **Frontend** — React 19 · TypeScript · Vite

## Running Locally

### 1. Install backend dependencies

```bash
pip3 install -r backend/requirements.txt
```

### 2. Start the backend

Run from the **project root** (the backend uses relative imports and must be launched as a package):

```bash
npm run backend
# equivalent: python3 -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### 3. Start the frontend

In a separate terminal:

```bash
npm install
npm run dev
```

Open the Vite URL shown in the terminal (default: `http://127.0.0.1:5173`).

---

## API Reference

### Risk profiler (original)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/summary` | Portfolio-level risk and data-quality totals |
| `GET` | `/api/poles` | Pole risk profiles — filter by `circuit`, `band`, `driver`, `min_score` |
| `GET` | `/api/poles/{pole_id}` | Single pole with factor-level explanations |
| `GET` | `/api/circuits` | Circuit segment risk rollups — filter by `circuit`, `band`, `min_score` |

### Dashboard

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/dashboard` | Full dashboard state (summary KPIs, open reports, map poles, selected pole detail, field photos, pole history). Pass `?selected_report_id=RPT-xxxx` to pre-select a report. |
| `POST` | `/api/dashboard/reports/{report_id}/notes` | Add a note to a report. Body: `{ "content": "string" }`. Broadcasts a `note_added` event to all WebSocket clients. |
| `PATCH` | `/api/dashboard/reports/{report_id}/status` | Update report status. Body: `{ "status": "open" \| "snoozed" \| "approved" \| "dismissed" }`. Broadcasts `report_status_changed` and `kpi_update` events. |
| `GET` | `/api/dashboard/reports/{report_id}/notes` | List notes for a report. |
| `WS` | `/api/dashboard/ws` | WebSocket connection for live updates. Send `{ "type": "ping" }` to keep the connection alive. |

### WebSocket events

Events are JSON objects broadcast to all connected clients when data changes:

| Event | Payload | Trigger |
|-------|---------|---------|
| `connected` | Summary KPI snapshot | On connection open |
| `kpi_update` | Updated summary KPIs | Report status changes |
| `note_added` | `{ report_id, note }` | New note posted |
| `report_status_changed` | `{ report_id, status }` | Report approved / dismissed / snoozed |
| `pong` | _(none)_ | Response to client ping |

---

## npm Scripts

| Script | Command |
|--------|---------|
| `npm run dev` | Start Vite dev server at `127.0.0.1:5173` |
| `npm run backend` | Start FastAPI at `127.0.0.1:8000` with hot reload |
| `npm run build` | Production build to `dist/` |
| `npm run preview` | Preview production build |
