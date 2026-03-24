#!/usr/bin/env python3
"""Test import of new Inkscape tools."""

try:
    from src.inkscape_mcp.tools import PORTMANTEAU_TOOLS

    print("All tools imported successfully")
    print(f"Found {len(PORTMANTEAU_TOOLS)} portmanteau tools")
    for tool in PORTMANTEAU_TOOLS:
        print(f"  - {tool['name']}: {len(tool['operations'])} operations")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback

    traceback.print_exc()
