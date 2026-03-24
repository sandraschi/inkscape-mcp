# Distribution & Installation

**Confidence**: 🟢 High
**Last validated**: 2025-11-11
**Primary sources**: Advanced Memory bootstrap scripts, Anthropic MCPB docs, npm packaging guides, marketplace submissions

---

## 1. Dual-channel Strategy

| Channel | Audience | Pros | Cons |
| --- | --- | --- | --- |
| **MCPB package** | Claude Desktop users | One-click install, autoupdates via Claude UI | Claude-only, requires MCPB manifest & review |
| **npx/npm bootstrap** | Cursor, Windsurf, VS Code (future), CLI-first users | Works cross-platform, easy local iteration | Requires Node toolchain; publish to npm for best reach |

Provide both to avoid locking users into a single IDE ecosystem.

---

## 2. MCPB Packaging (Claude-only)

1. Create `.mcpb` manifest (`name`, `description`, `entrypoint`, semantic version).
2. Bundle with zipped server or Git repo pointer.
3. Submit via Claude Desktop MCP settings → “Install from file/URL.”
4. Optional: host on GitHub releases; include checksum.
5. Keep CHANGELOG and manifest version aligned (semantic versioning).

Documentation: `https://docs.anthropic.com/claude/docs/mcp-packages`.

### Sample manifest + signing

```json
{
  "name": "advanced-memory-mcp",
  "description": "Advanced Memory knowledge base interface",
  "entrypoint": "scripts/run_server.ps1",
  "version": "1.0.0b8",
  "homepage": "https://github.com/sandraschi/advanced-memory-mcp",
  "checksum": {
    "algorithm": "sha256",
    "value": "<fill-with-sha256-of-zip>"
  }
}
```

1. Package the server (`git archive -o advanced-memory-mcp.zip HEAD`).
2. Calculate SHA-256 (`Get-FileHash advanced-memory-mcp.zip -Algorithm SHA256`).
3. Embed checksum in manifest and store both files in release artifacts.
4. Sign the archive (optional but recommended):
   - `cosign sign-blob --key cosign.key advanced-memory-mcp.zip > advanced-memory-mcp.zip.sig`
   - Publish `cosign.pub` alongside the signature.
5. Document verification steps for users (`cosign verify-blob --key cosign.pub ...`).

---

## 3. npx/NPM Bootstrapper

1. Create `scripts/bootstrap/<platform>/package.json` and `bootstrap.js`.
2. Script responsibilities: check prerequisites (git, python, uv), clone/update repo, run `uv sync`, `uv run ruff check`, optional `--generate-configs`.
3. Publish to npm (`npm publish`) or provide direct GitHub command (`npx --yes github:user/repo/path`).
4. Document usage in README (`npx --yes ...`), include flags for `--generate-configs`, `--skip-tests`.
5. For Windows, ensure PowerShell compatibility (no `&&`, use `;` or multi-line).

Plan to graduate from GitHub npx to npm registry once stable.

---

## 4. Cross-platform Bootstrap Validation

| OS | Prep | Validation steps |
| --- | --- | --- |
| **macOS (Apple Silicon)** | Ensure Homebrew `python@3.11`, `uv`, and `git` installed; confirm PowerShell 7 or use `bash` shim. | 1. `rm -rf ~/tmp/advanced-memory-mcp`<br>2. `npx --yes github:sandraschi/advanced-memory-mcp/scripts/bootstrap/macos`<br>3. Verify `uv sync`, `uv run ruff check .`, `uv run python -m pytest -k smoke`.<br>4. Confirm configs in `bootstrap-configs/` and launch `Cursor` template. |
| **Linux (Ubuntu LTS)** | Install `python3.11`, `nodejs`, `npm`, `uv`, `git`; set `POWERSHELL=` to skip PowerShell-specific paths. | 1. Run bootstrap with `npx --yes github:.../scripts/bootstrap/linux --skip-powershell`.<br>2. Validate virtualenv path (should default to XDG cache), rerun `uv sync`.<br>3. Execute smoke tests (`scripts/testing/run-all-tool-exercisers.ps1` via `pwsh` or inline python wrapper). |
| **Windows** | Covered in main bootstrap module; ensure PowerShell execution policy permits script. | Compare outputs with macOS/Linux logs to ensure identical versions and config files. |

Document parity runs in release notes and automate via GitHub Actions self-hosted macOS/Linux runners when possible. Store logs under `docs-private/install-validation/` for traceability.

---

## 5. MCP Configuration Templates

- Generate client config (Claude Desktop `claude_config.json`, Windsurf `.windsurf/mcpservers.json`, Cursor `.cursor/mcp.json`).
- Output to `bootstrap-configs/` so users can copy/paste.
- Document additional environment variables/secrets required.
- Provide quickstart snippets in README.

---

## 6. Release Notes & Signatures

- Publish release notes (e.g., `RELEASE_NOTES_1.0.0b8.md`) summarizing new features and installer changes.
- Consider signing release artifacts (Cosign, GPG) to build trust.
- Maintain download stats or user feedback channel (GitHub Discussions, Discord).

---

## 7. Post-install Verification

- Include lightweight health command (`uv run python scripts/testing/test_health_status_tools.py --smoke`).
- Document how to connect from Claude (`/mcp servers add`).
- Encourage users to run `adn_health("status")` or equivalent to confirm installation.

---

### Distribution Checklist
- [ ] MCPB manifest current; packaged builds tested in Claude Desktop.
- [ ] npx/npm bootstrapper verified on Windows/macOS/Linux; README instructions updated (logs stored in docs-private).
- [ ] Config templates generated and versioned.
- [ ] Release notes and versioning synchronized across manifest, pyproject, docs.
- [ ] Post-install tests documented for users.

Delivering polished installers broadens adoption and reduces setup friction across IDEs.***
