# AI IDE Development (Cursor)

**Confidence**: 🟢 High
**Last validated**: 2025-11-11
**Primary sources**: Cursor documentation on rules and MCP configuration (docs.cursor.com), community onboarding guides (agency-swarm.ai), internal bootstrap scripts

---

## 1. Why AI IDE Integration Matters

- Cursor IDE runs the MCP server alongside an AI pair-programmer, so a polished setup shortens feedback loops.
- `.cursorrules` lets us inject project-specific standards (FastMCP 2.13+, portmanteau discipline) directly into the IDE.
- Providing ready-to-use MCP configs and install commands removes user friction and boosts adoption.

---

## 2. Cursor MCP Configuration

| Step | Action | Notes |
| --- | --- | --- |
| 1 | Ensure the server is installed/bootstrapped (`pip`, `uv`, or `npx` script). | `npx --yes github:sandraschi/advanced-memory-mcp/scripts/bootstrap/windows -- --generate-configs` emits ready configs. |
| 2 | Create/Update `.cursor/mcp.json`. | Typical path: project root. Cursor merges with user-level config. |
| 3 | Register server entry: | ```json<br>{
  "servers": [
    {
      "name": "advanced-memory",
      "command": "uv",
      "args": ["run", "python", "-m", "advanced_memory.mcp.server"]
    }
  ]
}
``` |
| 4 | Restart Cursor or reload MCP connections. | Use Command Palette → “Reload MCP Servers” if available. |
| 5 | Test via Composer (`Ctrl/Cmd+L`), calling exposed tools (e.g., `adn_content`, `adn_skills_creator`). | Confirm structured JSON responses and helpful error suggestions. |

Keep configs versioned when possible; avoid secrets in repo (use `$ENV` placeholders).

---

## 3. `.cursorrules` Alignment

- Place `.cursorrules` at repo root (tracked) plus optional user rules for personal preferences.
- Reference this skill’s guidance:
  - Portmanteau expectations (`modules/tooling-strategy.md`).
  - Release gates and ruff/pytest cadence (`modules/development-workflow.md`, `modules/release-readiness.md`).
- Encourage IDE users to run `Show Rules` in Cursor to verify the file loaded.
- Update `.cursorrules` whenever standards change (FastMCP version bump, new test suites).

---

## 4. Workflow Tips inside Cursor

- Use Composer (`Ctrl/Cmd+I`) to stage multi-step plans (e.g., “Refactor adn_content operations”).
- Anchor conversations with `@files` and `@rules` to keep AI responses grounded.
- Leverage Agent Mode for repetitive tasks (running exercisers, scaffolding tests).
- Combine Cursor search (`Cmd+K`) with MCP tools (`adn_search`, `adn_content`) for cross-source context.

---

## 5. Distribution Signals

- Surface Cursor install steps in README/INSTALLATION (already documented).
- Ship config templates in `bootstrap-configs/` to accelerate onboarding.
- Highlight Cursor support in marketplace listings (skillsmp, mcp.cool).
- Provide troubleshooting FAQ: common errors (missing uv, Python PATH, command not found) with resolutions.

---

### Cursor Integration Checklist
- [ ] `.cursor/mcp.json` includes `advanced-memory` entry (command/args validated).
- [ ] `.cursorrules` synced with latest MCP standards and references this skill.
- [ ] Cursor-specific install instructions present in README/INSTALLATION.
- [ ] Config templates generated via bootstrap script and kept up to date.
- [ ] Marketplace and docs advertise Cursor compatibility with exact commands.

Cursor-ready guidance ensures developers can adopt the MCP server with minimal friction while staying aligned with our internal standards.***
