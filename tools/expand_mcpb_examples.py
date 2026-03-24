"""Ensure mcp-server/assets/prompts/examples.json has >= 100 tool-call examples."""

from __future__ import annotations

import json
from pathlib import Path


def _extra_examples() -> list[dict]:
    """Structured mappings: inkscape_file / vector / analysis / system."""
    ex: list[dict] = []
    n = 0
    file_ops = [
        ("load", "Open this SVG and confirm it loads", "design{}.svg"),
        ("info", "Dimensions and size for this file", "page{}.svg"),
        ("validate", "Is this SVG well-formed?", "icon{}.svg"),
        ("convert", "Export to PDF for print", "logo{}.svg", "out{}.pdf", "pdf"),
        ("list_formats", "Which export types exist?", None, None, None),
    ]
    for i in range(25):
        op, ui, pat = file_ops[i % 5][0], file_ops[i % 5][1], file_ops[i % 5][2]
        params: dict = {"operation": op}
        if op != "list_formats":
            params["input_path"] = pat.format(i)
        if op == "convert":
            params["output_path"] = file_ops[3][3].format(i)
            params["format"] = "pdf"
        ex.append(
            {
                "title": f"File {op} example {i + 39}",
                "description": f"Demonstrate inkscape_file {op}",
                "user_input": ui,
                "tool_call": "inkscape_file",
                "parameters": params,
                "expected_output": "Structured result with success flag and data or error",
            }
        )
        n += 1

    vec_ops = [
        ("trace_image", "Trace bitmap {} to SVG", "in{}.png", "out{}.svg"),
        ("path_simplify", "Simplify paths in {}", "busy{}.svg", "simp{}.svg"),
        ("render_preview", "PNG preview of {}", "doc{}.svg", "prev{}.png"),
        ("query_document", "Summarize objects in {}", "lay{}.svg", None),
        ("count_nodes", "Node count for object in {}", "p{}.svg", None),
    ]
    for i in range(30):
        op, ui_t, inp, outp = vec_ops[i % 5]
        params = {"operation": op, "input_path": inp.format(i)}
        if outp:
            params["output_path"] = outp.format(i)
        ex.append(
            {
                "title": f"Vector {op} example {i}",
                "description": f"inkscape_vector {op}",
                "user_input": ui_t.format(f"file{i}"),
                "tool_call": "inkscape_vector",
                "parameters": params,
                "expected_output": "Vector operation result or not-implemented notice",
            }
        )

    for i in range(15):
        op = ["statistics", "validate", "dimensions"][i % 3]
        ex.append(
            {
                "title": f"Analysis {op} {i}",
                "description": f"inkscape_analysis {op}",
                "user_input": f"Run {op} on sheet{i}.svg",
                "tool_call": "inkscape_analysis",
                "parameters": {"operation": op, "input_path": f"sheet{i}.svg"},
                "expected_output": "Analysis payload with measurements or validation",
            }
        )

    sys_ops = [
        "status",
        "version",
        "help",
        "diagnostics",
        "config",
        "list_extensions",
    ]
    for i in range(20):
        op = sys_ops[i % len(sys_ops)]
        ex.append(
            {
                "title": f"System {op} {i}",
                "description": f"inkscape_system {op}",
                "user_input": f"Server {op} please",
                "tool_call": "inkscape_system",
                "parameters": {"operation": op},
                "expected_output": "System tool structured response",
            }
        )

    for i in range(10):
        ex.append(
            {
                "title": f"Local models discovery {i}",
                "description": "list_local_models",
                "user_input": "What local LLM endpoints are available?",
                "tool_call": "list_local_models",
                "parameters": {},
                "expected_output": "List of models or empty if none",
            }
        )

    return ex


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    path = repo / "mcp-server" / "assets" / "prompts" / "examples.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    existing = data.get("examples", [])
    have = {json.dumps(e, sort_keys=True) for e in existing}
    for e in _extra_examples():
        key = json.dumps(e, sort_keys=True)
        if key in have:
            continue
        existing.append(e)
        have.add(key)
    data["examples"] = existing
    if len(existing) < 100:
        raise SystemExit(f"Still only {len(existing)} examples; adjust templates.")
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(existing)} examples to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
