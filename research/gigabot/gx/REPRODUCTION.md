# Windows release identity on macOS

CAMBC CLI 4.0.0 with native WASI SDK 33.0 reproduced all 172 outcomes against v86h, with 108 wins, 186 fuel-outs and no faults. The x3 hash was `b260ebe4ecb2`. The macOS WASI runtime archives embed different source paths from Windows, including libc++abi's `private_typeinfo.cpp` and `fallback_malloc.cpp`.

Keeping the native compiler and linker, and using the Windows release's sysroot and Clang builtins, produced the Windows x3 and v86h binaries exactly. No bot, SDK source, CMake source, or engine changes are needed. The corrected gate agrees with J018 on all 172 candidate and opponent digests, engine and map hashes, outcomes, banked scores, rounds, deaths, fault counts and fuel-outs. The native and corrected runs are in [runs](runs).

- x3: `5704d7ba41acca8f5c369c963cec1719c1285780a532cc797857d8d7e3a06d47`
- v86h: `0fae1c17ee73bd758529b92f7d7ab55f1dea6f2ecf0865cdac423b2ecd5640fb`
- Eight workers: 57.9 seconds for the corrected gate including both builds (178 games/minute).

To reproduce, install CAMBC 4.0.0, build once with the native CLI, then point the runner at a separate cache with the Windows WASI libraries. Use the Windows x86_64 asset from [WASI SDK 33.0](https://github.com/WebAssembly/wasi-sdk/releases/tag/wasi-sdk-33). The helper verifies the archive digest and copies only the Windows sysroot and builtins over the native WASI SDK copy.

```sh
python3 tools/gx/wasi_compat.py /path/to/native-cache /path/to/wasi-sdk-33.0-x86_64-windows.tar.gz /path/to/compat-cache
CAMBC_CACHE=/path/to/compat-cache DZ_CAMBC=/path/to/cambc DZ_MAX_PARALLEL=8 \
  OPPS=v86h SETS=pool WORKERS=8 bash tools/gx/gx_gate.sh repro-copy
```

The result is recorded separately from the runtime ceiling. The stock x3 control already exhausts fuel on some turns.
