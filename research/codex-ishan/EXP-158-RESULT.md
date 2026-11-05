# EXP-158 exact live source identity

The official v108 and v109 archive downloads are byte-identical at SHA-256 `c013c216393de628334c1d38d4c24d6abdd1b8bf159d8ffb262711040febd5e8`, with 45 source files. Two clean SDK5 Windows builds produced WASM `f3d919e9a0e870c131b821742d370f40cbdb78dbc04a22945add78d95da91775`. The weights header is `6661d16ace9971334ba646993729560f77bec507d4191e7527201f3e2ab21862`. The main header sets CLFS to 1. The signed-in site showed live v109. [Complete file hashes and official archive URL](LIVE109_SOURCE_VERIFIED.json).

This verifies the downloaded live source and the reproducible local build. The platform's compiled WASM hash is absent from the submission API. The archive gives the stronger identity for cross-host comparisons.
