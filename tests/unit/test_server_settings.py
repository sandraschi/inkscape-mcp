"""Unit tests for services/server_settings.py - the persisted-override store
backing /api/settings/server (inkscape_path/ollama_base_url/ollama_model take
effect live; mcp_port only on next restart, see app.py's route docstring)."""

from inkscape_mcp.services import server_settings


def test_load_returns_empty_dict_when_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr(server_settings, "_SETTINGS_PATH", tmp_path / "server_settings.json")
    assert server_settings.load() == {}


def test_save_persists_and_load_round_trips(tmp_path, monkeypatch):
    monkeypatch.setattr(server_settings, "_SETTINGS_PATH", tmp_path / "server_settings.json")

    result = server_settings.save(ollama_base_url="http://127.0.0.1:9999")

    assert result == {"ollama_base_url": "http://127.0.0.1:9999"}
    assert server_settings.load() == {"ollama_base_url": "http://127.0.0.1:9999"}


def test_save_merges_with_existing_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(server_settings, "_SETTINGS_PATH", tmp_path / "server_settings.json")
    server_settings.save(inkscape_path="/opt/inkscape/inkscape")

    server_settings.save(ollama_model="qwen3:32b")

    assert server_settings.load() == {
        "inkscape_path": "/opt/inkscape/inkscape",
        "ollama_model": "qwen3:32b",
    }


def test_save_with_none_or_empty_removes_field(tmp_path, monkeypatch):
    monkeypatch.setattr(server_settings, "_SETTINGS_PATH", tmp_path / "server_settings.json")
    server_settings.save(ollama_base_url="http://127.0.0.1:9999", ollama_model="qwen3:32b")

    result = server_settings.save(ollama_base_url=None, ollama_model="")

    assert result == {}
    assert server_settings.load() == {}


def test_save_returns_full_merged_state_not_just_new_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(server_settings, "_SETTINGS_PATH", tmp_path / "server_settings.json")
    server_settings.save(inkscape_path="/opt/inkscape/inkscape")

    result = server_settings.save(mcp_port="11099")

    assert result == {"inkscape_path": "/opt/inkscape/inkscape", "mcp_port": "11099"}
