#!/usr/bin/env python3
"""CUA webapp test — pre-Tauri / no-Tauri webapp smoke test.

Same idea as cua-smoke.py but WITHOUT the NSIS install/uninstall phases:
spins up backend + frontend (via the repo's start.ps1), waits for the
"Connected" badge (webapps show "Connecting..." for a few seconds while the
backend comes up), then walks every sidebar page discovered from the live UI.

CUA_WEBAPP_TEST_VERSION = 2 (v2: pages are discovered, not configured; no stale page list)

Phases:
    1. Kill stale processes (backend/frontend ports)
    2. Start stack (start.ps1 -Headless if supported, else direct spawn)
    3. Wait for backend health (config backend_port / health_path)
    4. Wait for frontend (config frontend_port) HTTP 200
    5. Open browser to frontend URL
    6. Wait for "Connected" badge (OCR, retry w/ timeout — the wrinkle)
    7. Nav walk: discover sidebar links from the UI, invoke each, per-page screenshots,
       fail if a page does not visibly change
    8. Diagnostics check (if backend exposes /api/v1/diagnostics)
    9. Cleanup: kill spawned processes
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from contextlib import suppress
from pathlib import Path

CUA_WEBAPP_TEST_VERSION = 2
DEFAULT_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cua-nsis-config.json")
_CONFIG = {}

CONNECTED_KEYWORDS = ["connected", "system online", "online", "ready"]
CONNECTING_KEYWORDS = ["connecting", "waiting for backend", "connecting..."]
FAIL_KEYWORDS = [
    "404",
    "not found",
    "error",
    "timeout",
    "internal server error",
    "failed to fetch",
    "cannot connect",
    "connection refused",
]


def load_config(path=None):
    p = path or DEFAULT_CONFIG
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def cfg(key, default=""):
    return _CONFIG.get(key, default)


_CONFIG = load_config()

BACKEND_PORT = int(cfg("backend_port", 10700))
FRONTEND_PORT = int(cfg("frontend_port", 0))
BACKEND_URL = f"http://127.0.0.1:{BACKEND_PORT}"
HEALTH_PATH = cfg("health_path") or cfg("backend_health_path", "/api/v1/health")
PRODUCT_NAME = cfg("product_name", "App")
WINDOW_TITLE_RE = cfg("window_title_re") or cfg("window_title", PRODUCT_NAME)
CONNECTED_TEXT = cfg("connected_badge_text", "connected")
CONNECTED_TIMEOUT = int(cfg("connected_timeout", 60))
PROCESS_NAMES = cfg("backend_process_names", [])


def log(msg):
    print(f"  [cua-webapp] {msg}", flush=True)


def fatal(msg):
    print(f"  [cua-webapp] FATAL: {msg}", flush=True)
    sys.exit(1)


def kill_stale():
    """Kill processes holding backend/frontend ports (via temp PS script)."""
    ports = [str(p) for p in (BACKEND_PORT, FRONTEND_PORT) if p]
    if not ports:
        return
    ps = (
        "\n".join(
            [
                "Get-NetTCPConnection -LocalPort " + p + " -ErrorAction SilentlyContinue "
                "| ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"
                for p in ports
            ]
        )
        + "\nexit 0\n"
    )
    import tempfile

    fd, path = tempfile.mkstemp(suffix=".ps1")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(ps)
        subprocess.run(  # noqa: S603 - fixed literal command array, local test script
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", path],  # noqa: S607 - powershell on PATH by fleet standard
            capture_output=True,
            timeout=15,
        )
    finally:
        with suppress(OSError):
            os.remove(path)
    log(f"Cleared ports {', '.join(ports)}")
    time.sleep(2)
    return True


def start_stack():
    """Start backend + frontend via start.ps1 (prefer -Headless), else direct spawn."""
    repo_root = Path(__file__).resolve().parent.parent
    start_ps1 = repo_root / "start.ps1"

    # Try start.ps1 -Headless first (fleet standard has this switch)
    if start_ps1.exists():
        try:
            log("Starting stack via start.ps1 -Headless...")
            # Fleet unified launcher requires probe mode env (same as fleet-webapp-start-probe.ps1)
            env = dict(os.environ)
            for v in ("VIRTUAL_ENV", "PYTHONPATH", "UV_PROJECT_ENVIRONMENT"):
                env.pop(v, None)
            env["FLEET_PROBE_RUN"] = "1"
            env["FLEET_PROBE_LOG_DIR"] = str(repo_root / "cua-reports" / "logs")
            subprocess.Popen(  # noqa: S603 - fixed literal command array, local test script
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",  # noqa: S607 - powershell on PATH by fleet standard
                    "-File",
                    str(start_ps1),
                    "-Headless",
                ],
                cwd=str(repo_root),
                stdin=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
                env=env,
            )
            return True
        except Exception as e:
            log(f"start.ps1 -Headless failed ({e}), falling back to direct spawn")

    # Fallback: direct spawn of backend via uv + python module (config: backend_module)
    module = cfg("backend_module", "")
    if not module:
        log("No backend_module in config — cannot direct-spawn backend")
        return False
    log(f"Direct spawn fallback: python -m {module}")
    subprocess.Popen(  # noqa: S603 - fixed literal command array, local test script
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",  # noqa: S607 - powershell on PATH by fleet standard
            f"Set-Location '{repo_root}'; $env:BACKEND_PORT='{BACKEND_PORT}'; uv run python -m {module}",
        ],
        cwd=str(repo_root),
        stdin=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    return True


def wait_backend():
    """Poll backend health endpoint until 200 or timeout."""
    url = f"{BACKEND_URL}{HEALTH_PATH}"
    deadline = time.time() + int(cfg("backend_timeout", 30))
    while time.time() < deadline:
        try:
            r = urllib.request.urlopen(url, timeout=3)  # noqa: S310 - localhost health poll from config
            if r.status == 200:
                log(f"Backend ready ({url})")
                return True
        except Exception:  # noqa: S110 - poll loop, backoff handled by time.sleep below
            pass
        time.sleep(2)
    log(f"Backend not reachable at {url}")
    return False


def wait_frontend():
    """Poll frontend port until HTTP 200 or timeout."""
    if not FRONTEND_PORT:
        log("No frontend_port in config — skipping frontend wait")
        return True
    url = f"http://127.0.0.1:{FRONTEND_PORT}"
    deadline = time.time() + int(cfg("frontend_timeout", 30))
    while time.time() < deadline:
        try:
            r = urllib.request.urlopen(url, timeout=3)
            if r.status == 200:
                log(f"Frontend ready ({url})")
                return True
        except Exception:  # noqa: S110 - poll loop, backoff handled by time.sleep below
            pass
        time.sleep(2)
    log(f"Frontend not reachable at {url}")
    return False


def open_browser():
    """Open the webapp in the default browser."""
    if not FRONTEND_PORT:
        return True
    url = f"http://127.0.0.1:{FRONTEND_PORT}"
    try:
        subprocess.Popen(["cmd", "/c", "start", "", url])  # noqa: S603, S607 - fixed literal, cmd.exe on PATH by design
        log(f"Opened browser: {url}")
        return True
    except Exception as e:
        log(f"Browser open failed: {e}")
        return False


def find_webapp_window():
    """Find the browser window showing the webapp (by title regex, prefer one with links)."""
    try:
        from pywinauto import Desktop

        desktop = Desktop(backend="uia")
        candidates = []
        for w in desktop.windows():
            title = (w.window_text() or "").lower()
            if re.search(WINDOW_TITLE_RE.lower(), title):
                candidates.append(w)
        if not candidates:
            return None
        # Prefer the window whose UIA tree has hyperlinks (the browser page),
        # not a bare titlebar stub.
        for w in candidates:
            try:
                if w.descendants(control_type="Hyperlink"):
                    return w
            except Exception:  # noqa: S110 - try each candidate, fall through on failure
                pass
        return candidates[0]
    except Exception:
        return None


def wait_connected_badge(timeout=None):
    """Wait for the Connected badge via OCR. The wrinkle: webapps show
    'Connecting...' for a few seconds while the backend comes up."""
    timeout = timeout or CONNECTED_TIMEOUT
    deadline = time.time() + timeout
    win = None
    text = ""
    connected_kw = CONNECTED_TEXT.lower()
    while time.time() < deadline:
        if win is None:
            win = find_webapp_window()
        if win:
            try:
                win.set_focus()
                time.sleep(0.5)
                img = win.capture_as_image()
                # OCR via tesseract
                try:
                    import pytesseract

                    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
                    text = (pytesseract.image_to_string(img) or "").lower()
                except Exception:
                    text = ""
                if connected_kw in text or any(k in text for k in CONNECTED_KEYWORDS):
                    log(f"Connected badge found after {int(time.time() - (deadline - timeout))}s")
                    return win, text
                # If we see connecting text, keep waiting (not an error)
                if any(k in text for k in CONNECTING_KEYWORDS):
                    log("  Still connecting...")
            except Exception:  # noqa: S110 - OCR/window failures are retried by the poll loop
                pass
        time.sleep(2)
    if win is None:
        log(f"No window matching '{WINDOW_TITLE_RE}' found in {timeout}s")
    else:
        log(f"Connected badge not found in {timeout}s (last OCR: '{text[:80]}')")
    return win, text


def _sidebar_links(win):
    """Sidebar links read from the live UI, top to bottom, as [(label, element)].

    The sidebar is the largest group of visible, labelled Hyperlinks sharing one x-extent,
    so in-page links elsewhere on the page are not mistaken for navigation.
    """
    columns = {}
    for el in win.descendants(control_type="Hyperlink"):
        try:
            label = (el.window_text() or "").strip()
            if not label or not el.is_visible():
                continue
            rect = el.rectangle()
        except Exception:  # noqa: S112 - element vanished mid-scan
            continue
        columns.setdefault((rect.left, rect.right), []).append((rect.top, label, el))
    if not columns:
        return []
    seen, links = set(), []
    for _top, label, el in sorted(max(columns.values(), key=len), key=lambda item: item[0]):
        if label not in seen:
            seen.add(label)
            links.append((label, el))
    return links


def _invoke(el):
    """Navigate without the mouse. UIA Invoke also works for links scrolled out of view
    (a tall sidebar's last entries sit below the window edge, where a click misses)."""
    try:
        el.invoke()
    except Exception:
        el.click_input()


def _log_nav_changes(output_dir, labels):
    """Say when pages were added or removed since the last run, then remember this run."""
    path = os.path.join(output_dir, "nav-last.json")
    try:
        with open(path, encoding="utf-8") as f:
            before = json.load(f)
    except (OSError, ValueError):
        before = None
    if before is not None:
        added = [label for label in labels if label not in before]
        removed = [label for label in before if label not in labels]
        if added or removed:
            log(f"Sidebar changed since last run: added {added}, removed {removed}")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(labels, f)


def nav_click_through(output_dir, win):
    """Walk every page the sidebar actually offers. There is no page list to maintain.

    Pages are discovered from the live UI on each run, so adding or deleting a sidebar entry
    needs no config change. It fails (never passes vacuously) when no sidebar is found or a
    page does not visibly change after navigation. Optional config `nav_must_include`
    (labels) guards against discovery regressions; legacy `nav_routes` is ignored.
    """
    os.makedirs(output_dir, exist_ok=True)
    with suppress(Exception):  # maximize is best-effort
        win.maximize()
        time.sleep(1)

    labels = [label for label, _el in _sidebar_links(win)]
    if not labels:
        log("FAIL: no sidebar links discovered (icon-only collapsed sidebar, or nav is not <a> links)")
        return False
    log(f"Discovered {len(labels)} sidebar pages: {', '.join(labels)}")
    if cfg("nav_routes"):
        log("config nav_routes is ignored: pages are discovered from the sidebar (you can remove it)")
    _log_nav_changes(output_dir, labels)

    failures = [
        (label, "required by nav_must_include but not in sidebar")
        for label in cfg("nav_must_include", [])
        if label not in labels
    ]
    previous = None
    for index, label in enumerate(labels, 1):
        try:
            el = dict(_sidebar_links(win)).get(label)
            if el is None:
                failures.append((label, "link disappeared during the walk"))
                continue
            _invoke(el)
            time.sleep(2)
            img = win.capture_as_image()
            digest = hashlib.md5(img.tobytes(), usedforsecurity=False).hexdigest()
            slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
            img.save(os.path.join(output_dir, f"webapp-{index:02d}-{slug}.png"))
            if digest == previous:
                failures.append((label, "screenshot identical to the previous page: navigation had no visible effect"))
            previous = digest
            log(f"Nav {index}/{len(labels)} '{label}': ok")
        except Exception as e:
            failures.append((label, str(e)))
            log(f"Nav '{label}' failed: {e}")
    if failures:
        log(f"Nav failures: {failures}")
        return False
    log(f"All {len(labels)} discovered pages navigated, each visibly different from the last")
    return True


def check_diagnostics():
    try:
        r = urllib.request.urlopen(f"{BACKEND_URL}/api/v1/diagnostics", timeout=5)  # noqa: S310 - localhost diagnostics check
        data = json.loads(r.read())
        log(f"Diagnostics: HTTP {r.status}, tools={len(data.get('tools', [])) if isinstance(data, dict) else '?'}")
        return True
    except Exception as e:
        log(f"Diagnostics check skipped: {e}")
        return False


def cleanup():
    kill_stale()
    log("Cleanup done")
    return True


_webapp_window = None  # module-level cache for the found window


def phase_nav_walk(output_dir=None):
    """Reuse the connected window from phase 6 if still alive, else re-find."""
    win, _ = wait_connected_badge(timeout=10)
    if not win:
        log("No webapp window for nav walk")
        return False
    return nav_click_through(output_dir or "cua-reports", win)


def main():
    parser = argparse.ArgumentParser(description="CUA webapp test (pre-Tauri)")
    parser.add_argument("--config")
    parser.add_argument("--output-dir", default="cua-reports")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--timeout", type=int, default=0)
    args = parser.parse_args()
    if args.config:
        _CONFIG.update(load_config(args.config))
    if args.timeout:
        global CONNECTED_TIMEOUT
        CONNECTED_TIMEOUT = args.timeout

    global BACKEND_PORT, FRONTEND_PORT, BACKEND_URL
    BACKEND_PORT = int(cfg("backend_port", 10700))
    FRONTEND_PORT = int(cfg("frontend_port", 0))
    BACKEND_URL = f"http://127.0.0.1:{BACKEND_PORT}"

    print(f"=== CUA Webapp Test v{CUA_WEBAPP_TEST_VERSION} ===")
    print(f"Product: {PRODUCT_NAME}  Backend: {BACKEND_PORT}  Frontend: {FRONTEND_PORT or 'n/a'}")

    phases = [
        ("1-kill-stale", kill_stale, True),
        ("2-start-stack", start_stack, True),
        ("3-backend-health", wait_backend, True),
        ("4-frontend-ready", wait_frontend, False),
        ("5-browser", lambda: None if args.no_browser else open_browser(), False),
        ("6-connected-badge", lambda: bool(wait_connected_badge()[0]), False),
        ("7-nav-walk", phase_nav_walk, False),
        ("8-diagnostics", check_diagnostics, False),
        ("9-cleanup", cleanup, False),
    ]

    passed = failed = 0
    for name, fn, critical in phases:
        try:
            ok = fn()
            if ok:
                passed += 1
                log(f"V {name}")
            else:
                failed += 1
                log(f"X {name}")
                if critical:
                    log(f"CRITICAL — aborting ({name})")
                    break
        except Exception as e:
            failed += 1
            log(f"X {name}: {e}")
            if critical:
                log(f"CRITICAL — aborting ({name})")
                break

    log(f"Result: {passed}/{passed + failed}")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
