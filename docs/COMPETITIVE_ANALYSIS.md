# Competitive Analysis — Inkscape MCP Ecosystem

Last updated: 2026-05-28 (Agent Lab planning)

Compares **sandraschi/inkscape-mcp** (this repo) with other vector/SVG automation and MCP projects.

## Summary

| Project | Scale | Architecture | Standout |
|---------|-------|--------------|----------|
| Inkscape CLI (`--batch-process`, Actions API) | Native | Headless subprocess | Full vector ops, stateful action chains |
| Generic SVG MCP / image servers | Various | HTTP/stdio + libraries | No Inkscape extension depth |
| Manual SVG editors (Figma export, Illustrator) | GUI | Human-driven | Precision, no agent loop |
| **sandraschi/inkscape-mcp** | 4 portmanteau + agentic | FastMCP 3.2 + CLI wrapper | Extension ecosystem, AI SVG, heraldry, fleet webapp |

## Where we lead

- **Portmanteau design** — `inkscape_file`, `inkscape_vector`, `inkscape_analysis`, `inkscape_system` instead of dozens of atomic MCP tools
- **Extension bridge** — `list_extensions` / `execute_extension` for 200+ Inkscape extensions
- **AI SVG construction** — agentic sampling + post-process via Inkscape CLI
- **FastMCP 3.2 SOTA** — prefab UI, structured dialogic returns, HTTP transport
- **Fleet webapp** — `web_sota` dashboard (10899/10900), SVG Studio, actions runner
- **Specialized workflows** — heraldry, DXF/laser paths, layer atlases, VR/Unity pipeline helpers

## Gaps we are closing (roadmap)

See [ROADMAP.md](ROADMAP.md).

| Gap | Our response | Phase |
|-----|--------------|-------|
| Unified agent vision export (PNG/PDF preview for loops) | `inkscape_render` portmanteau + `render_preview` consolidation | 1 (done) |
| Hands-In vs Hands-Off agent guidance | `inkscape_system` → `execution_mode` | 1 (done) |
| Webapp Agent Lab page (mirror blender/gimp/unity) | `/agent-tools` tabs | 2 (done) |
| SVG QA validation presets | `inkscape_validation` portmanteau | 2 (done) |
| Fleet handoff (SVG → gimp raster, blender curves, unity sprites) | `inkscape_fleet` + pipeline script | 3 (done) |
| Prometheus / Docker / smoke test | telemetry + GHCR image | 4 (done) |
| Robotics fab art (DXF, laser dot, Gazebo schematics) | `inkscape_fab_art` + robotics HTTP bridge | 5 (done) |
| UI vector icon packs and sheet layout | `inkscape_sim_art` + `audit_svg_pack` | 6 (done) |

## What we deliberately skip

- **Replacing Inkscape GUI** — agents augment Inkscape CLI, not rebuild a vector editor
- **Cloud-only SVG APIs as primary path** — local-first Inkscape + optional AI gen
- **One tool per Inkscape action** — portmanteau + `execute_extension` escape hatch instead
- **Live TCP bridge (GIMP-style)** — Inkscape has no stable in-process MCP bridge; batch CLI + optional GUI watch is the model

## Architecture comparison

```text
Typical SVG scripts:  shell → inkscape --batch-process → actions chain → files on disk

sandraschi:           MCP client → stdio OR HTTP (:10900)
                              → InkscapeCliWrapper (isolated subprocess per op)
                              → 4 portmanteau tools + agentic + extensions
                              → web_sota (:10899) for fleet visibility
```

## Fleet pipeline role

```text
inkscape-mcp (SVG source)  → gimp-mcp (rasterize, texture QA)  → unity3d-mcp (UI sprites)
inkscape-mcp (DXF/laser) → robotics-mcp (fab paths)          → gazebo-mcp (schematic overlays)
blender-mcp (curve import) ← inkscape-mcp (SVG paths export)
```

## References

- [ROADMAP.md](ROADMAP.md)
- [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- [docs/FEATURES.md](FEATURES.md)
- [gimp-mcp competitive analysis](https://github.com/sandraschi/gimp-mcp/blob/master/docs/COMPETITIVE_ANALYSIS.md)
- [blender-mcp competitive analysis](https://github.com/sandraschi/blender-mcp/blob/main/docs/COMPETITIVE_ANALYSIS.md)
