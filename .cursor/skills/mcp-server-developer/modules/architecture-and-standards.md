# Architecture & Standards

**Confidence**: 🟢 High
**Last validated**: 2025-11-11
**Primary sources**: Anthropic FastMCP repo (2.13 release notes), Advanced Memory `.cursorrules`, Anthropic skill-creator patterns, Sandra Schiavone’s portmanteau reorg plan

---

## 1. FastMCP 2.13+ Foundations

| Requirement | Why it matters | Implementation tips |
| --- | --- | --- |
| `FastMCP("server-name", lifespan=...)` | Server lifespan hooks enable persistent storage, startup validation, and graceful shutdown. | Use `@asynccontextmanager` to warm caches, open storage, and close resources. |
| Persistent storage | Claude Desktop restarts should not erase state. | `from fastmcp.storage import DiskStore`; wrap in your own persistence service. |
| Thin entrypoint | Keeps `server.py` under ~150 lines, enabling easier testing and reuse. | Only import tool registries, initialize storage, and call `mcp.add_tools(...)`. |
| Async tools | MCP tools must be async to avoid blocking the event loop. | Wrap sync libraries with executors or `asyncio.to_thread`. |
| Structured logging | Required for debugging Claude Desktop interactions. | Use `loguru` or standard `logging` with structured context (tool name, operation, latency). |

Reference: `https://github.com/anthropic/fastmcp` (tag `v2.13.0`), `docs/architecture/CLAUDE_SKILLS_ACTUAL_FORMAT.md`.

---

## 2. Folder Layout Blueprint

```
src/your_project/
├── mcp/
│   ├── server.py                # Thin entrypoint, imports tools and storage
│   └── tools/
│       ├── __init__.py          # Registers portmanteau tools
│       ├── shared/              # Reusable helpers (logging, validation)
│       └── <category>/          # Tool families (e.g., content/, skills/, automation/)
│           ├── tools.py         # @mcp.tool definitions
│           └── models.py        # Pydantic schemas
├── services/                    # Business logic, external integrations
├── storage/                     # Persistence adapters
└── tests/                       # pytest suites, fixtures, golden responses
```

Keep business logic out of tool definitions—tools orchestrate, services execute.

---

## 3. Error & Security Standards

- **Error contract**: `{"success": False, "error": "...", "error_code": "...", "suggestions": [...], "related_tools": [...]}`. Never raise raw exceptions.
- **Logging**: Log start, success, and failure events (`logger.info`, `logger.error(..., exc_info=True)`); include operation names and durations.
- **Input validation**: Pydantic models or manual validation for external user input. Reject suspicious patterns (shell metacharacters, HTML injection).
- **Command execution**: Prefer library APIs; if shell commands unavoidable, sanitize with `shlex.quote` and timeouts.
- **Transport security**: When calling external APIs, use HTTPS, handle OAuth tokens securely, and redact secrets in logs.

Reference: Advanced Memory `.cursorrules`, CVE notes in FastMCP 2.13 release.

---

## 4. Portmanteau Tool Design

- Group cohesive operations: e.g., `adn_content(operation="read")`, `adn_content(operation="write")`.
- Provide exhaustive docstrings following the mandated template (Prerequisites, Parameters, Returns, Usage, Examples, Errors, See Also).
- Keep operations discoverable: include operation list in docstring, ensure consistent parameter naming.
- Use helper routers inside the tool file (e.g., `_dispatch = {"list": _list_operation, ...}`) to keep main function tidy.
- Surface `Literal[...]` typing for `operation` to improve autocomplete and static validation.

---

## 5. Storage Strategy

| Scenario | Recommendation |
| --- | --- |
| Simple key/value | FastMCP DiskStore wrapper with JSON serialization. |
| Large documents | SQLite / DuckDB via `aiosqlite`, stored under `storage/`. |
| External integrations | Abstract clients in `services/` and inject via lifespan. |
| Secrets | Use environment variables or secure vault integration; do not hardcode in repo. |

Ensure tests can inject in-memory storage for deterministic behavior.

---

## 6. Documentation & Standards Alignment

- `.cursorrules` – enforce internal standards (FastMCP version, error handling, docstring requirements).
- README / INSTALLATION – stay in sync with installers (npx/npm, MCPB).
- Architecture docs – capture design decisions (ADR template) and portmanteau map.
- CHANGELOG – update for every release (semver or beta tags).

Keep documentation versioned alongside code to avoid drift.

---

### Architecture Checklist
- [ ] FastMCP 2.13+ lifespan, storage, and async compliance verified.
- [ ] `server.py` thin, tools organized by category with Pydantic schemas.
- [ ] Errors structured, logged, and actionable; no uncaught exceptions.
- [ ] Portmanteau tools defined with clear operation matrices and docstrings.
- [ ] Storage abstractions support tests and future persistence needs.
- [ ] Docs (.cursorrules, README, INSTALLATION) reflect current architecture.

This module ensures your server architecture is future-proof, secure, and aligned with Anthropic expectations.***
