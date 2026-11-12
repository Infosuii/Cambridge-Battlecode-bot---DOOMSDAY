# Final movement, crew and camp workstream

This snapshot preserves the November 10–11 development and the detailed v306 source audit. It supplements the repository's existing research and presentation.

- [Full architecture walkthrough](architecture-audit-v306-20261111/BOT-ARCHITECTURE.md): active decision flow, conditional systems, dormant experiments and important overrides.
- [Configuration appendix](architecture-audit-v306-20261111/CONFIGURATION-APPENDIX.md): 700 named source macros and their translation-unit differences.
- [Runtime knobs](architecture-audit-v306-20261111/RUNTIME-KNOBS.md) and [source method index](architecture-audit-v306-20261111/SOURCE-METHOD-INDEX.md).
- [Recommended v306 release](releases/best-final-v306AltarPressureReach/): source ZIP, compiled ZIP, Wasm and benchmark receipt.
- [v348 experiment](releases/v348LethalFinishSafety/): retained as an experiment, not a demonstrated replacement for v306.
- [Long benchmark](crew-next/long15-261110355-REPORT.md) and [comparison with the supplied opponent](crew-next/mediumzip-7d9b610b-261111401-REPORT.md).
- Development logs in `crew-next/`; full selected experimental sources, scripts, configurations and research in `workstream-source-and-research.zip`.

The readable bot trees are also under `bots/mainline/v306AltarPressureReach`, `v320CampChannelCore` and `v348LethalFinishSafety` at the repository root.

## Source capsule

The ZIP deduplicates identical file contents. GitHub's API size limit requires the ZIP to be uploaded as `workstream-source-and-research.zip.partNN` files. Download all parts, `ARCHIVE-PARTS.json` and `restore_snapshot.py` into the same directory; the helper automatically checks and joins the parts before restoration. `snapshot-manifest.json` records each original workstream-relative path, size and SHA-256; `blobs/<sha256>` stores its exact contents inside the ZIP. It includes experimental bot sources, audit inventories/macros, research scripts and aggregate records. It excludes simulation/replay caches, dependencies, build directories, logs and expanded system-header preprocessor dumps.

Restore into a new empty directory with Python 3:

```powershell
python restore_snapshot.py C:/projects/restored-doomsday
```

Use `--scope arena/bots/v306AltarPressureReach/` to restore one subtree. Different existing files are preserved and restoration stops.

The original historical reports may refer to machine-local paths or simulation caches removed during the separate cleanup. The source capsule preserves authored work and compact records, not every raw replay. None of this snapshot submits or activates a bot on the official ladder.
