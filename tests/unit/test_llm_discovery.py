"""
Unit tests for tools/llm_discovery.py (list_local_models, llm_ops).

Vendored/added 2026-09-07 as part of the LLM local+cloud provider surface
(SETTINGS_LLM.md). These were at 17% coverage - untested since the day they
landed - so this file targets exactly that gap rather than the rest of the
still-untested app.py REST bridge.
"""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from inkscape_mcp.tools.llm_discovery import list_local_models
from inkscape_mcp.tools.llm_discovery import llm_ops


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class TestListLocalModels:
    @pytest.mark.asyncio
    async def test_both_reachable(self):
        ollama_resp = _FakeResponse(
            200, {"models": [{"name": "gemma4:12b"}, {"name": "qwen3:32b"}]}
        )
        lmstudio_resp = _FakeResponse(200, {"data": [{"id": "local-model-1"}]})
        with patch(
            "httpx.AsyncClient.get",
            AsyncMock(side_effect=[ollama_resp, lmstudio_resp]),
        ):
            result = await list_local_models()

        assert result["success"] is True
        assert result["result"]["ollama"] == ["gemma4:12b", "qwen3:32b"]
        assert result["result"]["lm_studio"] == ["local-model-1"]
        assert result["result"]["errors"] == []
        assert "2 Ollama" in result["summary"]
        assert "1 LM Studio" in result["summary"]

    @pytest.mark.asyncio
    async def test_both_unreachable(self):
        with patch(
            "httpx.AsyncClient.get",
            AsyncMock(side_effect=ConnectionError("refused")),
        ):
            result = await list_local_models()

        # Discovery failures are non-fatal: the tool still reports success
        # with empty lists and a diagnostic string per endpoint, never raises.
        assert result["success"] is True
        assert result["result"]["ollama"] == []
        assert result["result"]["lm_studio"] == []
        assert len(result["result"]["errors"]) == 2
        assert any("Ollama" in e for e in result["result"]["errors"])
        assert any("LM Studio" in e for e in result["result"]["errors"])

    @pytest.mark.asyncio
    async def test_non_200_status_treated_as_no_models(self):
        with patch(
            "httpx.AsyncClient.get",
            AsyncMock(return_value=_FakeResponse(500, {})),
        ):
            result = await list_local_models()

        assert result["result"]["ollama"] == []
        assert result["result"]["lm_studio"] == []


class TestLlmOps:
    @pytest.mark.asyncio
    async def test_list_models_delegates_to_list_local_models(self):
        with patch(
            "httpx.AsyncClient.get",
            AsyncMock(return_value=_FakeResponse(200, {"models": []})),
        ):
            result = await llm_ops(operation="list_models")

        assert result["success"] is True
        assert result["operation"] == "list_models"
        assert "ollama" in result
        assert "lm_studio" in result

    @pytest.mark.asyncio
    async def test_vram_returns_gpu_list(self):
        with patch(
            "inkscape_mcp.tools.llm_discovery.llm_engine.gpu_vram", return_value=[{"index": 0}]
        ):
            result = await llm_ops(operation="vram")

        assert result == {"success": True, "operation": "vram", "gpus": [{"index": 0}]}

    @pytest.mark.asyncio
    async def test_non_ollama_provider_rejected_for_engine_ops(self):
        for op in ("loaded", "switch_model", "unload_all"):
            result = await llm_ops(operation=op, provider="gemini")
            assert result["success"] is False
            assert "gemini" in result["error"]
            assert "ollama" in result["message"]
            assert result["recovery_options"]

    @pytest.mark.asyncio
    async def test_switch_model_rejects_empty_model(self):
        result = await llm_ops(operation="switch_model", provider="ollama", model="   ")

        assert result["success"] is False
        assert result["error"] == "empty model"
        assert "list_models" in result["recovery_options"][0]

    @pytest.mark.asyncio
    async def test_switch_model_success_delegates_to_engine(self):
        fake_switch = {"evicted": ["old:model"], "warmed": True, "engine": True}
        with patch(
            "inkscape_mcp.tools.llm_discovery.llm_engine.switch_ollama_model",
            AsyncMock(return_value=fake_switch),
        ) as mock_switch:
            result = await llm_ops(
                operation="switch_model",
                provider="ollama",
                model="new:model",
                endpoint="http://x:1/",
            )

        mock_switch.assert_awaited_once_with("new:model", "http://x:1")
        assert result["success"] is True
        assert result["model"] == "new:model"
        assert result["evicted"] == ["old:model"]

    @pytest.mark.asyncio
    async def test_unload_all_evicts_everything(self):
        fake_switch = {"evicted": ["a", "b"], "warmed": False, "engine": True}
        with patch(
            "inkscape_mcp.tools.llm_discovery.llm_engine.switch_ollama_model",
            AsyncMock(return_value=fake_switch),
        ) as mock_switch:
            result = await llm_ops(operation="unload_all", provider="ollama")

        mock_switch.assert_awaited_once_with("", "http://localhost:11434")
        assert result["evicted"] == ["a", "b"]

    @pytest.mark.asyncio
    async def test_loaded_delegates_to_engine(self):
        fake_loaded = {
            "engine": True,
            "models": [{"name": "gemma4:12b", "size_vram_mb": 8000, "expires_at": ""}],
        }
        with patch(
            "inkscape_mcp.tools.llm_discovery.llm_engine.ollama_loaded",
            AsyncMock(return_value=fake_loaded),
        ):
            result = await llm_ops(operation="loaded", provider="ollama")

        assert result["success"] is True
        assert result["models"][0]["name"] == "gemma4:12b"
