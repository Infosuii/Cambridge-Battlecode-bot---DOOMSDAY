# K011: native Linux build hash mismatch under investigation

2026-11-03 00:13 UTC. Fresh CachyOS setup; code branch build/z-plan-5070 at 9c1bbde2d5cee6ab53235019027cb452a733b340. No tracked bot/SDK/CMake changes.

Native official `cambc 4.0.0` installed from PyPI, executable SHA256 552056aab1b99a6626597b6aaf0ae38f967709626f90f2d6926c4510ca929eb4. Its first build fetched WASI SDK 33.0 (Clang 22.1.0), CMake 3.31.8 and Ninja 1.12.1.

Command: `cambc build bots/x3 --release --output artifacts/tmp/g5070-default.wasm`.
Actual SHA256 **bf3f65d009c0419d2b0f04bdfab68b85f397ce6cb2350a36ab8782d4d74cd46a**, expected **5704d7ba41acca8f5c369c963cec1719c1285780a532cc797857d8d7e3a06d47**. This is a failed hash check, not a successful reproduction.

K011's exact 18-worker/172-game run is starting to establish whether the difference also changes map/side/outcome/banked records. No K014/K012/K013 strength comparisons will run before verification. Investigating compiler, source/SDK identity and platform build differences locally.

Assistance requested if available: publish the canonical x3/v92 release Wasm (5704d7ba41ac), v86h Wasm (0fae1c17ee73), and the reference build compiler version/flags/toolchain hashes so we can compare sections and reproduce the native build precisely. Do not change the job's pass condition. No ladder access or platform credentials needed.
