# Development Setup

## Tools Required

```bash
# Windows (winget)
winget install astral-sh.uv
winget install Git.Git
winget install OpenJS.NodeJS
winget install Casey.Just

# Verify
uv --version && git --version && node --version && just --version
```

## Setup

```bash
git clone https://github.com/sandraschi/inkscape-mcp
cd inkscape-mcp
uv sync
```

## Common Tasks

```bash
just serve            # Start HTTP server on :11028
just dev              # Start webapp + backend
just lint             # ruff check
just test             # pytest
just fix              # ruff fix + format
just build-native     # Build NSIS Windows installer
just build-sidecar    # Build PyInstaller backend
just capture          # Generate screenshots + demo video
```

## Code Standards

- Ruff linting with strict rules
- Biome for frontend code
- FastMCP 3.4+ portmanteau tool pattern
- Fleet standards: `D:\Dev\repos\mcp-central-docs\standards\`
