# Publishing Plan — inkscape-mcp v2.6.0

## Target Audiences

| Audience | Where | Hook |
|----------|-------|------|
| Inkscape users | r/Inkscape, Inkscape forum, Discord | "Your AI can now drive Inkscape" |
| MCP/Claude users | r/ClaudeAI, Anthropic Discord, Hacker News | "Full vector graphics through MCP" |
| SVG/creative devs | r/webdev, r/programming, X | "Generate and animate SVGs with AI" |

## Materials to Create

### 1. Screenshots (Playwright automation)

| Page | What to show | Technique |
|------|-------------|-----------|
| Dashboard | Hero card with server stats, 4 KPI cards, tool categories grid | Full-page screenshot via Playwright |
| Animation Studio | Preset gallery + live preview with bouncing circle | Screenshot, then animate via SMIL |
| Layer Manager | SVG loaded with layer list, create/hide/lock UI | Screenshot |
| Agent Lab | Tool cards with operation buttons | Screenshot |
| Status page | Health JSON expande | Screenshot |

Script: `just screenshot-pages` (uses Playwright)

### 2. Animated SVG demo

Generate a showcase SVG with multiple animated elements:

```python
# tools/animation.py operations:
inkscape_animation(operation="apply_preset", preset_name="bounce", fill="#ff4488", duration=2)
inkscape_animation(operation="apply_preset", preset_name="pulse", fill="#4488ff", duration=1.5)
inkscape_animation(operation="apply_preset", preset_name="rotate", fill="#88ff44", duration=3)
```

Combine into a single `demo-animated.svg`. Include in repo and embed in README.

### 3. Promo video (screen recording)

Best tool: **OBS Studio** (free) or **ShareX** (lighter). Record:

| Segment | Duration | Content |
|---------|----------|---------|
| 1. Server start | 5s | Terminal: `just serve` output |
| 2. Dashboard | 10s | Open `http://127.0.0.1:11029`, show hero + KPIs |
| 3. Animation Studio | 15s | Click presets, adjust color/size, show live preview |
| 4. Generate SVG | 10s | Download the animated SVG, open in browser |
| 5. Layer Manager | 10s | Load an SVG, show layer toggles |
| 6. Agent Lab | 10s | Call a tool, show the response |
| 7. Done | 5s | GitHub link, star callout |

Total: ~60s. Post to X, Reddit, and embed in README.

### Alternative to screen recording (no install)

Use **Playwright's video recording** — the `browser_video` MCP tool can record a video of the page without any external software.

### 4. GitHub Preview image

Generate a 1280×640 social preview (`social-preview.svg` or `social-preview.png`):
- Left: Animated SVG demo (bouncing circles)
- Right: Terminal output + "Inkscape MCP" logo
- Bottom: Badge strip (FastMCP, Tauri, NSIS, Python)

## Publishing Sequence

| Day | Channel | Post |
|-----|---------|------|
| 0 | GitHub | Update repo description, topics, social preview |
| 0 | README | Add screenshots section, link to animated demo |
| 1 | r/Inkscape | "My AI can now create animated SVGs with Inkscape" — show animation studio |
| 1 | r/ClaudeAI | "I built an MCP server that gives Claude full Inkscape control" |
| 2 | Hacker News | "Show HN: Inkscape MCP — AI-powered vector graphics server" |
| 3 | X/Twitter | GIF of animation studio + "27 → 50 stars challenge" |
| 3 | Inkscape forum | "New: MCP integration for AI-assisted SVG workflows" |

## Key Messages

- "AI can now create, edit, layer, animate, and export SVG files using Inkscape"
- "One installer: MCP server + webapp dashboard + Windows desktop app"
- "60+ operations: from layer management to SMIL animation to LPE effects"
- "Free, open-source, MIT license"
