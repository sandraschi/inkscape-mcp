# Depot + Demo Workflows — Implementation Plan

Spec locked via AskUserQuestion (2026-09-27):
- CRUD entity: **both** — workflow definitions (editable step sequences) and the SVG/PNG
  assets each run produces, linked by `workflow_id`.
- Storage: **SQLite** for metadata (stdlib `sqlite3`, no new dependency), files on disk
  under `~/.config/inkscape-mcp/depot/assets/` (matches the existing config dir
  convention in `config.py::load_config`).
- UI: **editable workflow builder** — steps are visible and editable (tool, operation,
  raw JSON params) before running, not just a fixed preset gallery.

## Data model (SQLite, `~/.config/inkscape-mcp/depot/depot.db`)

```sql
CREATE TABLE workflows (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT DEFAULT '',
  steps TEXT NOT NULL,        -- JSON array of {tool, operation, params}
  is_builtin INTEGER DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE assets (
  id TEXT PRIMARY KEY,
  workflow_id TEXT,           -- nullable, FK -> workflows.id
  name TEXT NOT NULL,
  file_path TEXT NOT NULL,
  thumbnail_path TEXT,
  tags TEXT DEFAULT '',       -- comma-separated
  created_at TEXT NOT NULL
);
```

No `runs` table for v1 — a run's only durable output is the asset row it creates.

## Backend

- `services/depot_store.py` — schema init + CRUD functions (`list_workflows`,
  `get_workflow`, `create_workflow`, `update_workflow`, `delete_workflow` [blocked for
  `is_builtin`], same set for assets), plus `seed_builtins()` called once at init.
- `services/depot_routes.py` — `register_depot_routes(router, mcp)`:
  - `GET/POST /api/depot/workflows`, `GET/PUT/DELETE /api/depot/workflows/{id}`
  - `POST /api/depot/workflows/{id}/run` — executes `steps` in order via the existing
    `_call_mcp_tool(mcp, tool, params)` helper in `app.py` (already the single place
    that normalizes FastMCP's ToolResult - reused, not reimplemented), writes the
    resulting SVG (and a rendered PNG thumbnail via `inkscape_render.export_preview`)
    into the assets dir, inserts an `assets` row, returns the asset.
  - `GET/PATCH/DELETE /api/depot/assets`, `/api/depot/assets/{id}`
- Wire into `register_rest_api` in `app.py` the same way `apps_routes.py` is wired
  (one `APIRouter(prefix="/api")` + `include_router`).
- Seed 3 builtin workflows mirroring the README's own example prompts - now actually
  runnable end-to-end because `inkscape_layers`/`inkscape_animation` registration and
  `inkscape_vector`'s full parameter surface were fixed in this same session:
  1. "Bouncing circle" - `inkscape_vector.create_object` (circle) -> `inkscape_animation.apply_preset` (bounce)
  2. "Layer rename + hide" - `inkscape_layers.create` -> `rename` -> `hide`
  3. "Text to roughened path" - `inkscape_vector.create_object` (text) -> `text_to_path` -> `apply_lpe` (roughen)

## Frontend (`web_sota`)

- `src/api/depot.ts` — typed client (`apiGet`/`apiPost`/new `apiPut`/`apiPatch` in
  `api/client.ts`) for the routes above.
- `src/pages/depot.tsx` — two tabs:
  - **Workflows**: list + step builder (tool/operation selects, raw JSON textarea per
    step - a fully dynamic per-operation form is out of scope for v1 given `inkscape_vector`
    alone has 27 params; JSON is the pragmatic v1 editor), Run button, "Save as new" to
    fork a builtin.
  - **Assets**: gallery grid (thumbnail, name, tags, source workflow link, delete).
- Add `/depot` route in `App.tsx` and a nav entry in `sidebar.tsx`.

## Explicitly out of scope for v1 (say so, don't build)

- Per-operation dynamic param forms (JSON textarea instead).
- A `runs` history table.
- Multi-user/auth on the depot (single local user, same trust model as the rest of
  this webapp).
