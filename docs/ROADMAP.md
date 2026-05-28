# Improvement Roadmap

Phased plan derived from [COMPETITIVE_ANALYSIS.md](COMPETITIVE_ANALYSIS.md).
Mirrors the blender-mcp / gimp-mcp / unity3d-mcp Agent Lab phases, adapted for Inkscape CLI + batch workflows.

**Current baseline:** v2.0.0b0 — four portmanteau tools, agentic SVG, `web_sota` dashboard, extension bridge.

## Phase 1 — Agent vision and runtime guidance (2.1.0)

**Status: complete (v2.1.0)**

| Item | Tool / module |
|------|----------------|
| Unified preview export for agent loops | `inkscape_render` → `export_preview`, `export_multi_dpi` |
| Document summary for vision context | `inkscape_render` → `get_document_summary` |
| Hands-In vs Hands-Off guidance | `inkscape_system` → `execution_mode` |
| Inkscape detection + CLI health | `inkscape_system` → `status`, `diagnostics` |
| Phase 1 tests | `tests/unit/test_phase1_tools.py` |

### Agent workflow

```powershell
# HTTP MCP (webapp / IDE)
cd D:\Dev\repos\inkscape-mcp\web_sota
.\start.ps1

# Agent:
# inkscape_system operation=status
# inkscape_system operation=execution_mode
# inkscape_render operation=export_preview input_path=D:/Temp/diagram.svg output_path=D:/Temp/review.png
```

## Phase 2 — Webapp Agent Lab and validation (2.2.0)

**Status: complete (v2.2.0)**

| Item | Tool / module |
|------|----------------|
| Webapp `/agent-tools` page | mirror blender-mcp / gimp-mcp tabbed UI |
| `POST /api/v1/tool` proxy | `app.py` REST bridge |
| SVG QA validation portmanteau | `inkscape_validation` (viewBox, stroke/fill, size limits) |
| Export preview history | web_sota gallery tab (localStorage) |

## Phase 3 — Fleet handoff (2.3.0)

**Status: complete (v2.3.0)**

| Item | Tool / module |
|------|----------------|
| SVG → GIMP raster handoff | `inkscape_fleet` → `push_gimp_raster` + HTTP :10773 |
| Blender curve/SVG import staging | `inkscape_fleet` → `stage_blender_svg` |
| Unity UI sprite atlas push | `inkscape_fleet` → `push_unity_sprite`, `build_layer_atlas` |
| Fleet pipeline script | `scripts/fleet_pipeline.py`, `scripts/run-fleet-pipeline.ps1` |

## Phase 4 — Telemetry, Docker, monitoring (2.4.0)

**Status: complete (v2.4.0)**

| Item | Tool / module |
|------|----------------|
| Prometheus `/metrics` + `/api/metrics` | `utils/telemetry.py`, optional `[monitoring]` extra |
| JSON structured logs | `utils/structured_logging.py`, `INKSCAPE_MCP_LOG_FORMAT=json` |
| Docker + GHCR image | `Dockerfile`, `docker-compose.yml`, `.github/workflows/docker-publish.yml` |
| Grafana/Loki/Promtail stack | `monitoring/` (profile `monitoring`) |
| Smoke test script | `scripts/smoke_test.py` |
| Phase 4 tests | `tests/unit/test_phase4_tools.py` |

### Docker quick start

```powershell
cd D:\Dev\repos\inkscape-mcp
docker compose up inkscape-mcp

# With monitoring (Prometheus :9092, Grafana :3002, Loki :3102):
docker compose --profile monitoring up -d
```

## Phase 5 — Robotics and fab art (2.5.0)

**Status: complete (v2.5.0)**

| Item | Tool / module |
|------|----------------|
| DXF / laser path batch | `inkscape_fab_art` → `batch_dxf_export`, `batch_laser_dots` + `export_dxf` |
| Gazebo schematic overlays | `inkscape_fab_art` → `gazebo_schematic` (SVG → PNG + staging) |
| Robotics HTTP bridge | `robotics_fab_art` in robotics-mcp → inkscape HTTP :10900 |
| Fleet E2E smoke | `scripts/fleet_e2e_smoke.py --offline --strict` |
| Phase 5 tests | `tests/unit/test_phase5_tools.py` |

### CI offline smoke

```powershell
cd D:\Dev\repos\inkscape-mcp
$Env:PYTHONPATH = "src"
uv run python scripts/fleet_e2e_smoke.py --offline --strict
```

## Phase 6 — UI vector packs and SVG refine loop (2.6.0)

**Status: complete (v2.6.0)**

| Item | Tool / module |
|------|----------------|
| SVG icon pack batch | `inkscape_sim_art` → `svg_pack_batch` + icon templates |
| Icon sheet layout (margin/bleed) | `inkscape_sim_art` → `build_icon_sheet` + manifest JSON |
| SVG pack audit | `inkscape_validation` → `audit_svg_pack` |
| AI SVG refine loop | `inkscape_sim_art` → `ai_svg_refine_loop` + Ollama/OpenAI handoff |
| Resonite UI staging | `inkscape_sim_art` → `stage_resonite_ui` |
| Fleet E2E smoke in CI | extended `scripts/fleet_e2e_smoke.py --offline --strict` |
| Phase 6 tests | `tests/unit/test_phase6_tools.py` |

## After Agent Lab

| Repo | Rationale |
|------|-----------|
| **resonite-mcp** | Social VR asset pipeline; pairs with blender VRM + gimp textures |
| **unity3d-mcp hardening** | VRChat SDK validation, strict fleet E2E in CI |
| **gimp-mcp Phase 6** | PBR map batch, decal UV sheets (parallel track, same fleet) |
