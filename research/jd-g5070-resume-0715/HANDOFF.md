# Frozen builder handoff (validation in progress)

The leading local candidate uses `JD_CONTACT=3,JD_GOV=5`. Its release WASM SHA-256 is
`e36f44134ed7ca2e9fc914bee73c0b76a826519e0b74446e88c43140a72fe0a2`.
The immutable v92 baseline remains `5704d7ba41acca8f5c369c963cec1719c1285780a532cc797857d8d7e3a06d47`.
No official submission, activation or ladder duel occurred. No ladder lock was requested or held.

Candidate source: `bots/jd-g5070-resume-0715/src`. Every switch defaults off, preserving v92's exact hash.
The packaged variant has CONTACT3 and GOV5 explicitly enabled. Use the manifest, not directory defaults,
to identify the scored artifact. `JD_PROGRESS`, `JD_FIELDS`, `JD_LASTPICK`, and neural heads remain off
in the leading candidate. The roster codec is tested infrastructure; it has no measured gameplay value here.

Strategy freeze: commit `30aa8ead`, recorded in FINAL_FREEZE.json. Two policy finalists plus a runtime-only
control are being confirmed on 186 maps x six opponents x two sides = 2,232 cells per variant.
The official pool and fresh generated partition remain confirmation-only; do not tune on their results.

The seed and completed iteration31 checkpoints are preserved. `export.py` emits exact float32 literals,
pins the upstream exporter, refuses overwrite and verifies every emitted float against its checkpoint.
Golden fixtures passed 121/121 real WASM observations and185/185 host rows including64 extreme cases.
Both models failed release qualification on corrected-runtime conformance and remain off. The training
job was found stopped; it was not restarted. Full checkpoint lineage is in TRAINING_LINEAGE.json.

Source-only archive: see PACKAGE.json. Created with official `cambc bundle`; never uploaded.
Remote Git push was rejected by automatic approval review for source-export authorization. All new commits
are local on `johndoe/qualifier-builder-g5070-resume-0715`; issue #6 documents the current epoch3 ownership.
Other checkout changes and the old training outputs were preserved.

One exact next command after confirmation completes:

`python tools/jd_g5070_resume_0715/summarize.py`

Clean archive reproduction (use a fresh name each time):

`python tools/jd_g5070_resume_0715/reproduce.py --name final-smoke-01`

The local runner retains the original frozen partitions and requires `--holdout` for final data. Full
replays, statistics, frozen source/builds and model files remain in the original `jd-eval` directory.
Only compact evidence and source are committed. Official diagnostics are checked; silent SDK false
returns are not separately instrumented and are not claimed to be zero illegal attempts.
