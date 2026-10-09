"""
Unit tests for the app.py helpers added/fixed during the 2026-09-07 LLM
vendoring pass: _call_mcp_tool (the to_mcp_result() unwrap that had a real
bug - a truthy structured_content dict was being read as an is_error flag,
so any successful tool call with data reported as failed), _ollama_tool_schemas
(builds the agentic chat tool-calling loop's tool list), and _filter_logs
(the /api/logs search/level/kind filtering). app.py itself is otherwise
untested (0% - its REST routes are defined as closures inside
register_rest_api(mcp, config), which needs a real or heavily-mocked FastMCP
instance to exercise via a client; out of scope here). These three are
plain module-level functions and the highest-risk logic from today's work,
so they're covered directly instead.
"""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from mcp.types import CallToolResult
from mcp.types import TextContent

from inkscape_mcp.app import _call_mcp_tool
from inkscape_mcp.app import _filter_logs
from inkscape_mcp.app import _ollama_tool_schemas


def _mcp_with_call_tool(mcp_result_factory):
    """A fake `mcp` whose call_tool() returns an object with a
    to_mcp_result() producing whatever the caller wants for this test."""
    fake_tool_result = MagicMock()
    fake_tool_result.to_mcp_result = MagicMock(side_effect=mcp_result_factory)
    mcp = MagicMock()
    mcp.call_tool = AsyncMock(return_value=fake_tool_result)
    return mcp


class TestCallMcpTool:
    @pytest.mark.asyncio
    async def test_call_tool_result_success_with_structured_content(self):
        """CallToolResult path: isError=False, real data -> success."""
        mcp = _mcp_with_call_tool(
            lambda: CallToolResult(
                content=[TextContent(type="text", text="ignored")],
                structuredContent={"answer": 42},
                isError=False,
            )
        )
        outcome = await _call_mcp_tool(mcp, "some_tool", {"x": 1})

        assert outcome == {"success": True, "data": {"answer": 42}, "error": None}
        mcp.call_tool.assert_awaited_once_with("some_tool", {"x": 1})

    @pytest.mark.asyncio
    async def test_call_tool_result_real_error(self):
        """CallToolResult path: isError=True -> the ONLY shape that should
        ever report failure with populated data. Reads the error text from
        content[0]."""
        mcp = _mcp_with_call_tool(
            lambda: CallToolResult(
                content=[TextContent(type="text", text="boom: file not found")],
                isError=True,
            )
        )
        outcome = await _call_mcp_tool(mcp, "some_tool", {})

        assert outcome["success"] is False
        assert outcome["error"] == "boom: file not found"

    @pytest.mark.asyncio
    async def test_tuple_shape_with_truthy_structured_content_is_not_an_error(self):
        """Regression test for the actual bug fixed 2026-09-07: FastMCP's
        ToolResult.to_mcp_result() can return a bare (content, structured)
        tuple with NO error signal at all. structured_content is a dict, not
        a bool - a non-empty dict is truthy, so treating it as is_error
        (the old code: `is_error = mcp_result[1]`) marked every successful
        tool call that returned real data as a failure. This must succeed."""
        content = [TextContent(type="text", text="ignored")]
        structured = {"server": {"status": "running"}, "tools": {"file": "available"}}
        mcp = _mcp_with_call_tool(lambda: (content, structured))

        outcome = await _call_mcp_tool(mcp, "inkscape_system", {"operation": "status"})

        assert outcome["success"] is True
        assert outcome["data"] == structured
        assert outcome["error"] is None

    @pytest.mark.asyncio
    async def test_tuple_shape_with_empty_dict_structured_content(self):
        """An empty dict is also truthy-adjacent territory to get wrong -
        `{}` must still count as real (if empty) structured data, not as an
        error and not as "no data" (success requires data is not None)."""
        content = [TextContent(type="text", text="ignored")]
        mcp = _mcp_with_call_tool(lambda: (content, {}))

        outcome = await _call_mcp_tool(mcp, "some_tool", {})

        assert outcome["success"] is True
        assert outcome["data"] == {}

    @pytest.mark.asyncio
    async def test_bare_content_list_falls_back_to_json_parsing_text(self):
        """No CallToolResult, no tuple - just a bare content list. data is
        parsed from the first content item's text as JSON."""
        mcp = _mcp_with_call_tool(lambda: [TextContent(type="text", text='{"parsed": true}')])

        outcome = await _call_mcp_tool(mcp, "some_tool", {})

        assert outcome["success"] is True
        assert outcome["data"] == {"parsed": True}

    @pytest.mark.asyncio
    async def test_bare_content_list_non_json_text_wrapped_as_output(self):
        mcp = _mcp_with_call_tool(lambda: [TextContent(type="text", text="plain text, not json")])

        outcome = await _call_mcp_tool(mcp, "some_tool", {})

        assert outcome["success"] is True
        assert outcome["data"] == {"output": "plain text, not json"}

    @pytest.mark.asyncio
    async def test_call_tool_raising_is_caught_and_reported(self):
        mcp = MagicMock()
        mcp.call_tool = AsyncMock(side_effect=RuntimeError("tool crashed"))

        outcome = await _call_mcp_tool(mcp, "some_tool", {})

        assert outcome == {"success": False, "data": None, "error": "tool crashed"}

    @pytest.mark.asyncio
    async def test_empty_content_list_with_no_structured_content_is_not_success(self):
        """No content, no structured data, no error flag: data stays None,
        so success must be False (success requires data is not None) even
        though is_error was never set."""
        mcp = _mcp_with_call_tool(lambda: ([], None))

        outcome = await _call_mcp_tool(mcp, "some_tool", {})

        assert outcome["success"] is False
        assert outcome["data"] is None


class TestOllamaToolSchemas:
    @pytest.mark.asyncio
    async def test_builds_openai_style_schemas_from_registered_tools(self):
        fake_tool = MagicMock()
        fake_tool.name = "inkscape_vector"
        fake_tool.description = "Vector operations."
        fake_tool.parameters = {"type": "object", "properties": {"operation": {"type": "string"}}}

        mcp = MagicMock()
        mcp.list_tools = AsyncMock(return_value=[fake_tool])

        schemas = await _ollama_tool_schemas(mcp)

        assert schemas == [
            {
                "type": "function",
                "function": {
                    "name": "inkscape_vector",
                    "description": "Vector operations.",
                    "parameters": {
                        "type": "object",
                        "properties": {"operation": {"type": "string"}},
                    },
                },
            }
        ]

    @pytest.mark.asyncio
    async def test_list_tools_failure_returns_empty_list_not_raise(self):
        mcp = MagicMock()
        mcp.list_tools = AsyncMock(side_effect=RuntimeError("registry unavailable"))

        schemas = await _ollama_tool_schemas(mcp)

        assert schemas == []

    @pytest.mark.asyncio
    async def test_description_none_becomes_empty_string(self):
        fake_tool = MagicMock()
        fake_tool.name = "list_local_models"
        fake_tool.description = None
        fake_tool.parameters = {"type": "object", "properties": {}}

        mcp = MagicMock()
        mcp.list_tools = AsyncMock(return_value=[fake_tool])

        schemas = await _ollama_tool_schemas(mcp)

        assert schemas[0]["function"]["description"] == ""


class TestFilterLogs:
    LOGS = [
        {
            "id": "1",
            "level": "INFO",
            "kind": "server",
            "detail": "REST bridge mounted",
            "meta": {"logger": "app"},
        },
        {
            "id": "2",
            "level": "ERROR",
            "kind": "tool_call",
            "detail": "trace_image failed",
            "meta": {"logger": "vector"},
        },
        {
            "id": "3",
            "level": "INFO",
            "kind": "tool_call",
            "detail": "list_models ok",
            "meta": {"logger": "llm"},
        },
    ]

    def test_no_filters_returns_everything(self):
        assert _filter_logs(self.LOGS) == self.LOGS

    def test_filter_by_level(self):
        result = _filter_logs(self.LOGS, level="ERROR")
        assert [e["id"] for e in result] == ["2"]

    def test_filter_by_kind(self):
        result = _filter_logs(self.LOGS, kind="tool_call")
        assert [e["id"] for e in result] == ["2", "3"]

    def test_search_matches_detail(self):
        result = _filter_logs(self.LOGS, search="trace_image")
        assert [e["id"] for e in result] == ["2"]

    def test_search_matches_meta_not_just_detail(self):
        """meta search was added specifically when the orphaned backend's
        better logging.py was ported before deletion - detail text alone
        wouldn't match a search on the logger name."""
        result = _filter_logs(self.LOGS, search="llm")
        assert [e["id"] for e in result] == ["3"]

    def test_search_is_case_insensitive(self):
        result = _filter_logs(self.LOGS, search="REST")
        assert [e["id"] for e in result] == ["1"]

    def test_combined_filters(self):
        result = _filter_logs(self.LOGS, level="INFO", kind="tool_call")
        assert [e["id"] for e in result] == ["3"]

    def test_no_matches_returns_empty(self):
        assert _filter_logs(self.LOGS, level="DEBUG") == []
