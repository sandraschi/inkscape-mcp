"""Ring-buffer activity log for MCP webapp dashboards."""

import csv
import io
import json
import time
from collections import deque
from pathlib import Path
from typing import Any
from uuid import uuid4


class ActivityLog:
    """Ring-buffer activity log with file tail fallback."""

    def __init__(self, max_entries: int = 2000):
        self.max_entries = max_entries
        self._entries: deque[dict[str, Any]] = deque(maxlen=max_entries)
        self._file_path: Path | None = None
        self._file_pos: int = 0

    def add(self, level: str, kind: str, detail: str, meta: dict | None = None) -> str:
        entry_id = f"{time.time():.6f}.{uuid4().hex[:6]}"
        self._entries.append({
            "id": entry_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + f".{int(time.time()*1e6)%1000000:06d}Z",
            "level": level.upper(),
            "kind": kind,
            "detail": detail,
            "meta": meta or {},
        })
        return entry_id

    def info(self, kind: str, detail: str, **meta) -> str:
        return self.add("INFO", kind, detail, meta)

    def warn(self, kind: str, detail: str, **meta) -> str:
        return self.add("WARNING", kind, detail, meta)

    def error(self, kind: str, detail: str, **meta) -> str:
        return self.add("ERROR", kind, detail, meta)

    def debug(self, kind: str, detail: str, **meta) -> str:
        return self.add("DEBUG", kind, detail, meta)

    def start_file_watch(self, path: Path) -> None:
        self._file_path = path
        if path.exists():
            self._file_pos = path.stat().st_size

    def _tail_file(self, lines: int = 200) -> list[str]:
        if not self._file_path or not self._file_path.exists():
            return []
        with open(self._file_path, "r", encoding="utf-8", errors="replace") as f:
            f.seek(0)
            all_lines = f.readlines()
        return [l.rstrip("\n\r") for l in all_lines[-lines:]]

    def query(
        self,
        limit: int = 50,
        offset: int = 0,
        level: str | None = None,
        kind: str | None = None,
        search: str | None = None,
        sort: str = "desc",
        after_id: str | None = None,
    ) -> dict[str, Any]:
        entries = list(self._entries)

        if after_id:
            try:
                after_time = float(after_id.split(".")[0])
                entries = [e for e in entries if float(e["id"].split(".")[0]) > after_time]
            except (ValueError, IndexError):
                pass
        if level:
            level_order = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}
            min_lvl = level_order.get(level.upper(), 1)
            entries = [e for e in entries if level_order.get(e["level"], 1) >= min_lvl]
        if kind:
            entries = [e for e in entries if e["kind"] == kind]
        if search:
            q = search.lower()
            entries = [e for e in entries if q in e["detail"].lower() or q in json.dumps(e["meta"]).lower()]

        entries.sort(key=lambda e: e["id"], reverse=(sort == "desc"))

        total = len(entries)
        page = entries[offset:offset + limit]

        if not page and self._file_path:
            file_lines = self._tail_file(limit)
            page = [
                {"id": f"file.{i}", "timestamp": "", "level": "INFO", "kind": "server",
                 "detail": line, "meta": {}}
                for i, line in enumerate(file_lines)
            ]
            total = len(page)

        return {
            "entries": page,
            "total": total,
            "limit": limit,
            "offset": offset,
            "max_entries": self.max_entries,
            "sort": sort,
        }

    def stats(self) -> dict[str, Any]:
        levels = {}
        kinds = {}
        for e in self._entries:
            levels[e["level"]] = levels.get(e["level"], 0) + 1
            kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
        return {
            "total": len(self._entries),
            "max_entries": self.max_entries,
            "levels": levels,
            "kinds": kinds,
            "file_path": str(self._file_path) if self._file_path else None,
        }

    def export(self, format: str = "json", **filters) -> str:
        result = self.query(limit=self.max_entries, **filters)
        if format == "csv":
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow(["id", "timestamp", "level", "kind", "detail", "meta"])
            for e in result["entries"]:
                w.writerow([e["id"], e["timestamp"], e["level"], e["kind"], e["detail"], json.dumps(e["meta"])])
            return buf.getvalue()
        return json.dumps(result["entries"], indent=2)

    def clear(self) -> None:
        self._entries.clear()


activity_log = ActivityLog()
