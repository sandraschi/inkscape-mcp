"""Required checks before `mcpb pack`, per MCPB_PACKAGING_STANDARDS.md section 2.5.

Stdlib only -- must run before any packaged dependency is guaranteed installed.

Usage:
    uv run python mcpb/verify_pack.py import <mcpb_src_dir> <entry_module_or_file> <package_name>
    uv run python mcpb/verify_pack.py ast <entry_point_file>
    uv run python mcpb/verify_pack.py pollution <mcpb_dir>

The import check accepts either a dotted module path resolvable under
mcpb_src_dir (e.g. "pkg.server", the style in MCPB_PACKAGING_STANDARDS.md
section 2.2's example manifest) or a standalone bootstrap script path (e.g.
"mcpb/run_server.py") that itself does sys.path setup and imports the real
package - the latter is the more common pattern fleet-wide per section 2.5's
own "entry_point: run_server.py" discussion, and needs runpy execution
instead of importlib, since it generally isn't itself an importable module.

Exits 0 and prints "OK ..." on pass; exits 1 and prints "FAIL ..." on failure.
"""

from __future__ import annotations

import ast
import builtins
import importlib
import runpy
import sys
from pathlib import Path


def check_import(stage_dir: str, entry_module_or_file: str, package_name: str) -> None:
    """Load the entry point with stage_dir inserted at the front of sys.path;
    assert the target package actually resolved from there and not from some
    other installed copy (site-packages, an editable install, a stale twin)."""
    stage = Path(stage_dir).resolve()
    sys.path.insert(0, str(stage))

    entry_path = Path(entry_module_or_file)
    if entry_path.suffix == ".py" and entry_path.exists():
        # Standalone wrapper script (e.g. run_server.py) - run its top-level
        # code (imports, sys.path setup) without triggering `if __name__ ==
        # "__main__":`, by giving it a run_name that isn't "__main__".
        #
        # This script's OWN argv ("import", stage_dir, entry, package_name)
        # is still sys.argv at this point - runpy does not touch it. A wrapper
        # that unconditionally calls a CLI entry point's main() at module
        # level (not gated behind `if __name__ == "__main__":`) - confirmed
        # the more common fleet pattern per this module's own docstring, and
        # exactly what inkscape-mcp's run_server.py does - then has its
        # argparse choke on these four verifier arguments as if they were its
        # own CLI flags. Neutralize argv for the duration of the run.
        saved_argv = sys.argv
        sys.argv = [str(entry_path)]
        try:
            runpy.run_path(str(entry_path), run_name="__mcpb_verify__")
        finally:
            sys.argv = saved_argv
        mod = sys.modules.get(package_name)
        if mod is None:
            raise SystemExit(f"FAIL import: running {entry_path} never imported {package_name!r}")
    else:
        mod = importlib.import_module(entry_module_or_file)

    origin = Path(mod.__file__).resolve()
    if stage not in origin.parents:
        raise SystemExit(f"FAIL import: {package_name} resolved to {origin}, not under {stage}")
    print(f"OK import: {package_name} -> {origin}")


def _target_names(node: ast.AST) -> set[str]:
    """Names bound by an assignment-like target (Name / Tuple / List / Starred)."""
    names: set[str] = set()
    if isinstance(node, ast.Name):
        names.add(node.id)
    elif isinstance(node, (ast.Tuple, ast.List)):
        for elt in node.elts:
            names |= _target_names(elt)
    elif isinstance(node, ast.Starred):
        names |= _target_names(node.value)
    return names


def check_ast(entry_file: str) -> None:
    """Flag `name.attr(...)` call sites where `name` is never bound anywhere in
    the module -- catches the "uvicorn.run() with no import uvicorn" class of
    bug. Deliberately conservative: only single-level attribute calls on a bare
    Name are checked; chained/nested expressions are skipped rather than risk
    a false positive.
    """
    src = Path(entry_file).read_text(encoding="utf-8")
    tree = ast.parse(src, filename=entry_file)

    bound: set[str] = set(dir(builtins)) | {"self", "cls", "__class__"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                bound.add(alias.asname or alias.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(node.name)
        elif isinstance(node, ast.arg):
            bound.add(node.arg)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                bound |= _target_names(t)
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            bound |= _target_names(node.target)
        elif isinstance(node, ast.NamedExpr):
            bound |= _target_names(node.target)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            bound |= _target_names(node.target)
        elif isinstance(node, ast.comprehension):
            bound |= _target_names(node.target)
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if item.optional_vars is not None:
                    bound |= _target_names(item.optional_vars)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            bound.add(node.name)
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            bound.update(node.names)

    missing: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            base = node.func.value
            if isinstance(base, ast.Name) and base.id not in bound:
                missing.append(f"{base.id}.{node.func.attr}() at line {node.lineno}")

    if missing:
        raise SystemExit("FAIL ast: unbound name(s) at call sites:\n  " + "\n  ".join(missing))
    print(f"OK ast: {entry_file} -- no unbound call-site names")


def check_pollution(mcpb_dir: str) -> None:
    root = Path(mcpb_dir)
    bad: list[Path] = []
    for pattern in ("__pycache__", "*.pyc", "*.bak", "*.bak.*", "*.bak-*", "*.orig", "*.rej"):
        bad.extend(root.rglob(pattern))
    if bad:
        listing = "\n  ".join(str(p) for p in bad[:20])
        raise SystemExit(f"FAIL pollution: {len(bad)} disallowed path(s) under {mcpb_dir}:\n  {listing}")
    print(f"OK pollution: {mcpb_dir} is clean")


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    cmd, args = sys.argv[1], sys.argv[2:]
    checks = {"import": check_import, "ast": check_ast, "pollution": check_pollution}
    fn = checks.get(cmd)
    if fn is None:
        raise SystemExit(f"unknown check {cmd!r}; expected one of {sorted(checks)}")
    fn(*args)


if __name__ == "__main__":
    main()
