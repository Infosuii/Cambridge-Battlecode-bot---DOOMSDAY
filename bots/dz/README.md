# DOOMSDAY Zero — pure algorithmic bot

Clean-slate C++20 implementation begun 2026-10-28. No previous bot code, weights,
learned policies, or old per-map decision tables are included. The official SDK
and standard library are the only bot dependencies. Old bots are opponents only.

Start with [the current handoff](../../research/dz/HANDOFF.md). The supplied research
is preserved under `research/zero-bot-plan-2026-10-28/` along with its supporting
audit packages. Its planning sketches are inputs, not assertions of implemented behavior.

## Implemented starter

- Persistent draft/play loops, catch boundaries, fuel tiers, hard reserve, stale-round
  checks before SDK mutations, and immediate restart after suspended execution.
- All actions and shared-memory writes pass through `Actuator`.
- Runtime map/group/item/champion metadata, budgeted startup, cached home/altar fields,
  lazy group fields, and dynamic collision-aware walking.
- Self/visible-unit observations, persistent partial camp HP, respawn-generation reset,
  bounded camp scans, six-round progress contracts, and avoid timers.
- Tested six-slot claim codec; sorted body handles; unsupported group indices publish
  IDLE. Claims are soft hints. Team messages remain disabled because freshness is unresolved.
- Research-prior legal draft for 3/4/5 picks; fixed role shopping; nearest-group farming;
  basic attack and metadata-driven reset/damage/CC/shield spells; basic banking, recall,
  camp-blocked altar prerequisites, and ward placement.
- No output in the default release build. A separate `--trace` copy prints diagnostics.

## Still required

Most of Z0's 27 conformance tests; full fingerprint; calibrated ObjModel and EE;
economy auction and crews; single capturer and timed cluster circuits; hazard banking;
gear utility; exhaustive map-aware draft; race controller; tested team-message freshness;
opening schedule; dash/heal/consumable policies; meaningful parity/league/holdout gates.
The low-fuel emergency path currently heads home; it is not the complete planned 5k-fuel SafeMode.
Caught module errors are counted, but per-module disabling is not yet implemented.

This is a walking skeleton, not a finals candidate. Read `research/dz/RESULTS.md` for
known weak maps and failed experiments. A win against idle can come from the gold
tiebreak with few or zero banked gems; never use idle win rate as an economy claim.

## Reproduce (from the repository root)

```powershell
python tools/dz.py host
python tools/dz.py build
python tools/dz.py verify
python tools/dz.py smoke --name my-fresh-idle-run --pool
python tools/dz.py smoke --name my-fresh-v65-run --pool --opponent v65
python tools/dz.py conformance --name my-fresh-ct-run --maps 00collision 01big-world
```

The runner uses Python's standard library and repo-relative paths, without
`config/paths.json`, NumPy, Node, training data, credentials, or a Python venv.
The official CLI builds through the repository's official `cmake/CMakeLists.txt` and
vendored `sdk/`; a bot-local build template is not used by this CLI.
For host tests install a C++20 g++ compiler and put it on PATH, or set `DZ_CXX`.
See repository `CONTINUE_HERE.md` for restoring the pinned Windows build toolchain.

Every run requires a fresh name. Raw working files go to `artifacts/tmp/dz/<name>`;
portable frozen source, both Wasm binaries, build logs, full native summaries and
replays go into `research/dz/runs/<name>/evidence.zip`, with external JSON reports.
`verify` checks capsule CRCs and content hashes. Diagnostic truncated games intentionally
have no match outcome; their fault counts are not measured. The fuel resumption test
deliberately exhausts fuel and must never be evaluated as a release candidate.

No automatic submission, activation, or ladder duel occurs in these commands.
