# Inkscape — the SVG editor behind inkscape-mcp

Inkscape is a free, open-source vector graphics editor that uses SVG (Scalable
Vector Graphics) as its native format — a free alternative to Adobe
Illustrator or CorelDRAW, and the actual engine every tool in this MCP server
drives.

## Where it comes from

Inkscape started in 2003 as a fork of [Sodipodi](https://en.wikipedia.org/wiki/Sodipodi)
(itself based on Raph Levien's GNOME illustration app, Gill), begun by four
Sodipodi developers — Bryce Harrington, MenTaLguY, Nathan Hurst, and Ted
Gould — who wanted a redesigned interface and stricter SVG-standard
compliance. It's licensed under the GPL 2.0-or-later, and has been fiscally
sponsored by the [Software Freedom Conservancy](https://sfconservancy.org/)
since 2006 — the nonprofit that handles Inkscape's funds, legal support, and
administrative infrastructure so the project itself stays a volunteer-run,
non-commercial effort rather than a company's product.

## Community and ecosystem

Development happens in the open on [Inkscape's GitLab](https://gitlab.com/inkscape/inkscape),
governed by an elected board and driven by a global volunteer contributor
base — it's a regular participant in Google Summer of Code, ships UI
translations into 100+ languages, and has spawned an ecosystem of its own:
the [Inkscape Extensions](https://inkscape.org/gallery/=extension/) gallery
(Python-based, the same `.inx`/`inkex` layer this MCP server's
`inkscape_system.list_extensions` inspects), community-run tutorials and
forums at inkscape.org, and years of conference talks (LGM — Libre Graphics
Meeting) where its maintainers and the wider FOSS graphics community
(GIMP, Blender, Krita) compare notes.

## What Inkscape can do (beyond what this MCP wraps)

This server drives a large slice of Inkscape headlessly (see Feature
Coverage below), but Inkscape itself is a full interactive editor with a lot
this MCP intentionally doesn't touch:
- Node/bezier path editing, the Pen and Calligraphy tools, and a Spray/Tiled
  Clones system for pattern-based duplication
- Gradient and mesh-gradient editors, a Filter Gallery (blur, glow, texture,
  and other raster-style SVG filter effects), and a pattern editor
- Live Path Effects (LPEs) — non-destructive geometry effects (spiro, power
  stroke, roughen, envelope, and more) that stay editable after applying
- An XML editor for hand-editing the SVG DOM directly, plus an accessible,
  filterable font browser and an SVG font editor
- Text on a path, flowed text in a shape, and a symbols library for reusable
  assets
- Native PDF and EPS import/export (with LaTeX-friendly text extraction),
  bitmap tracing (potrace-based), and raster-to-vector Shape Builder editing
- A full Python extension API for scripting new effects, importers, and
  exporters — the same API this MCP's own tools ultimately build on

## How this MCP server uses it

The MCP server shells out to Inkscape's CLI (`inkscape --actions`) for every
vector operation that needs Inkscape itself (some operations, like SVG
primitive creation, are pure Python and never touch the binary at all — see
[TOOLS.md](TOOLS.md)). If Inkscape is missing or not on PATH, those tools
return "Inkscape not found" warnings.

---

## Quick Install

### Windows

```powershell
# Option A: winget (recommended)
winget install Inkscape.Inkscape

# Option B: Download installer
# https://inkscape.org/release/
```

The installer adds Inkscape to PATH by default. If you installed to a custom path, set `INKSCAPE_PATH`:
```powershell
$env:INKSCAPE_PATH = "C:\Program Files\Inkscape\bin\inkscape.exe"
```

### macOS

```bash
brew install --cask inkscape
```

### Linux

```bash
# Ubuntu / Debian
sudo apt install inkscape

# Fedora
sudo dnf install inkscape

# Arch
sudo pacman -S inkscape

# Flatpak
flatpak install org.inkscape.Inkscape
# NOTE: Flatpak needs special PATH handling — see Troubleshooting below
```

---

## Verify Installation

```bash
inkscape --version
```

Expected output: `Inkscape 1.4.0` (or similar). **1.2+ recommended** for Actions-based automation.

Then verify the MCP server can detect it:
```bash
uv run inkscape-mcp --mode http --port 11028
# Look for: "Inkscape CLI: Available"
```

---

## PATH Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `inkscape: command not found` | Not on PATH | Add install dir to PATH, or set `INKSCAPE_PATH` |
| "Inkscape not found" in webapp | Server environment ≠ your terminal | Set `INKSCAPE_PATH` in `claude_desktop_config.json` `env` block |
| Flatpak: `inkscape` not in PATH | Flatpak binaries not on PATH | Use `flatpak run org.inkscape.Inkscape` or set `INKSCAPE_PATH` to the flatpak wrapper |
| Windows: runs in PowerShell but not in Claude Desktop | Claude Desktop may not inherit user PATH | Use absolute path in `INKSCAPE_PATH` |

To find where Inkscape is installed:

| OS | Command |
|----|---------|
| Windows | `where inkscape` |
| macOS | `which inkscape` |
| Linux | `which inkscape` |

---

## How Inkscape-MCP Uses Inkscape

The MCP server communicates with Inkscape exclusively through its CLI. It NEVER opens the Inkscape GUI automatically. Every tool constructs an `inkscape --actions` command, executes it, and parses the output.

### Actions API (Inkscape 1.2+)

Inkscape 1.2 introduced the `--actions` flag, replacing the older `--verb` system. The MCP server uses `--actions` for all operations:

```
inkscape input.svg --actions="select-all;selection-union;export-filename:output.svg;export-do"
```

Each action is a semicolon-separated command chain:
1. `select-all` — select all objects
2. `selection-union` — boolean union
3. `export-filename:output.svg` — set output path
4. `export-do` — execute export

### Common Actions Used

| Action | Purpose | Used By |
|--------|---------|---------|
| `file-open:PATH` | Open SVG | inkscape_file |
| `file-close` | Close document | inkscape_file |
| `export-filename:PATH` | Set output path | All export tools |
| `export-dpi:N` | Set export DPI | render_preview |
| `export-do` | Execute export | All export tools |
| `select-all` | Select all | Boolean, combine, LPE tools |
| `select-by-id:ID` | Select specific object | path_simplify, inspect, object_raise |
| `select-by-element:TYPE` | Select by element type | text_to_path |
| `selection-union` | Boolean union | apply_boolean |
| `selection-difference` | Boolean difference | apply_boolean |
| `selection-intersection` | Boolean intersection | apply_boolean |
| `selection-exclusion` | Boolean XOR | apply_boolean |
| `selection-simplify:THRESHOLD` | Reduce nodes | path_simplify |
| `selection-raise` | Raise Z-order | object_raise |
| `selection-lower` | Lower Z-order | object_lower |
| `selection-inset:N` | Inset path | path_inset_outset |
| `selection-outset:N` | Outset path | path_inset_outset |
| `object-to-path` | Convert shape to path | object_to_path |
| `path-combine` | Combine paths | path_combine |
| `path-break-apart` | Break compound path | path_break_apart |
| `fit-canvas-to-selection` | Resize canvas | fit_canvas_to_drawing |
| `file-vacuum-defs` | Remove unused defs | optimize_svg |
| `file-cleanup` | Clean document | path_clean |
| `edit-select-all` | Select everything | — |
| `edit-duplicate` | Duplicate selection | — |
| `edit-delete` | Delete selection | — |
| `layer-new` | New layer | (planned) |
| `layer-rename` | Rename layer | (planned) |
| `layer-toggle-visibility` | Toggle layer | (planned) |

### Legacy --verb System

Inkscape 1.0–1.1 used `--verb` instead of `--actions`. The MCP server requires 1.2+ for full functionality but falls back gracefully for basic operations on older versions.

---

## Inkscape Feature Coverage

| Inkscape Feature | MCP Coverage | Notes |
|-----------------|-------------|-------|
| SVG file I/O | ✅ Full | Load, save, convert, export |
| Path operations | ✅ Full | Boolean, simplify, inset/outset, combine, breakapart |
| Object creation | ✅ Full | Rect, circle, star, text, path via SVG generation |
| Layers | ✅ Full | List, create, rename, hide/show, lock, reorder |
| Text | ✅ Full | Content edit, style, fonts, text-to-path |
| LPEs | ✅ Full | 15 LPEs: bend, roughen, spiro, envelope, etc. |
| Animation | ✅ Full | SMIL presets + CSS + element/transform/motion |
| Live GUI control | ✅ Partial | `hands_in_command` via `--active-window` |
| Filters | ❌ Not direct | 100+ SVG filters — use via LPEs or SVG attributes |
| Extensions system | ✅ Partial | List .inx files; execution gated |
| Export formats | ✅ Full | PNG, PDF, EPS, SVG, DXF |

---

## Inkscape 1.2+ vs 1.0–1.1

| Feature | 1.0–1.1 | 1.2+ |
|---------|---------|------|
| Actions API | ❌ (verbs only) | ✅ |
| Streamable HTTP | ❌ | ❌ (not applicable) |
| LPEs via CLI | ❌ | ✅ `org.inkscape.effect.*` |
| `--actions-file` | ❌ | ✅ |
| `--active-window` | ❌ | ✅ |
| `--query-all` | ✅ | ✅ (richer output) |
| `--shell` mode | ✅ | ✅ |

---

## Related Docs

- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — common Inkscape integration issues
- [CONFIGURATION.md](CONFIGURATION.md) — `INKSCAPE_PATH` and other env vars
- [TOOLS.md](TOOLS.md) — all tools that shell out to Inkscape
