#!/usr/bin/env python3
"""
Test script to generate the Polish royal crest using the new construct_svg operation.
"""

import sys
import os
import asyncio
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from inkscape_mcp.tools.vector_operations import inkscape_vector


async def test_polish_crest():
    """Test constructing the Polish royal crest."""
    print("Testing Polish royal crest construction...")

    # Create temporary output file
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
        output_path = tmp.name

    try:
        # Construct the crest
        result = await inkscape_vector(
            operation="construct_svg",
            output_path=output_path,
            description="Create the royal crest of arms of Poland - white eagle with crown on red background",
            cli_wrapper=None,  # No CLI wrapper needed for basic construction
            config=None,
        )

        print(f"Result: {result}")

        if result.get("success"):
            print(f"SUCCESS: Successfully created Polish crest at: {output_path}")

            # Read and show a bit of the content
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
                print(f"Generated SVG ({len(content)} characters):")
                print(content[:500] + "..." if len(content) > 500 else content)
        else:
            print(f"FAILED: Failed to create crest: {result.get('error')}")

    except Exception as e:
        print(f"ERROR: {e}")

    finally:
        # Clean up
        if os.path.exists(output_path):
            os.unlink(output_path)


if __name__ == "__main__":
    asyncio.run(test_polish_crest())
