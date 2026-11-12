# x1 on the 5060 PC: README

You are the **run machine** for the x1 Battlecode bot. Rishik's PC develops the bot; this PC plays the games at
volume (full tests, retries, the branch farm, the joint search, the league). The two machines talk only through
the GitHub branch `comms/x1`. Start with HANDOVER.md for the current state and your first jobs.

## Setup (about 20 minutes plus the first compiler download)

1. Clone and check out the code branch:
   ```
   git clone https://github.com/Infosuii/neural-networkk-battlecode.git x1work
   cd x1work && git checkout build/z-plan
   git checkout -b build/z-plan-5060 && git push -u origin build/z-plan-5060
   ```
   Use a short path outside OneDrive. Keep 30 GB free.
2. Python 3.12 (stdlib only for the tools used here).
3. Engine CLI: on Windows `tools/vendor/cambc.exe` is used automatically. Elsewhere install `cambc==4.0.0` and set
   `DZ_CAMBC` to it. The first build downloads its compiler once.
4. Comms: `SIDE=g5060 bash tools/x1_comms.sh init` (creates `../x1-comms` on `comms/x1`). Read `PROTOCOL.md` there.
5. Workers: use threads minus 2 per run (`WORKERS=...`), one run at a time.

## Commands

| Task | Command |
|---|---|
| full gate of a candidate | `WORKERS=N bash tools/x1_gate.sh x1 TAG "--set X1_FLAG=1"` |
| switch hash check | `python tools/x1_flag_hashes.py SNAPSHOT_SRC SPEC.json OUT.json` |
| feature sweep | `bash tools/x1_sweep1d.sh` |
| comms | `SIDE=g5060 bash tools/x1_comms.sh pull` / `push "message"` |

Runs land in `research/dz/runs/<name>/results.json` (+ `evidence.zip`, keep local).

## Rules

- Push code only to `build/z-plan-5060`. Never push `main`, `build/z-plan`, `lab/box`, `ops`, `experiment/*` or
  Tamim's branches; never merge any branch into another.
- Never edit `bots/x1`: the PC is its only writer. Test switches with `--set`.
- In `comms/x1` write only `g5060/`. No code there; nothing from there is merged anywhere.
- Never upload to the ladder or log in anywhere; Rishik uploads.
- Retry before reject (research/x1/RETRY_QUEUE.md): you report numbers and the gate verdict; you never drop a feature.
- Fuel: report every fuel-out; a candidate with new fuel-outs fails the gate.
