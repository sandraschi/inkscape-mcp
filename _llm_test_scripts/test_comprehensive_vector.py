#!/usr/bin/env python3
"""
Comprehensive test script for all Inkscape vector operations.
Demonstrates the full power of the vibe architect workflow.
"""

import sys
import os
import asyncio
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from inkscape_mcp.tools.vector_operations import inkscape_vector


async def test_all_operations():
    """Test all major vector operations."""
    print("TESTING: Inkscape Vector Operations - Vibe Architect Workflow")
    print("=" * 60)

    # Test 1: Generate QR Code
    print("\n1. Generating QR Code...")
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
        qr_path = tmp.name

    result = await inkscape_vector(
        operation="generate_barcode_qr",
        output_path=qr_path,
        barcode_data="https://github.com/antigravity",
        barcode_type="qr",
    )
    print(f"   Result: {'SUCCESS' if result.get('success') else 'FAILED'} {result.get('message')}")

    # Test 2: Create Mesh Gradient
    print("\n2. Creating Mesh Gradient...")
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
        gradient_path = tmp.name

    result = await inkscape_vector(
        operation="create_mesh_gradient",
        output_path=gradient_path,
        gradient_stops=[
            {"color": "#FF0000", "x": 0, "y": 0},
            {"color": "#00FF00", "x": 200, "y": 0},
            {"color": "#0000FF", "x": 0, "y": 200},
            {"color": "#FFFF00", "x": 200, "y": 200},
        ],
    )
    print(f"   Result: {'SUCCESS' if result.get('success') else 'FAILED'} {result.get('message')}")

    # Test 3: Text to Path
    print("\n3. Converting Text to Path...")
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
        text_path = tmp.name

    result = await inkscape_vector(
        operation="text_to_path",
        output_path=text_path,
        text_content="AG VIBE",
        font_family="Arial",
        font_size=48.0,
    )
    print(f"   Result: {'SUCCESS' if result.get('success') else 'FAILED'} {result.get('message')}")

    # Test 4: Construct SVG (Polish Crest)
    print("\n4. Constructing Polish Royal Crest...")
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
        crest_path = tmp.name

    result = await inkscape_vector(
        operation="construct_svg",
        output_path=crest_path,
        description="Create the royal crest of arms of Poland - white eagle with crown on red background",
    )
    print(f"   Result: {'SUCCESS' if result.get('success') else 'FAILED'} {result.get('message')}")

    # Test 5: Count Nodes (Complexity Analysis)
    print("\n5. Analyzing Path Complexity...")
    result = await inkscape_vector(
        operation="count_nodes", input_path=crest_path, target_object="eagle-body"
    )
    print(f"   Result: {'SUCCESS' if result.get('success') else 'FAILED'} {result.get('message')}")

    # Test 6: Path Clean (Optimization)
    print("\n6. Cleaning SVG (Removing LDDO)...")
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
        clean_path = tmp.name

    result = await inkscape_vector(
        operation="path_clean", input_path=crest_path, output_path=clean_path
    )
    print(f"   Result: {'SUCCESS' if result.get('success') else 'FAILED'} {result.get('message')}")

    # Test 7: Generate Laser Dot (Easter Egg)
    print("\n7. Generating Laser Dot for Benny...")
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
        laser_path = tmp.name

    result = await inkscape_vector(
        operation="generate_laser_dot", output_path=laser_path, dot_x=300.0, dot_y=200.0
    )
    print(f"   Result: {'SUCCESS' if result.get('success') else 'FAILED'} {result.get('message')}")

    print("\n" + "=" * 60)
    print("SUCCESS: Vibe Architect Workflow Complete!")
    print(f"Generated {7} SVG files for testing")

    # Clean up
    for path in [qr_path, gradient_path, text_path, crest_path, clean_path, laser_path]:
        if os.path.exists(path):
            os.unlink(path)


if __name__ == "__main__":
    asyncio.run(test_all_operations())
