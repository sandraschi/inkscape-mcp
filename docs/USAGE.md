# Usage

Agents interact with **MCP tools**, not Python functions in your notebook. The server exposes **portmanteau** tools: each tool takes an `operation` string and paths/parameters.

Full parameter detail: [API.md](API.md). Install: [INSTALL.md](INSTALL.md). Inkscape: [INKSCAPE.md](INKSCAPE.md). Sampling workflows: [AI_SAMPLING.md](AI_SAMPLING.md).

## Tools at a glance

| Tool | Role |
|------|------|
| `inkscape_file` | `load`, `convert`, `info`, `validate`, `list_formats` |
| `inkscape_vector` | trace, boolean, simplify, preview, QR, units, z-order, … |
| `inkscape_analysis` | `statistics`, `validate`, `dimensions` |
| `inkscape_system` | `status`, `version`, `help`, `config`, `diagnostics`, extensions |
| `list_local_models` | optional local LLM discovery |

## Natural language → tool

Ask in plain language; the model should map to the right tool and `operation`. Examples:

- “Validate `logo.svg` and tell me width and height.” → `inkscape_file` / `inkscape_analysis`
- “Export `diagram.svg` to `diagram.pdf`.” → `inkscape_file` `convert`
- “Trace `scan.png` to `scan.svg`.” → `inkscape_vector` `trace_image`
- “Is Inkscape available?” → `inkscape_system` `status`

## JSON shape (illustrative)

Exact fields match the tool signatures in code; this is a typical pattern:

```json
{
  "operation": "convert",
  "input_path": "/path/to/in.svg",
  "output_path": "/path/to/out.pdf",
  "format": "pdf"
}
```

For `inkscape_vector`, include `input_path` and, when needed, `output_path`, `object_id`, `operation_type`, etc.

## Safe habits

- Prefer **absolute paths** if the client’s working directory is unclear.
- **Confirm overwrites** before `convert` or destructive vector ops.
- Run **`status`** or **`validate`** before long batches.

## Agentic / multi-step

When the client supports sampling, optional agentic tools can orchestrate plans. Otherwise chain the portmanteau tools yourself — [AI_SAMPLING.md](AI_SAMPLING.md).

## Config

Optional YAML or env-based settings (Inkscape path, timeouts). See server help output and [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
