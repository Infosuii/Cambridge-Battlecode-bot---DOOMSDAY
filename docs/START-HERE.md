# Start here

**DOOMSDAY is a hybrid strategy bot for Cambridge Battlecode.** The recommended final local release is v306.
Choose a route through the repository below.

## The five-minute tour

1. Read the [architecture overview](architecture.md): how observations become an action.
2. Open [`play_turn`](../bots/mainline/v306AltarPressureReach/src/bot.cpp), near line 8036, for the main decision cascade.
3. Follow `handle_enemies`, `tribute_if_needed` and `farm` for combat, banking and economy.
4. Read the [results guide](RESULTS.md) to see what was measured and why v306 stayed the recommendation.
5. Use the [complete feature audit](../research/doomsday-movement-20261110/architecture-audit-v306-20261111/BOT-ARCHITECTURE.md)
   when you want every subsystem, including inactive alternatives and configuration interactions.

## Run or inspect the final bot

| Artifact | Use |
|---|---|
| [Compiled release ZIP](../research/doomsday-movement-20261110/releases/best-final-v306AltarPressureReach/compiled-bot.zip) | Packaged release containing source and the frozen compiled bot |
| [Source ZIP](../research/doomsday-movement-20261110/releases/best-final-v306AltarPressureReach/bot.zip) | Original source package |
| [Frozen WebAssembly](../research/doomsday-movement-20261110/releases/best-final-v306AltarPressureReach/bot.wasm) | Exact compiled v306 artifact |
| [Readable source](../bots/mainline/v306AltarPressureReach/src) | The 44 source/header files, including model weights |
| [Build receipt](../bots/mainline/v306AltarPressureReach/release-build.json) | Source, SDK, CLI and compiled hashes |

These are historical competition artifacts. Use the compatible CAMBC engine/CLI; a newer engine is not guaranteed
to accept or reproduce them. The frozen Wasm avoids introducing a new compilation into a replay comparison.

The historical CLI build form is:

```bash
cambc build bots/mainline/v306AltarPressureReach --release --output v306.wasm
```

The repository includes SDK material, but this presentation update does not revalidate a clean installation of
the historical toolchain. Compare the environment and build receipt before claiming exact reproduction.

## Follow the evidence

The [extended benchmark](../research/doomsday-movement-20261110/crew-next/long15-261110355-REPORT.md) compares v306,
v320 and v348 on paired conditions. The [supplied-opponent test](../research/doomsday-movement-20261110/crew-next/mediumzip-7d9b610b-261111401-REPORT.md)
is a separate matchup and reveals an important weakness on major-objective maps.

Model presence does not establish model use: several experimental models are disabled. Zero native faults does
not imply zero fuel exhaustion. The [audit](../research/doomsday-movement-20261110/architecture-audit-v306-20261111/BOT-ARCHITECTURE.md)
and [results guide](RESULTS.md) explain these distinctions.

## Recover the research

The final source/research capsule preserves 19,710 files with content deduplication. GitHub's API required twelve
parts. Download all `.partNN` files, `ARCHIVE-PARTS.json` and `restore_snapshot.py` together, then follow the
[restore guide](../research/doomsday-movement-20261110/README.md). The helper verifies hashes and refuses to replace
different existing files.

Earlier project material is indexed by [research](../research/README.md), [bot family](../bots/README.md) and
[timeline](timeline.md). Historical handoff documents describe their original state; they are not current instructions.
