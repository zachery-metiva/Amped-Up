# Amped Up

Field operations dashboard for utility pole inspection and risk tracking. Field technicians submit reports with drone photos; the backend scores poles by severity and broadcasts live updates to all connected dashboards via WebSocket.

## Stack

- **Backend** — Python 3.11+ · FastAPI · Pydantic · Uvicorn
- **Frontend** — React 19 · TypeScript · Vite

## Running Locally

### 1. Install backend dependencies

```bash
python -m pip install -r backend/requirements.txt
```

### 2. Configure Supabase Postgres

Create a Supabase project, then open **Project Settings > Database > Connection string**.
Copy the URI connection string and put it in a local `.env` file:

```env
DATABASE_URL=postgresql://postgres.your-project-ref:your-password@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require
```

The app accepts Supabase URLs that start with `postgresql://` or `postgres://` and automatically uses the installed `psycopg` driver.

Then create the schema and seed the dashboard data:

```bash
npm run db:upgrade
npm run db:seed:violations
npm run db:seed
```

If `DATABASE_URL` is not set, the backend falls back to a local `amped_up_dev.db` SQLite database for quick development only.

### 3. Start the backend

Run from the **project root** (the backend uses relative imports and must be launched as a package):

```bash
npm run backend
# equivalent: python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### Seed DTE OSM pole inventory

The dashboard seed task imports `dte_osm_poles.csv` from the project root and falls back to `dte_osm_poles.geojson` if the CSV is unavailable:

```bash
python -m backend.seed_dashboard_data
```

The original GeoJSON is also available from the backend at `/api/dashboard/osm-poles.geojson`.

Seeded mock records use Detroit neighborhoods and corridors such as Downtown, Corktown, Midtown, Eastern Market, Mexicantown, New Center, Rivertown, Boston-Edison, Southwest Detroit, and East English Village. Imported OSM pole nodes are labeled with the nearest Detroit area and DTE-style feeder name.

### Build inspection training data

The SVG exemplar library can be exported into model-ready JSONL records for IBM/watsonx adaptation or evaluation:

```bash
python scripts/export_inspection_training_data.py
```

This writes `dataset/inspection_training/inspection_records.jsonl`, `ibm_messages.jsonl`, and `dashboard_contracts.jsonl`. Each record maps the SVG/preview image to pole specifications, defect labels, regulatory references, dashboard severity, violation type, evidence requirements, and recommended action.

### 4. Start the frontend

In a separate terminal:

```bash
npm install
npm run dev
```

Open the Vite URL shown in the terminal (default: `http://127.0.0.1:5173`).

---

## Deployment

### Frontend: GitHub Pages

The workflow at `.github/workflows/deploy-frontend.yml` builds the Vite app and publishes `dist/` to GitHub Pages.

Production domain:

```text
https://amped-up.online
```

The Vite build includes `public/CNAME`, so the Pages artifact contains the custom domain. In the GitHub repository, add this secret before running the workflow:

```env
VITE_API_BASE_URL=https://your-render-service.onrender.com
```

Then open **Settings > Pages**, set the source to **GitHub Actions**, set the custom domain to `amped-up.online`, and enable **Enforce HTTPS** once GitHub allows it.

Configure the domain DNS for GitHub Pages:

```text
A     @    185.199.108.153
A     @    185.199.109.153
A     @    185.199.110.153
A     @    185.199.111.153
AAAA  @    2606:50c0:8000::153
AAAA  @    2606:50c0:8001::153
AAAA  @    2606:50c0:8002::153
AAAA  @    2606:50c0:8003::153
CNAME www  CarlSciz.github.io
```

Do not include the repository name in the `www` CNAME target.

### Backend: Render Free Web Service

Render can use `render.yaml` from the repository root. Create a new Blueprint/Web Service from the repo, then set these environment variables in Render:

```env
DATABASE_URL=postgresql://your-neon-pooled-connection-string?sslmode=require
FRONTEND_ORIGINS=https://amped-up.online,https://www.amped-up.online
WATSONX_API_KEY=...
WATSONX_PROJECT_ID=...
WATSONX_URL=https://us-south.ml.cloud.ibm.com
```

Render runs Alembic migrations before starting FastAPI:

```bash
python -m alembic upgrade head && python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Use Neon's pooled connection string for `DATABASE_URL`; the local SQLite fallback is only for development.

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
| `POST` | `/api/dashboard/reports` | Submit a new field report. See [Field report submission](#field-report-submission) below. |
| `POST` | `/api/dashboard/reports/{report_id}/notes` | Add a note to a report. Body: `{ "content": "string" }`. Broadcasts a `note_added` event to all WebSocket clients. |
| `PATCH` | `/api/dashboard/reports/{report_id}/status` | Update report status. Body: `{ "status": "open" \| "snoozed" \| "approved" \| "dismissed" }`. Broadcasts `report_status_changed` and `kpi_update` events. |
| `GET` | `/api/dashboard/reports/{report_id}/notes` | List notes for a report. |
| `WS` | `/api/dashboard/ws` | WebSocket connection for live updates. Send `{ "type": "ping" }` to keep the connection alive. |

### WebSocket events

Events are JSON objects broadcast to all connected clients when data changes:

| Event | Payload | Trigger |
|-------|---------|---------|
| `connected` | Summary KPI snapshot | On connection open |
| `kpi_update` | Updated summary KPIs | Report status changes or new report submitted |
| `note_added` | `{ report_id, note }` | New note posted |
| `report_added` | Full report object | New field report submitted via capture page |
| `report_status_changed` | `{ report_id, status }` | Report approved / dismissed / snoozed |
| `pong` | _(none)_ | Response to client ping |

---

## Field report submission

Field technicians capture and submit reports through a mobile-optimised two-step flow.

### Capture page URL

```
http://127.0.0.1:5173/report
http://127.0.0.1:5173/report?pole=P-1147
```

Pass `?pole=<pole_id>` to pre-fill the pole ID. Any path beginning with `/report` loads the submission flow.

### Steps

| Step | Screen | Description |
|------|--------|-------------|
| 1 | Capture | Live camera viewfinder, GPS lock indicator, three labelled photo slots (Overview · Damage · Base of pole). Tap the shutter to fill each slot in order. |
| 2 | Review | Thumbnails of all three photos, GPS coordinates card, optional free-text description. Tap **Submit report** to POST to the backend. |

Severity is **not** selectable by field technicians — it is assigned by ops staff on the dashboard after review.

### Submit endpoint

`POST /api/dashboard/reports`

Request body:

```json
{
  "pole_id": "P-1147",
  "location": { "lat": 47.6062, "lon": -122.3321, "accuracy": 4.2 },
  "description": "Crossarm showing visible rot, leaning approx 15°",
  "photo_count": 3
}
```

`location` may be `null` if GPS was unavailable. On success the server returns `201 Created` with the full report object and broadcasts `report_added` + `kpi_update` to all connected dashboard WebSocket clients.

---

## npm Scripts

| Script | Command |
|--------|---------|
| `npm run dev` | Start Vite dev server at `127.0.0.1:5173` |
| `npm run backend` | Start FastAPI at `127.0.0.1:8000` with hot reload |
| `npm run db:upgrade` | Apply Alembic migrations to `DATABASE_URL` |
| `npm run db:seed:violations` | Seed NESC violation type metadata |
| `npm run db:seed` | Seed dashboard users, Detroit poles, reports, photos, and history |
| `npm run build` | Production build to `dist/` |
| `npm run preview` | Preview production build |
