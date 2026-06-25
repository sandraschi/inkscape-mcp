# Inkscape — the SVG editor behind inkscape-mcp

Inkscape is a free, open-source vector graphics editor. It uses SVG (Scalable Vector Graphics) as its native format. Think of it as a free alternative to Adobe Illustrator or CorelDRAW.

The MCP server shells out to Inkscape's CLI (`inkscape --actions`) for every vector operation. If Inkscape is missing or not on PATH, most tools return "Inkscape not found" warnings.

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
