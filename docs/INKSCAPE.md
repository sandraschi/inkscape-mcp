# Inkscape application

The MCP server shells out to **Inkscape**. If the CLI is missing or wrong, every tool fails.

## Install Inkscape

- **Windows:** [inkscape.org/release](https://inkscape.org/release/) — ensure the install adds Inkscape to PATH, or note the full path to `inkscape.exe` (often under `C:\Program Files\Inkscape\bin\`).
- **macOS:** Official dmg / Homebrew; ensure `inkscape` is on PATH in the environment your IDE uses.
- **Linux:** distro package or Flatpak; for Flatpak, the host MCP process may need the wrapper path your setup documents.

## Verify the CLI

In the **same** terminal (or environment) the MCP server will use:

```bash
inkscape --version
```

You should see a version line (1.x). **1.2+** is recommended for Actions-based automation.

## Configuration

- **Auto-detect:** the server tries to find Inkscape on startup.
- **Override:** set `inkscape_path` in config, or environment variables such as `INKSCAPE_PATH` if your deployment uses them (see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)).

## Limitations

Not every Inkscape feature is exposed as a CLI action. If an operation returns “not implemented” or fails, use the GUI for that step or open an issue with the exact action and version.
