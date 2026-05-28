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

**Status: planned**

| Item | Tool / module |
|------|----------------|
| SVG → GIMP raster handoff | HTTP to gimp-mcp `:10773` |
| Blender curve/SVG import staging | fleet HTTP + filesystem drop |
| Unity UI sprite atlas push | unity3d-mcp REST + layer export |
| Fleet pipeline script | `scripts/fleet_pipeline.py` (inkscape → gimp → unity) |

## Phase 4 — Telemetry, Docker, monitoring (2.4.0)

**Status: planned**

| Item | Tool / module |
|------|----------------|
| Prometheus `/metrics` | optional monitoring extra |
| JSON structured logs | Loki-friendly |
| Docker + GHCR image | MCP server container |
| Smoke test script | `scripts/smoke_test.py` |

## Phase 5 — Robotics and fab art (2.5.0)

**Status: planned**

| Item | Tool / module |
|------|----------------|
| DXF / laser path batch | extend `inkscape_vector` + `generate_laser_dot` presets |
| Gazebo schematic overlays | SVG → PNG handoff for model docs |
| Robotics HTTP bridge | `robotics_fab_art` in robotics-mcp calling inkscape over HTTP |
| Fleet E2E smoke | `scripts/fleet_e2e_smoke.py` (inkscape → gimp → robotics probe) |

## After Agent Lab

| Repo | Rationale |
|------|-----------|
| **resonite-mcp** | Social VR asset pipeline; pairs with blender VRM + gimp textures |
| **unity3d-mcp hardening** | VRChat SDK validation, strict fleet E2E in CI |
| **gimp-mcp Phase 6** | PBR map batch, decal UV sheets (parallel track, same fleet) |
