# gx-final: exact x3mf fallback

The source in [bots/gx-final](../../bots/gx-final/src) is a byte-for-byte copy of x3mf's source, with `X1_MAPFIT=1` and no GX policy changes. The [CAMBC source bundle](gx-final.zip) contains the same 39 files under `src/`.

- Release Wasm SHA-256: `c3da892053a7eaeba8056c6eb9f94cc6122b0c6296ff265e06d7931a886a8c05`.
- ZIP SHA-256: `c8755adcd1d57797ff1e0b51a29c787c3b70473fe6352ddd96a876d293508b4d`.
- Exact reference: 341/516 across v92, v86h and x1bru; 548 fuel-outs and zero faults. Styled: 50/100 vs v92, 42/100 vs x1bru. Maze: 59/118 vs v92, 83/118 vs x1bru.

The release build was reproduced from the packaged source and checked against the benchmark bytes. These match results belong to those exact bytes. This package is a baseline for comparisons; it offers no new ladder improvement to test.
