"""Unit tests for utils/inkscape_gallery.py - the online extension gallery
integration (search/install/uninstall against inkscape.org). Network calls
are not mocked here (that would just test the mock); the pure logic that
matters most - the safety gates and local filesystem bookkeeping - is."""

import json
import zipfile

import pytest

from inkscape_mcp.utils import inkscape_gallery


class TestNormalizeItem:
    def _valid_info(self, **overrides):
        info = {
            "id": "org.inkscape.extension.1",
            "name": "Test Ext",
            "author": "someone",
            "verified": True,
            "links": {"file": "https://example.com/x.zip", "html": "https://example.com/x"},
            "summary": "A test extension.",
            "version": "1.2.3",
            "tags": ["laser"],
            "stats": {"liked": 5, "downloaded": 10},
            "Inkscape Version": ["1.2", "1.3"],
        }
        info.update(overrides)
        return info

    def test_maps_all_fields(self):
        item = inkscape_gallery._normalize_item(self._valid_info())
        assert item == {
            "id": "org.inkscape.extension.1",
            "name": "Test Ext",
            "author": "someone",
            "license": "",
            "tags": ["laser"],
            "summary": "A test extension.",
            "version": "1.2.3",
            "stars": 5,
            "downloads": 10,
            "verified": True,
            "targets": ["1.2", "1.3"],
            "download_url": "https://example.com/x.zip",
            "page_url": "https://example.com/x",
        }

    def test_missing_required_field_returns_none(self):
        info = self._valid_info()
        del info["verified"]
        assert inkscape_gallery._normalize_item(info) is None

    def test_none_valued_tags_becomes_empty_list_not_none(self):
        """The real API returns "tags": null for untagged items - a bare
        .get("tags", []) would pass None through since the key IS present."""
        item = inkscape_gallery._normalize_item(self._valid_info(tags=None))
        assert item["tags"] == []

    def test_none_valued_version_falls_back_to_revisions(self):
        item = inkscape_gallery._normalize_item(
            self._valid_info(version=None, stats={"liked": 0, "downloaded": 0, "revisions": 11})
        )
        assert item["version"] == "12"

    def test_none_version_and_no_revisions_is_unknown(self):
        item = inkscape_gallery._normalize_item(self._valid_info(version=None, stats={}))
        assert item["version"] == "?"


class TestExtensionsDir:
    def test_respects_env_override(self, monkeypatch, tmp_path):
        monkeypatch.setenv("INKSCAPE_EXTENSIONS", str(tmp_path))
        assert inkscape_gallery.extensions_dir() == tmp_path


class TestSafeExtract:
    def test_extracts_normal_files(self, tmp_path):
        zip_path = tmp_path / "good.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("ext.inx", "<inkscape-extension/>")
            zf.writestr("ext.py", "print('hi')")

        dest = tmp_path / "dest"
        with zipfile.ZipFile(zip_path) as zf:
            written = inkscape_gallery._safe_extract(zf, dest)

        assert sorted(written) == ["ext.inx", "ext.py"]
        assert (dest / "ext.inx").read_text() == "<inkscape-extension/>"

    def test_rejects_path_traversal(self, tmp_path):
        zip_path = tmp_path / "evil.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("../../evil.py", "print('pwned')")

        dest = tmp_path / "dest"
        with zipfile.ZipFile(zip_path) as zf:
            with pytest.raises(ValueError, match="Unsafe path"):
                inkscape_gallery._safe_extract(zf, dest)


class TestInstallExtension:
    @pytest.mark.asyncio
    async def test_unverified_without_allow_flag_raises_before_any_download(self, monkeypatch):
        """The permission gate must short-circuit before touching the
        network - assert nothing under httpx is even imported/called by
        making the module's httpx unusable and confirming we never get far
        enough to need it."""
        monkeypatch.setattr(inkscape_gallery, "httpx", None)

        with pytest.raises(PermissionError, match="not a reviewed/verified extension"):
            await inkscape_gallery.install_extension(
                "some.id", "Some Ext", "https://example.com/x.zip", verified=False
            )

    @pytest.mark.asyncio
    async def test_missing_download_url_raises_value_error(self):
        with pytest.raises(ValueError, match="download_url is required"):
            await inkscape_gallery.install_extension("some.id", "Some Ext", "", verified=True)


class TestManagedExtensions:
    def test_list_managed_empty_when_no_marker(self, monkeypatch, tmp_path):
        monkeypatch.setenv("INKSCAPE_EXTENSIONS", str(tmp_path))
        assert inkscape_gallery.list_managed_extensions() == {"extensions": []}

    def test_list_managed_reads_marker_file(self, monkeypatch, tmp_path):
        monkeypatch.setenv("INKSCAPE_EXTENSIONS", str(tmp_path))
        tmp_path.mkdir(parents=True, exist_ok=True)
        marker = tmp_path / inkscape_gallery._MANAGED_MARKER
        marker.write_text(
            json.dumps(
                {"ext.1": {"name": "Ext One", "files": ["a.py"], "dir": str(tmp_path / "ext.1")}}
            )
        )

        result = inkscape_gallery.list_managed_extensions()

        assert result == {
            "extensions": [
                {
                    "id": "ext.1",
                    "name": "Ext One",
                    "files": ["a.py"],
                    "dir": str(tmp_path / "ext.1"),
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_uninstall_unknown_id_raises_key_error(self, monkeypatch, tmp_path):
        monkeypatch.setenv("INKSCAPE_EXTENSIONS", str(tmp_path))
        with pytest.raises(KeyError, match="was not installed by this server"):
            await inkscape_gallery.uninstall_extension("never.installed")

    @pytest.mark.asyncio
    async def test_uninstall_removes_files_and_updates_marker(self, monkeypatch, tmp_path):
        monkeypatch.setenv("INKSCAPE_EXTENSIONS", str(tmp_path))
        pkg_dir = tmp_path / "ext.1"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "a.py").write_text("x")
        marker = tmp_path / inkscape_gallery._MANAGED_MARKER
        marker.write_text(
            json.dumps({"ext.1": {"name": "Ext One", "files": ["a.py"], "dir": str(pkg_dir)}})
        )

        result = await inkscape_gallery.uninstall_extension("ext.1")

        assert result["id"] == "ext.1"
        assert not pkg_dir.exists()
        assert inkscape_gallery.list_managed_extensions() == {"extensions": []}
