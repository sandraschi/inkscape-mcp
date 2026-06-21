# ── Fleet Standard Recipes ──
# Import this file in any repo's justfile:
#     import 'scripts/just/fleet.just'
# Defines only recipes repos typically don't ship themselves.
# build-native/build-sidecar are NOT here — repos define their own with VC vars.

REPO_DIR := justfile_directory()

# ── Build & Release ──────────────────────────────────────────────────────────

# Build .mcpb bundle for Claude Desktop (auto-generates manifest + .mcpbignore if missing)
mcpb-pack:
    pwsh -NoProfile -File "{{REPO_DIR}}/scripts/mcpb-pack.ps1" -RepoRoot "{{REPO_DIR}}"

# Run CUA-NSIS smoke test (install → launch → verify → uninstall)
cua-nsis-test:
    C:\Windows\py.exe scripts/cua-smoke.py

# ── Utilities ─────────────────────────────────────────────────────────────────

# Scan repository for Unicode issues in logger/print calls
emojibuster:
    pwsh -NoProfile -File "{{REPO_DIR}}/scripts/just/emojibuster.ps1" -Path "{{REPO_DIR}}"
