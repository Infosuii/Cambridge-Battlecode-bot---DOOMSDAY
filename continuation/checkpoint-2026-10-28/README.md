# Portable research evidence, 2026-10-28

23 ordinary Git files of at most40MiB contain a962,096,269-byte compressed archive. No Git LFS or external download
link is required. `manifest.json` authenticates every part and maps57,025 logical files to29,577 unique SHA256 objects.
Full local verification read and validated every object successfully. Logical content is9,292,045,859 bytes.

Restore with `python tools/continuation_checkpoint.py restore --install-runtime` on a fresh Windows x64 laptop.
See repository `CONTINUE_HERE.md` for prerequisites, configuration, branch and continuation prompt.

Included: full new research experiments and exact source/Wasm provenance; V76/V80 final paired comparisons;
older V80 native summaries and frozen builds; v74 ladder, current-top and MG18208504 replay evidence; source-review
receipts/parity vectors; the official Windows WASI SDK, CMake, Ninja and replay runtime assets.

Excluded: credentials/login sessions, machine-specific config, Python virtual environments, obsolete CUDA training
corpora and generic generated caches. The original evaluation cache alone occupied about249GiB; it is rebuildable.
Some older V80 raw arm replays are omitted, with their native summaries, frozen builds and reports preserved.
Immediate continuation does not depend on excluded material. Research source/tools are normal Git files outside this
archive and remain authoritative; the restorer never overwrites them.
