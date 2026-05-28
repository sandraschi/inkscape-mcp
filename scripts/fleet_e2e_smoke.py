"""Fleet E2E smoke: inkscape fab art -> gimp -> robotics (best-effort when offline)."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from inkscape_mcp.utils.fleet_e2e_offline import run_offline_smoke
from inkscape_mcp.utils.fleet_http import (
    DEFAULT_GIMP_URL,
    DEFAULT_INKSCAPE_URL,
    DEFAULT_ROBOTICS_URL,
    call_http_tool,
    check_http_health,
)


async def _probe(name: str, url: str) -> dict[str, object]:
    ok = await check_http_health(url, health_path="/api/health")
    if not ok:
        ok = await check_http_health(url, health_path="/api/v1/health")
    if not ok:
        ok = await check_http_health(url, health_path="/health")
    return {"service": name, "url": url, "online": ok}


async def run_e2e_smoke(
    *,
    svg_path: str | None,
    input_dir: str | None,
    offline: bool = False,
    offline_work_dir: Path | None = None,
) -> dict[str, object]:
    if offline:
        work = offline_work_dir or Path("D:/Temp/fleet_pipeline/inkscape_e2e_offline")
        return await run_offline_smoke(work_dir=work)

    steps: list[dict[str, object]] = []
    probes = await asyncio.gather(
        _probe("inkscape-mcp", DEFAULT_INKSCAPE_URL),
        _probe("gimp-mcp", DEFAULT_GIMP_URL),
        _probe("robotics-mcp", DEFAULT_ROBOTICS_URL),
    )
    steps.append({"name": "fleet_probe", "success": True, "detail": probes})

    inkscape_online = next(p for p in probes if p["service"] == "inkscape-mcp")["online"]
    if inkscape_online:
        presets = await call_http_tool(
            DEFAULT_INKSCAPE_URL,
            "inkscape_fab_art",
            {"operation": "list_presets"},
        )
        steps.append({"name": "inkscape_fab_presets", "success": bool(presets.get("success")), "detail": presets})
    else:
        steps.append({"name": "inkscape_fab_presets", "success": False, "detail": {"skipped": "inkscape offline"}})

    gimp_online = next(p for p in probes if p["service"] == "gimp-mcp")["online"]
    if gimp_online and svg_path and Path(svg_path).is_file():
        raster = await call_http_tool(
            DEFAULT_INKSCAPE_URL,
            "inkscape_fleet",
            {
                "operation": "push_gimp_raster",
                "svg_path": svg_path,
                "target_platform": "gazebo",
            },
        )
        steps.append({"name": "inkscape_to_gimp", "success": bool(raster.get("success")), "detail": raster})
    elif svg_path:
        steps.append({"name": "inkscape_to_gimp", "success": False, "detail": {"skipped": "services offline"}})

    robotics_online = next(p for p in probes if p["service"] == "robotics-mcp")["online"]
    if robotics_online:
        import httpx

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{DEFAULT_ROBOTICS_URL.rstrip('/')}/api/v1/tools/robotics_fab_art",
                    json={"operation": "inkscape_status"},
                )
                body = response.json() if response.status_code == 200 else {"error": response.text}
                steps.append(
                    {
                        "name": "robotics_fab_bridge",
                        "success": response.status_code == 200,
                        "detail": body,
                    },
                )
        except Exception as exc:
            steps.append({"name": "robotics_fab_bridge", "success": False, "detail": {"error": str(exc)}})
    else:
        steps.append({"name": "robotics_fab_bridge", "success": False, "detail": {"skipped": "robotics offline"}})

    if input_dir and Path(input_dir).is_dir() and inkscape_online:
        batch = await call_http_tool(
            DEFAULT_INKSCAPE_URL,
            "inkscape_fab_art",
            {
                "operation": "batch_dxf_export",
                "input_dir": input_dir,
            },
        )
        steps.append({"name": "fab_dxf_batch", "success": bool(batch.get("success")), "detail": batch})

    success = all(bool(s.get("success")) for s in steps if s.get("name") != "fleet_probe")
    return {"success": success, "mode": "http", "steps": steps}


def main() -> None:
    parser = argparse.ArgumentParser(description="Inkscape fleet E2E smoke")
    parser.add_argument("--svg-path", default="")
    parser.add_argument("--input-dir", default="")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--offline-work-dir", default="")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    work_dir = Path(args.offline_work_dir) if args.offline_work_dir else None
    report = asyncio.run(
        run_e2e_smoke(
            svg_path=args.svg_path or None,
            input_dir=args.input_dir or None,
            offline=args.offline,
            offline_work_dir=work_dir,
        ),
    )
    print(json.dumps(report, indent=2))
    if not args.json:
        mode = report.get("mode", "http")
        print(f"\nE2E smoke ({mode}) {'SUCCESS' if report['success'] else 'FAILED'}")
    if args.strict and not report.get("success"):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
