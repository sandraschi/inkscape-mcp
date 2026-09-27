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
(Python-based, on the `.inx`/`inkex` plugin API — `inkscape_system` has real
integration with it: `search_extensions` queries the live gallery,
`install_extension` downloads and installs a result (verified/reviewed
packages only, by default), `uninstall_extension` and
`list_managed_extensions` round it out. `list_extensions` separately scans
for `.inx` files already installed locally, and `execute_extension` -
actually *running* an installed extension from here - is currently a stub
that always returns "disabled", regardless of which extension you ask for),
community-run tutorials and forums at inkscape.org,
and years of conference talks (LGM — Libre Graphics
Meeting) where its maintainers and the wider FOSS graphics community
(GIMP, Blender, Krita) compare notes.

## What Inkscape can do — and how much of it this MCP now reaches

Inkscape is a full interactive editor; a one-shot CLI/MCP call can't replicate
everything a mouse-and-dialog workflow can. Most of the list below is now
directly reachable through `inkscape_vector`/`inkscape_system` as pure SVG
DOM edits (no Inkscape process needed for these - they write the same
`<linearGradient>`, `<pattern>`, `<textPath>`, `shape-inside`, and `<symbol>`
markup Inkscape's own GUI produces, verified by rendering the result through
the real Inkscape binary):

- **Gradients and patterns** — `create_gradient` (linear/radial, arbitrary
  stops) and `create_pattern` (tiling, from raw SVG tile content) each return
  a ready `fill` value. Mesh gradients specifically: `create_mesh_gradient`.
- **Filter Gallery equivalents** — `apply_filter` (blur, drop_shadow, glow).
- **Live Path Effects (LPEs)** — `list_lpes` / `apply_lpe`: spiro, power
  stroke, roughen, envelope, bend, and more, non-destructively.
- **XML editor equivalent** — `get_attributes` / `set_attributes`: read or
  write any attribute (or `style.<prop>`) on any element by id.
- **Text on a path** and **flowed text in a shape** — `text_on_path`
  (`<textPath>`) and `flow_text` (CSS `shape-inside`, the same mechanism
  Inkscape's own "Flow into frame" produces).
- **Symbols library** — `create_symbol` / `use_symbol` (`<symbol>`/`<use>`).
- **PDF/EPS import-export** (`inkscape_file.convert`) and **bitmap tracing**
  (`trace_image`, potrace-based) were already covered.

Genuinely not implemented, and not planned as one-shot operations because
they're inherently interactive with no meaningful static equivalent:
- **Node/bezier path editing** and the **Pen tool** — live, click-by-click
  point manipulation; `apply_lpe`/`path_simplify`/boolean ops cover the
  non-interactive geometry transforms that would otherwise need this.
- **Calligraphy tool** and **Spray/Tiled Clones** — pressure/stroke-dynamics
  and live click-to-place duplication; there's no fixed "correct" one-shot
  output to generate.
- **Shape Builder** — a live click-to-combine-or-erase tool; the same result
  is reachable non-interactively via `apply_boolean`.
- **Font browser / SVG font editor** — SVG fonts are a largely-deprecated
  legacy format; `text_list_fonts` already covers listing installed system
  fonts for `text_set_style`/`create_object`.
- **Python extension *authoring* API** — writing new Inkscape extensions is
  a different job from this MCP's (see the extension *gallery* integration
  above, which is about using existing extensions, not writing new ones).

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
| Filters | ✅ Partial | `apply_filter`: blur, drop_shadow, glow (not the full 100+ built-in gallery) |
| Gradients / patterns | ✅ Full | `create_gradient` (linear/radial), `create_mesh_gradient`, `create_pattern` |
| XML editing | ✅ Full | `get_attributes` / `set_attributes` by element id |
| Text on path / flowed text | ✅ Full | `text_on_path`, `flow_text` |
| Symbols | ✅ Full | `create_symbol` / `use_symbol` |
| Extensions (local) | ✅ Partial | List .inx files; execution gated (see extension gallery below for install) |
| Extension gallery | ✅ Full | `search_extensions` / `install_extension` / `uninstall_extension` |
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
