# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ['run_server.py'], pathex=['src'],
    datas=[('src/inkscape_mcp', 'inkscape_mcp')],
    hiddenimports=['uvicorn.logging','uvicorn.loops','uvicorn.loops.asyncio','uvicorn.protocols','uvicorn.protocols.http','uvicorn.protocols.http.httptools_impl','uvicorn.protocols.http.h11_impl','uvicorn.lifespan','uvicorn.lifespan.on','cachetools','beartype','_strptime','_datetime','joserfc','joserfc.jwk','joserfc.jwt'],
    excludes=['tkinter','setuptools','pip','wheel','test','tests','unittest','_distutils_hack'],
    noarchive=True,
    runtime_hooks=['hooks/runtime-opentelemetry.py'],
)

# Filter large native binaries (pyd/DLL) to control installer size.
# cachetools and beartype are pure Python, already in hiddenimports.
SKIP = ['torch','playwright','bitsandbytes','llvmlite','pyarrow','pymupdf','grpc','numba','Cython','google','azure','boto3','botocore','matplotlib','PIL','pandas','scipy','sklearn','onnxruntime']
a.binaries = [b for b in a.binaries if not any(s in b[0].lower() for s in SKIP)]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas, name='inkscape-mcp-backend', debug=False, strip=False, upx=False, upx_exclude=[], runtime_tmpdir=None, console=True)
