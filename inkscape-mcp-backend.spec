# -*- mode: python ; coding: utf-8 -*-


from PyInstaller.utils.hooks import collect_submodules

a = Analysis(
    ['run_server.py'],
    pathex=['src'],
    binaries=[],
    datas=[('src/inkscape_mcp', 'inkscape_mcp')],
    hiddenimports=[
        'uvicorn.logging', 'uvicorn.loops.asyncio', 'uvicorn.protocols.http.httptools_impl',
        'uvicorn.lifespan.on', 'cachetools', '_strptime', '_datetime',
        'joserfc', 'joserfc.jwk', 'joserfc.jwt',
    ] + collect_submodules('key_value') + collect_submodules('inkscape_mcp'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    # MANDATORY: without noarchive=True, stdlib modules (difflib, statistics, pydoc)
    # become unreachable when packages load from disk-extracted datas in onefile mode.
    noarchive=True,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='inkscape-mcp-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX breaks or triggers AV false-positives on frozen builds
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
