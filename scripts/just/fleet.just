# ── Fleet Standard Recipes ──
# Import this file in any repo's justfile:
#     import 'scripts/just/fleet.just'
# Defines only recipes repos typically don't ship themselves.
# build-native/build-sidecar/mcpb-pack/cua-nsis-test are NOT here —
# repos define those with repo-specific config and prerequisites.

REPO_DIR := justfile_directory()

# ── Utilities ─────────────────────────────────────────────────────────────────

# Scan repository for Unicode issues in logger/print calls
emojibuster:
    pwsh -NoProfile -File "{{REPO_DIR}}/scripts/just/emojibuster.ps1" -Path "{{REPO_DIR}}"
