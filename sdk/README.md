# SDK

`cpp/` is the official CAMBC C++ SDK (`cambc.h`): game constants, the champion and world API, and the host calls that
are cheap compared with wasm loops (bitboards, distance fields). `cmake/` holds the build files for the neural-framework
bot. Bots are normally built with the official CLI: `cambc build <bot dir> --release --output <file>.wasm`.
