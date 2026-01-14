"""
SVG test fixtures and data for testing.
"""

import tempfile
from pathlib import Path
from typing import Dict, List


# Sample SVG content for testing
SVG_FIXTURES = {
    "minimal": """<?xml version="1.0" encoding="UTF-8"?>
<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="10" width="80" height="80" fill="blue"/>
</svg>""",
    "with_objects": """<?xml version="1.0" encoding="UTF-8"?>
<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
  <rect id="rect1" x="10" y="10" width="50" height="50" fill="red"/>
  <circle id="circle1" cx="100" cy="100" r="30" fill="blue"/>
  <path id="path1" d="M150 150 L180 180 L120 180 Z" fill="green"/>
  <text id="text1" x="20" y="150" font-family="Arial" font-size="14">Sample Text</text>
</svg>""",
    "complex": """<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="400" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:red"/>
      <stop offset="100%" style="stop-color:blue"/>
    </linearGradient>
    <radialGradient id="grad2" cx="50%" cy="50%" r="50%">
      <stop offset="0%" style="stop-color:yellow"/>
      <stop offset="100%" style="stop-color:orange"/>
    </radialGradient>
  </defs>
  <g id="group1">
    <rect x="20" y="20" width="100" height="100" fill="url(#grad1)"/>
    <circle cx="200" cy="100" r="50" fill="url(#grad2)"/>
    <path d="M300 50 Q350 100 300 150 Q250 100 300 50" stroke="black" fill="none"/>
  </g>
  <g id="group2" transform="translate(50, 200)">
    <polygon points="50,0 100,50 50,100 0,50" fill="purple"/>
    <ellipse cx="150" cy="50" rx="40" ry="25" fill="cyan"/>
  </g>
</svg>""",
    "text_heavy": """<?xml version="1.0" encoding="UTF-8"?>
<svg width="500" height="300" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .title { font-size: 24px; font-weight: bold; fill: navy; }
      .body { font-size: 14px; fill: black; }
      .highlight { fill: red; font-weight: bold; }
    </style>
  </defs>
  <text id="title1" x="20" y="40" class="title">Sample Document</text>
  <text id="para1" x="20" y="70" class="body">This is a sample SVG document</text>
  <text id="para2" x="20" y="90" class="body">containing various text elements</text>
  <text id="highlight1" x="20" y="120" class="highlight">Important Text</text>
  <text id="footer1" x="20" y="280" class="body" font-size="10">Footer information</text>
</svg>""",
    "layered": """<?xml version="1.0" encoding="UTF-8"?>
<svg width="300" height="300" xmlns="http://www.w3.org/2000/svg">
  <g id="layer_background" inkscape:groupmode="layer" inkscape:label="Background">
    <rect width="300" height="300" fill="lightgray"/>
  </g>
  <g id="layer_shapes" inkscape:groupmode="layer" inkscape:label="Shapes">
    <circle id="bg_circle" cx="150" cy="150" r="100" fill="blue" opacity="0.3"/>
    <rect id="bg_rect" x="50" y="50" width="200" height="150" fill="red" opacity="0.3"/>
  </g>
  <g id="layer_overlay" inkscape:groupmode="layer" inkscape:label="Overlay">
    <text id="title" x="150" y="30" text-anchor="middle" font-size="18" fill="black">Layered Document</text>
    <circle id="fg_circle" cx="150" cy="150" r="30" fill="yellow"/>
  </g>
</svg>""",
    "empty": """<?xml version="1.0" encoding="UTF-8"?>
<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
</svg>""",
    "malformed": """<?xml version="1.0" encoding="UTF-8"?>
<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="10" width="80" height="80" fill="blue">
  <!-- Missing closing tag -->
</svg>""",
    "no_namespace": """<?xml version="1.0"?>
<svg width="100" height="100">
  <rect x="10" y="10" width="80" height="80" fill="blue"/>
</svg>""",
}


# Expected analysis results for test SVGs
EXPECTED_ANALYSIS = {
    "minimal": {
        "document_info": {"width": 100, "height": 100, "viewBox": None, "has_defs": False},
        "objects": [{"id": None, "type": "rect", "x": 10, "y": 10, "width": 80, "height": 80}],
    },
    "with_objects": {
        "document_info": {"width": 200, "height": 200, "viewBox": None, "has_defs": False},
        "objects": [
            {"id": "rect1", "type": "rect", "x": 10, "y": 10, "width": 50, "height": 50},
            {"id": "circle1", "type": "circle", "cx": 100, "cy": 100, "r": 30},
            {"id": "path1", "type": "path", "d": "M150 150 L180 180 L120 180 Z"},
            {"id": "text1", "type": "text", "x": 20, "y": 150},
        ],
    },
}


def create_temp_svg(content: str, suffix: str = ".svg") -> Path:
    """Create a temporary SVG file with given content."""
    fd, path = tempfile.mkstemp(suffix=suffix, text=True)
    file_path = Path(path)

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        return file_path
    except Exception:
        os.close(fd)
        file_path.unlink(missing_ok=True)
        raise


def create_test_svgs() -> Dict[str, Path]:
    """Create temporary files for all SVG fixtures."""
    temp_files = {}
    for name, content in SVG_FIXTURES.items():
        temp_files[name] = create_temp_svg(content, f"_{name}.svg")
    return temp_files


def cleanup_test_svgs(temp_files: Dict[str, Path]):
    """Clean up temporary SVG files."""
    for path in temp_files.values():
        path.unlink(missing_ok=True)


class SVGTestFixture:
    """Context manager for SVG test fixtures."""

    def __init__(self, fixture_name: str = "minimal"):
        self.fixture_name = fixture_name
        self.temp_file: Path = None

    def __enter__(self) -> Path:
        self.temp_file = create_temp_svg(SVG_FIXTURES[self.fixture_name])
        return self.temp_file

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_file and self.temp_file.exists():
            self.temp_file.unlink(missing_ok=True)


# Test data for vector operations
VECTOR_TEST_DATA = {
    "boolean_test": {
        "input_svg": """<?xml version="1.0"?>
<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
  <rect id="rect1" x="10" y="10" width="50" height="50" fill="red"/>
  <rect id="rect2" x="30" y="30" width="50" height="50" fill="blue"/>
</svg>""",
        "expected_union": "Single combined shape",
        "expected_intersection": "Overlapping area only",
        "expected_difference": "rect1 minus rect2 overlap",
    },
    "trace_test": {
        "description": "Simple geometric shape for tracing",
        "expected_output": "Vector path representation",
    },
    "text_test": {
        "input_text": "Hello World",
        "font_size": 24,
        "expected_paths": "Text converted to vector paths",
    },
    "optimize_test": {
        "input_svg": """<?xml version="1.0"?>
<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
  <path d="M10 10 L50 10 L50 50 L10 50 Z" fill="red"/>
  <path d="M60 60 L90 60 L90 90 L60 90 Z" fill="blue"/>
</svg>""",
        "expected_simplified": "Simplified path data",
        "expected_cleaned": "Redundant nodes removed",
    },
}


# Mock Inkscape CLI responses for testing
MOCK_INKSCAPE_RESPONSES = {
    "version": "Inkscape 1.3 (1:1.3+202307231459+0~ubuntu0.22.04.1)",
    "query_dimensions": "10,20,100,50",
    "export_success": "",
    "actions_success": "Actions executed successfully",
    "error_file_not_found": "Error: File not found or not readable",
    "error_invalid_operation": "Error: Unknown action",
    "objects_list": """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <rect id="rect1" x="10" y="20" width="100" height="50"/>
  <circle id="circle1" cx="200" cy="150" r="30"/>
</svg>""",
    "document_info": """<?xml version="1.0"?>
<svg width="400" height="300" viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
  <metadata>
    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
      <cc:Work rdf:about="">
        <dc:format>image/svg+xml</dc:format>
        <dc:title>Test Document</dc:title>
      </cc:Work>
    </rdf:RDF>
  </metadata>
</svg>""",
}


def get_mock_response(command_args: List[str]) -> str:
    """Get mock response based on command arguments."""
    cmd_str = " ".join(command_args)

    if "--version" in cmd_str:
        return MOCK_INKSCAPE_RESPONSES["version"]

    if "--query-x --query-y --query-width --query-height" in cmd_str:
        return MOCK_INKSCAPE_RESPONSES["query_dimensions"]

    if "export-filename" in cmd_str and "export-do" in cmd_str:
        return MOCK_INKSCAPE_RESPONSES["export_success"]

    if "--actions=" in cmd_str:
        return MOCK_INKSCAPE_RESPONSES["actions_success"]

    return ""  # Default empty response
