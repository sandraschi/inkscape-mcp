# Release Readiness

**Confidence**: 🟢 High
**Last validated**: 2025-11-11
**Primary sources**: Advanced Memory release process, Release Flash checklist, CI/CD roadmap notes

---

## 1. Pre-release Gate

| Gate | Criteria | Tools |
| --- | --- | --- |
| Code health | `uv run ruff check .`, `uv run ruff format .`, `uv run python -m pytest -v` | CI pipeline, local scripts |
| Tool contracts | Tool exercisers (core/import/export/skills/health) pass | `scripts/testing/run-all-tool-exercisers.ps1` |
| Skill archives | `scripts/maintenance/rebuild_skill_archives.py` re-runs without errors | ensures packaged skills match source |
| Docs & versioning | README, INSTALLATION, `.cursorrules`, CHANGELOG, release notes updated | manual review |
| Security review | Secrets scan clean, dependencies checked, error handling consistent | `gitleaks`, dependency audit |

Do not tag a release until every gate is green.

---

## 2. CI/CD Highlights

- **Lint & Test**: Run ruff + pytest in GitHub Actions (Linux, Windows matrix).
- **Packaging job**: Build MCPB artifact, npm package (if publishing), attach to GitHub release.
- **Smoke tests**: Invoke a headless FastMCP client or use recorded Claude Desktop log to ensure startup.
- **Release automation**: Tag + release note generation (e.g., `releaselib`, `semantic-release`).
- **Post-release monitor**: Alert on error rate spikes or install failures.

Future milestone (from CI/CD roadmap): add macOS runner, automated marketplace PR updates.

---

## 3. Versioning & Tagging

- Adopt semantic versioning (e.g., `1.0.0`, `1.1.0`, `1.1.1`). Beta builds may use suffix (`1.0.0b9`).
- Sync version across `pyproject.toml`, MCPB manifest, npm package, README badge.
- Tag format: `git tag v1.0.0`, include release notes summary.
- Push tag before publishing to npm or uploading MCPB.

---

## 4. Release Notes Template

```
## Highlights
- Feature 1
- Feature 2

## Install
- MCPB: ...
- npx/npm: ...

## Checks
- Ruff / pytest / tool exercisers ✅
- Skill archives regenerated ✅

## Follow-ups
- ...

```

Keep concise but informative; link to docs for deeper detail.

---

## 5. Post-release Actions

- Verify installation on clean machine/VM.
- Update marketplace listings (skillsmp, mcp.cool).
- Notify community and collect feedback.
- Create ticket backlog for follow-ups noted in release notes.
- Monitor logs/analytics for regression signs.

---

### Release Checklist
- [ ] All gates green (lint, tests, tool exercisers, archives, docs).
- [ ] Version synchronized; release notes drafted.
- [ ] CI pipeline succeeded on target platforms.
- [ ] Distribution artifacts built (MCPB, npm).
- [ ] Marketplaces and community notified; monitoring in place.

A disciplined release process protects user trust and keeps your MCP server production-ready.***
