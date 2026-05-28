"""Smoke test for inkscape-mcp Agent Lab tool surface and telemetry."""

from __future__ import annotations

import asyncio
import sys


async def main() -> int:
    from inkscape_mcp.main import InkscapeMCPServer
    from inkscape_mcp.utils.execution_mode import describe_execution_mode
    from inkscape_mcp.utils.telemetry import init_metrics, metrics_enabled, render_metrics

    print("=== inkscape-mcp smoke test ===")
    server = InkscapeMCPServer()
    if not await server.initialize():
        print("FAIL server initialization")
        return 1

    init_metrics()
    tools = await server.mcp.list_tools()
    names = {t.name for t in tools}
    required = {
        "inkscape_file",
        "inkscape_vector",
        "inkscape_analysis",
        "inkscape_render",
        "inkscape_validation",
        "inkscape_fleet",
        "inkscape_fab_art",
        "inkscape_system",
    }
    missing = required - names
    print(f"Tools registered: {len(names)}")
    if missing:
        print(f"FAIL missing tools: {sorted(missing)}")
        return 1
    print(f"OK phase tools present: {sorted(required)}")

    mode = await describe_execution_mode(cli_wrapper=server.cli_wrapper, config=server.config)
    print(
        f"Execution mode: {mode.get('label')} ({mode.get('mode')}) "
        f"cli={mode.get('cli_available')}"
    )

    for tool_name, args in [
        ("inkscape_system", {"operation": "status"}),
        ("inkscape_system", {"operation": "execution_mode"}),
        ("inkscape_fleet", {"operation": "list_staging"}),
        ("inkscape_validation", {"operation": "check_viewbox", "input_path": "D:/Temp/missing.svg"}),
    ]:
        result = await server.mcp.call_tool(tool_name, args)
        text = result.content[0].text if result.content else str(result)
        print(f"OK {tool_name}: {text[:140].replace(chr(10), ' ')}")

    metrics_body = render_metrics()
    if metrics_enabled() and b"inkscape_mcp" not in metrics_body and b"disabled" in metrics_body:
        print("WARN metrics enabled but prometheus_client may be missing")
    else:
        print(f"OK metrics endpoint bytes={len(metrics_body)}")

    print("=== smoke test passed ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
