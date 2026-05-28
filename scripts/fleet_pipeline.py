"""CLI for fleet vector pipeline (inkscape -> gimp -> unity)."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

from inkscape_mcp.cli_wrapper import InkscapeCliWrapper
from inkscape_mcp.config import InkscapeConfig
from inkscape_mcp.inkscape_detector import InkscapeDetector
from inkscape_mcp.utils.fleet_http import DEFAULT_BLENDER_URL
from inkscape_mcp.utils.fleet_http import DEFAULT_GIMP_URL
from inkscape_mcp.utils.fleet_http import DEFAULT_UNITY_URL
from inkscape_mcp.utils.fleet_pipeline import run_fleet_pipeline
from inkscape_mcp.utils.fleet_staging import DEFAULT_STAGING_DIR

logger = logging.getLogger(__name__)


def _load_cli() -> tuple[Any, InkscapeConfig]:
    config = InkscapeConfig.load_default()
    detector = InkscapeDetector()
    path = detector.detect_inkscape_installation()
    if path:
        config.inkscape_executable = str(path)
    wrapper = InkscapeCliWrapper(config) if config.inkscape_executable else None
    return wrapper, config


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fleet vector pipeline: inkscape SVG -> PNG -> gimp QA -> unity sprite",
    )
    parser.add_argument("--svg-path", required=True, help="Source SVG path")
    parser.add_argument("--project-path", required=True, help="Unity project path")
    parser.add_argument("--png-path", default="", help="Existing PNG (skip export if set)")
    parser.add_argument("--staging-dir", default=str(DEFAULT_STAGING_DIR))
    parser.add_argument("--dpi", type=int, default=192)
    parser.add_argument("--gimp-url", default=DEFAULT_GIMP_URL)
    parser.add_argument("--blender-url", default=DEFAULT_BLENDER_URL)
    parser.add_argument("--unity-url", default=DEFAULT_UNITY_URL)
    parser.add_argument("--skip-validate", action="store_true")
    parser.add_argument("--skip-gimp", action="store_true")
    parser.add_argument("--stage-blender", action="store_true")
    parser.add_argument("--import-to-blender", action="store_true")
    parser.add_argument("--skip-unity", action="store_true")
    parser.add_argument("--target-platform", default="unity")
    parser.add_argument("--json", action="store_true", help="Print JSON report only")
    return parser


async def _main_async(args: argparse.Namespace) -> int:
    cli_wrapper, config = _load_cli()
    report = await run_fleet_pipeline(
        svg_path=args.svg_path,
        project_path=args.project_path,
        png_path=args.png_path or None,
        staging_dir=Path(args.staging_dir),
        dpi=args.dpi,
        gimp_url=args.gimp_url,
        blender_url=args.blender_url,
        unity_url=args.unity_url,
        skip_validate=args.skip_validate,
        skip_gimp=args.skip_gimp,
        skip_blender_stage=not args.stage_blender,
        import_to_blender=args.import_to_blender,
        skip_unity=args.skip_unity,
        target_platform=args.target_platform,
        cli_wrapper=cli_wrapper,
        config=config,
    )

    payload = report.to_dict()
    print(json.dumps(payload, indent=2))
    if not args.json:
        print(f"\nPipeline {'SUCCESS' if report.success else 'FAILED'}")
    return 0 if report.success else 1


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = _build_parser()
    args = parser.parse_args()
    try:
        code = asyncio.run(_main_async(args))
    except KeyboardInterrupt:
        code = 130
    sys.exit(code)


if __name__ == "__main__":
    main()
