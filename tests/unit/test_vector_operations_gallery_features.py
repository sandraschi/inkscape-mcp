"""Unit tests for the gradient/pattern/XML-editor/text-on-path/flow-text/
symbol operations added to inkscape_vector - all pure ElementTree edits, no
Inkscape CLI involved, so tested directly against real temp SVG files."""

import pytest

from inkscape_mcp.tools.vector_operations import inkscape_vector

BASE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">
  <path id="wavepath" d="M 0,100 Q 100,50 200,100" fill="none"/>
  <rect id="box1" x="0" y="0" width="100" height="100" fill="none"/>
  <circle id="circle1" cx="50" cy="50" r="10" fill="blue"/>
</svg>
"""


@pytest.fixture
def base_svg(tmp_path):
    p = tmp_path / "base.svg"
    p.write_text(BASE_SVG, encoding="utf-8")
    return p


class TestCreateGradient:
    @pytest.mark.asyncio
    async def test_linear_gradient_returns_usable_fill(self, base_svg):
        result = await inkscape_vector(
            operation="create_gradient",
            input_path=str(base_svg),
            output_path=str(base_svg),
            object_id="grad1",
            params={
                "type": "linear",
                "stops": [{"offset": "0%", "color": "#f00"}, {"offset": "100%", "color": "#00f"}],
            },
        )
        assert result["success"] is True
        assert result["data"]["fill"] == "url(#grad1)"
        assert "<linearGradient" in base_svg.read_text()
        assert 'id="grad1"' in base_svg.read_text()

    @pytest.mark.asyncio
    async def test_radial_gradient(self, base_svg):
        result = await inkscape_vector(
            operation="create_gradient",
            input_path=str(base_svg),
            output_path=str(base_svg),
            params={"type": "radial", "stops": [{"offset": 0, "color": "#fff"}]},
        )
        assert result["success"] is True
        assert "<radialGradient" in base_svg.read_text()

    @pytest.mark.asyncio
    async def test_missing_stops_fails_cleanly(self, base_svg):
        result = await inkscape_vector(
            operation="create_gradient",
            input_path=str(base_svg),
            output_path=str(base_svg),
            params={},
        )
        assert result["success"] is False
        assert "stops" in result["message"]


class TestCreatePattern:
    @pytest.mark.asyncio
    async def test_creates_pattern_with_tile_content(self, base_svg):
        result = await inkscape_vector(
            operation="create_pattern",
            input_path=str(base_svg),
            output_path=str(base_svg),
            object_id="pat1",
            params={
                "width": 5,
                "height": 5,
                "content": '<circle cx="2" cy="2" r="1" fill="green"/>',
            },
        )
        assert result["success"] is True
        assert result["data"]["fill"] == "url(#pat1)"
        svg_text = base_svg.read_text()
        assert '<pattern id="pat1"' in svg_text
        assert "<circle" in svg_text  # tile content merged in

    @pytest.mark.asyncio
    async def test_invalid_content_fails_cleanly(self, base_svg):
        result = await inkscape_vector(
            operation="create_pattern",
            input_path=str(base_svg),
            output_path=str(base_svg),
            params={"content": "<not-closed>"},
        )
        assert result["success"] is False


class TestAttributes:
    @pytest.mark.asyncio
    async def test_set_then_get_attributes_round_trips(self, base_svg):
        set_result = await inkscape_vector(
            operation="set_attributes",
            input_path=str(base_svg),
            output_path=str(base_svg),
            object_id="circle1",
            params={"fill": "red", "style.opacity": "0.5"},
        )
        assert set_result["success"] is True

        get_result = await inkscape_vector(
            operation="get_attributes", input_path=str(base_svg), object_id="circle1"
        )
        assert get_result["success"] is True
        assert get_result["data"]["attributes"]["fill"] == "red"
        assert get_result["data"]["style"]["opacity"] == "0.5"
        assert get_result["data"]["tag"] == "circle"

    @pytest.mark.asyncio
    async def test_get_attributes_unknown_id(self, base_svg):
        result = await inkscape_vector(
            operation="get_attributes", input_path=str(base_svg), object_id="nope"
        )
        assert result["success"] is False


class TestTextOnPath:
    @pytest.mark.asyncio
    async def test_creates_text_path_element(self, base_svg):
        result = await inkscape_vector(
            operation="text_on_path",
            input_path=str(base_svg),
            output_path=str(base_svg),
            ref_id="wavepath",
            params={"content": "Hello", "font_size": 12},
        )
        assert result["success"] is True
        svg_text = base_svg.read_text()
        assert "<textPath" in svg_text
        assert "Hello" in svg_text

    @pytest.mark.asyncio
    async def test_missing_ref_id_fails(self, base_svg):
        result = await inkscape_vector(
            operation="text_on_path",
            input_path=str(base_svg),
            output_path=str(base_svg),
            params={"content": "x"},
        )
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_nonexistent_path_id_fails(self, base_svg):
        result = await inkscape_vector(
            operation="text_on_path",
            input_path=str(base_svg),
            output_path=str(base_svg),
            ref_id="doesnotexist",
            params={"content": "x"},
        )
        assert result["success"] is False


class TestFlowText:
    @pytest.mark.asyncio
    async def test_creates_shape_inside_text(self, base_svg):
        result = await inkscape_vector(
            operation="flow_text",
            input_path=str(base_svg),
            output_path=str(base_svg),
            ref_id="box1",
            params={"content": "Some flowed text", "font_size": 10},
        )
        assert result["success"] is True
        svg_text = base_svg.read_text()
        assert "shape-inside:url(#box1)" in svg_text
        assert "Some flowed text" in svg_text


class TestSymbols:
    @pytest.mark.asyncio
    async def test_create_symbol_then_use_it(self, base_svg):
        create_result = await inkscape_vector(
            operation="create_symbol",
            input_path=str(base_svg),
            output_path=str(base_svg),
            object_id="icon1",
            params={"content": '<path d="M0,0 L1,1"/>', "viewBox": "0 0 1 1"},
        )
        assert create_result["success"] is True
        assert '<symbol id="icon1"' in base_svg.read_text()

        use_result = await inkscape_vector(
            operation="use_symbol",
            input_path=str(base_svg),
            output_path=str(base_svg),
            ref_id="icon1",
            params={"x": 10, "y": 20, "width": 5, "height": 5},
        )
        assert use_result["success"] is True
        svg_text = base_svg.read_text()
        assert 'href="#icon1"' in svg_text
        assert 'x="10"' in svg_text

    @pytest.mark.asyncio
    async def test_use_symbol_missing_target_fails(self, base_svg):
        result = await inkscape_vector(
            operation="use_symbol",
            input_path=str(base_svg),
            output_path=str(base_svg),
            ref_id="ghost",
            params={},
        )
        assert result["success"] is False
