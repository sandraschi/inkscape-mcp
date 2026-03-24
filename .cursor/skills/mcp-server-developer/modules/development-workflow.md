# Development Workflow

**Confidence**: 🟢 High
**Last validated**: 2025-11-11
**Primary sources**: Advanced Memory dev workflow docs, internal tooling scripts, FastMCP docs, ruff/pytest guidance

---

## 1. Environment Setup

1. **Clone & uv sync**: `uv sync` installs pinned dependencies (FastMCP, loguru, pytest, ruff).
2. **Pre-commit helpers**: Mirror `scripts/pre_commit_check.py` or create similar guard to run imports, syntax, tool registration, ruff.
3. **PowerShell profile** (Windows) or shell script to ensure Python PATH and uv caching are correct.

---

## 2. The Ruff ↔ Pytest Dance

| Step | Command | Purpose |
| --- | --- | --- |
| Lint | `uv run ruff check .` | Guarantee zero lint errors; treat warnings as blockers. |
| Format | `uv run ruff format .` | Keep diffs clean; run after lint passes. |
| Tests | `uv run python -m pytest -v` | Validate unit/integration tests (include tool exercisers). |
| Smoke | `uv run python scripts/testing/test_core_tools.py --skip-heavy` | Fast verification of tool contracts and structured errors. |
| Full suite | `scripts/testing/run-all-tool-exercisers.ps1` | Optional but recommended before releases; covers import/export, skills, health/sync. |

Fail any step? Fix immediately; never defer to “after commit.”

---

## 3. Inner-loop Practices

- **TDD / doc-first**: Draft module docstrings and Pydantic models before writing tool logic.
- **Fixtures**: Use pytest fixtures for storage, config, and external API stubs.
- **Type hints**: Maintain full typing to catch interface mismatches early (`pyright` optional but encouraged).
- **Watch mode**: Leverage `watchexec` or IDE runners to re-run targeted tests when files change.
- **Logging toggles**: Use environment variable (e.g., `MCP_DEBUG=1`) to surface extra debug output when needed.

---

## 4. Feature Workflow Template

1. Create ADR or architecture note (Problem, Goals, Non-goals, Design).
2. Update `.cursorrules` or documentation if standards change.
3. Implement services first, followed by tool wrappers.
4. Write or update tests (unit + integration).
5. Run ruff / format / pytest.
6. Regenerate skill archives if skill content changed.
7. Update docs (README, INSTALLATION, CHANGELOG).
8. Commit with descriptive message referencing issue or ADR.

---

## 5. Tool Exerciser Scripts

| Script | Coverage |
| --- | --- |
| `scripts/testing/test_core_tools.py` | Hits every exposed portmanteau with valid + invalid params (`operation="explode"`). |
| `scripts/testing/test_import_export_tools.py` | Validates packaging/import flows, ensures structured errors. |
| `scripts/testing/test_skills_tools.py` | Exercises skills and skill-creator operations including GitHub/Wikipedia distillation. |
| `scripts/testing/test_health_status_tools.py` | Checks status/health/sync endpoints. |

Integrate these into CI/CD to catch regressions before release.

---

## 6. Git Hygiene

- **Small PRs** focused on a single concern.
- **Conventional commits** optional but helpful (`feat:`, `fix:`, `docs:`).
- **Refactor vs feature** commits separated to keep review clean.
- **Do not commit** large binaries or secrets; rely on `.gitignore` and pre-commit scanning.

---

### Workflow Checklist
- [ ] Environment bootstrapped with uv and pre-commit guard rails.
- [ ] Ruff lint + format run on every change; zero tolerance for failures.
- [ ] Pytest suites and tool exercisers pass locally.
- [ ] Documentation and CHANGELOG updated in tandem with code.
- [ ] Git commits clean, scoped, and free of sensitive data.

Following this workflow keeps development predictable, review-friendly, and ready for release automation.***
