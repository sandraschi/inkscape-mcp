# Contributing to Inkscape MCP

Thank you for your interest in contributing to Inkscape MCP! We welcome contributions that improve the bridge between agentic workflows and vector graphics.

## Development Setup

### Prerequisites
- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- [Inkscape](https://inkscape.org/) installed and available in your system PATH

### Installation
```powershell
# Clone the repository
git clone https://github.com/sandraschi/inkscape-mcp.git
cd inkscape-mcp

# Sync environment
uv sync
```

## Development Workflow

### 1. Verification
Use the `just` dashboard to verify your changes:
```powershell
just test    # Run pytest suite
just lint    # Run ruff check
just check   # Full quality verification (lint + test + typecheck)
```

### 2. Running Locally
```powershell
just run-stdio  # Test as an MCP stdio server
```

## Pull Request Process

1. Fork the repository and create your feature branch.
2. Ensure your code follows the **PowerShell-first** operational heuristics for Windows.
3. Update relevant documentation in `docs/` if modifying tool signatures or operations.
4. Verify all tests pass using `just check`.
5. Submit your Pull Request.

## License

By contributing to Inkscape MCP, you agree that your contributions will be licensed under the same MIT License that covers the project.

Thank you for contributing! 🎨
