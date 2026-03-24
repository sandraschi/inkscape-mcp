# Tooling Strategy

**Confidence**: 🟢 High
**Last validated**: 2025-11-11
**Primary sources**: Advanced Memory portmanteau plan, Anthropic marketplace guidance, internal tooling audits

---

## 1. Avoiding Tool Explosion

| Problem | Consequence | Mitigation |
| --- | --- | --- |
| Too many discrete tools | Claude Desktop limits registered tools; UX becomes noisy. | Consolidate operations into portmanteau tools with `operation` parameter. |
| Overlapping responsibilities | Difficulty maintaining consistent behavior and docs. | Define clear capability boundaries per tool family (content, skills, import/export). |
| Deeply nested options | Harder for AI to guess parameters. | Use Pydantic models with descriptive field names and defaults; document examples. |

Track exposed tool count in README; aim for 12–16 carefully curated portmanteaus.

---

## 2. Designing Portmanteau Interfaces

- **Operation taxonomy**: map each operation to CRUD verbs or workflow stages (`create`, `read`, `update`, `list`, `validate`).
- **Parameter consistency**: e.g., `identifier`, `operation`, `project`, `tags` should behave the same across tools.
- **Fallback handling**: include safe defaults; return `INVALID_OPERATION` structured error for unknown `operation`.
- **Docstring clarity**: list operations with bullet points; provide examples for each to help model selection.
- **Dispatch pattern**: use dictionary mapping to private funcs to keep main tool readable.

---

## 3. Shared Utilities

- **Input validation**: centralize common validators (note identifiers, file paths) in `tools/shared/validators.py`.
- **Error helpers**: create `make_error(...)` factory to guarantee consistent error payloads.
- **Logging decorators**: standardize logging and timing with context managers or wrappers.
- **Retry/backoff**: shared HTTP client with exponential backoff and circuit breaker for unreliable APIs.

---

## 4. Testing & Contracts

- Write golden tests for portmanteau operation routing (expected error codes, success payload schema).
- Snapshot structured error responses to ensure AI-parseable output stays stable.
- Add contract tests to verify invalid operations produce suggestions pointing to valid options.
- Use coverage reports to spot categories lacking tests.

---

## 5. Documentation Alignment

- Keep `docs/PORTMANTEAU_TOOLS_REFERENCE.md` current; update after each tooling change.
- Each tool docstring should mirror README description to avoid drift.
- Provide quickstart examples in README showing how to call exposed tools from Claude (e.g., `.fn(...)`).
- Document negative cases (what happens if `operation="explode"`).

---

## 6. Monitoring Tool Usage

- Log operation invocations and error codes; aggregate metrics to identify underused or noisy operations.
- Periodically review logs for operations with high failure rates; adjust defaults or docs.
- Consider analytics integration (e.g., simple CSV export, Grafana dashboard).

---

### Tooling Checklist
- [ ] Portmanteau boundaries defined; exposed tool count within target range.
- [ ] Parameters consistent across tools; docstrings list operations with examples.
- [ ] Shared utilities handle validation, logging, and error shaping.
- [ ] Tests cover routing, success, and failure paths for every operation.
- [ ] Documentation and metrics reflect actual tool behavior.

Disciplined tooling keeps MCP servers ergonomic for Claude while remaining maintainable for developers.***
