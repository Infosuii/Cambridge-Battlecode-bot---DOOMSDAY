# Agent A report: game audit, decision inventory, teacher interface (Wave 1)

Model/runtime: this session (Kiro CLI, configured model). No training, no submission. 111 official matches in total
(`--release`, default fuel, at most 4 concurrent): probe 2, reference 48, repeat 8, first-hour sensitivity 16, lab strip 24,
strip variant 8, capture self-test 5.

## Deliverables

| # | File(s) | Status |
|---|---|---|
| 1 | `AUDIT.md`, `sdk_facts.json` (`tools/audit_sdk_facts.py`; probe `probe/a_sdk_dump.cpp`, raw `evidence/sdk_probe_facts.jsonl`) | done; every SDK line ref computed from a pattern match in cambc.h/imports.h |
| 2 | `decision_inventory.json` (59 entries), table in `AUDIT.md` / `inventory_table.md` (`tools/audit_inventory.py`) | done; all 10 candidate heads covered; inactive code paths marked |
| 3 | `patches/01_fuel_routing.diff` (`tools/audit_fuel_routing.py`) | done; 38 reads routed; **byte-identical wasm** |
| 4 | `patches/02_strip_lab.diff` (`tools/audit_strip_lab.py`) | done; off = byte-identical; on = 4/24 cells identical |
| 5 | `bot/src/nn_teacher.h`, `bot/src/nn_teacher.cpp`, `patches/03_teacher_capture.diff` (`tools/audit_teacher_capture.py`) | done; heads off = byte-identical; shadow self-test 0 violations |
| 6 | `INVARIANTS.md`, `tools/audit_equivalence.py`, `tests/fixtures/teacher/{schedule,reference_digests}.json` | done; determinism and sensitivity shown |
| 7 | this file, `CONTRACT_ISSUES.md` | done |

Helpers: `tools/audit_mkpatch.py` (git-style diffs, `git apply --check`, scratch trees on a frozen base),
`tools/audit_build_compare.py` (official build + section/export comparison).

## Commands (from ROOT, `$env:PYTHONPATH="$PWD\python"`, `$py` = neural-gameplay venv python)

```
& $py tools/audit_fuel_routing.py artifacts/tmp/A/fuelmod/bot/src
& $py tools/audit_mkpatch.py diff --mod artifacts/tmp/A/fuelmod/bot/src --out archive/agents/A/patches/01_fuel_routing.diff
& $py tools/audit_strip_lab.py artifacts/tmp/A/stripmod/bot/src
& $py tools/audit_mkpatch.py diff --mod artifacts/tmp/A/stripmod/bot/src --out archive/agents/A/patches/02_strip_lab.diff
& $py tools/audit_teacher_capture.py artifacts/tmp/A/capmod/bot/src
& $py tools/audit_mkpatch.py diff --mod artifacts/tmp/A/capmod/bot/src --out archive/agents/A/patches/03_teacher_capture.diff
git apply --check -v agents/A/patches/0{1,2,3}_*.diff                    # all OK against current bot/src
& $py tools/audit_mkpatch.py scratch --dest artifacts/tmp/A/final_stack --patch archive/agents/A/patches/01_fuel_routing.diff --patch archive/agents/A/patches/02_strip_lab.diff --patch archive/agents/A/patches/03_teacher_capture.diff
& $py tools/audit_build_compare.py --bot artifacts/tmp/A/final_stack/bot --out artifacts/tmp/A/final_stack/final_stack.wasm
& $py tools/audit_equivalence.py reference
& $py tools/audit_equivalence.py compare --candidate references/builds/original.wasm --label repeat-original --maps 4 --opponents v47
& $py tools/audit_equivalence.py compare --candidate references/builds/first-hour.wasm --label sens-first-hour --maps 4
& $py tools/audit_equivalence.py compare --candidate artifacts/tmp/A/p02on/p02on.wasm --label strip-lab-1 --opponents original
& $py tools/audit_sdk_facts.py ; & $py tools/audit_inventory.py
```
(The probe and capture self-test were run as inline scripts that build scratch bots: `probe/a_sdk_dump.cpp` and
`probe/a_teacher_check.cpp` + main.cpp call sites; results in `evidence/`.)

## Results

**Fuel routing (01).** 38 decision-gating reads -> `nnb::teacher_left()`: bot.cpp 22, tsearch.cpp 13, world.cpp 1,
draft.cpp 1 (A2_DPLAN rollouts; compiled out), `rb::left()` 1 (the governor's only read). 26 instrumentation reads
(bot.cpp 8 lines, tsearch.cpp 5, world.cpp 4, common.h 9) are left raw on purpose (listed in
`tools/audit_fuel_routing.py LEFT_RAW`; presence asserted for bot/tsearch/world when the tree is built); all are in compiled-out or constant-false
blocks except world.cpp:43 (runs once in `World::init`, value only used by an `if (APEX_PROFILE)` print).
With the lead stub (`kFuelCredit=false`) the patched build is **byte-identical** to `references/builds/original.wasm`
(sha256 `eb0ea88f...4442`, code section `02739407...0136`; `evidence/p01_build_compare.json`). No matches were needed for
this claim: identical wasm + deterministic engine (below) gives identical games. With `kFuelCredit=true` the tree compiles
and runs (capture self-test build).

**Lab strip (02).** Classification in AUDIT.md section 5. `NN_STRIP_LAB=0`: byte-identical. `NN_STRIP_LAB=1`
(knobs constexpr; exports, learner, builds, ctl removed): code 291,789 -> 283,470 bytes; exports 14 -> 2 (the 12
`lab_*` removed; `memory` and `_start` remain); versus original on 12 maps x 2 sides: **4/24 cells identical** (00rows A/B,
01hooks A/B), 20 different, 9 outcome changes, fuel trace different in 24/24 (`evidence/eq_strip_lab_1_vs_original.json`).
A scratch variant that removes only exports, ctl and builds (learner and mutable knobs kept) was identical in 6/8 cells
(`evidence/eq_strip_variant_s2.json`). Conclusion: stripping is not behaviour-identical; it is a fuel change. No
improvement claimed (the stripped bot's cell wins were 15 vs 12 for the reference cells; that is not evidence of strength).

**Teacher interface (05).** `nn_teacher.h` = `struct nn_teacher_access` (friend of Bot): 34 read-only accessors of teacher
state and 10 accessors of per-turn captures (objective top-K with teacher first, bank verdict + all terms, fight target keys / formula /
search / final verdicts, behaviour-chain branch, next purchase, follow_field steps, spell choice, ward tile, draft net
scores). Patch 03 inserts 23 gated capture sites (`if constexpr (nnt::k...)`). Heads off: patch 03 alone, the frozen base with
`nn_teacher.cpp` and no patch, and 01+02+03 stacked (also in reverse order, which gives identical files) all build to
the **byte-identical** original wasm (`evidence/final_stack_off_build_compare.json`,
`evidence/final_plain_with_nn_teacher_build_compare.json`); nn_teacher.cpp is compiled (build log) and contributes no code.
Shadow self-test (all heads `shadow`, kFuelCredit on, captures checked after every turn, 4 matches + 1 draft check;
`evidence/capture_selftest.json`): 0 violations of objective candidate-0 == returned group, committed `target_group` ==
captured teacher choice on every farm/nofarm turn (e.g. 1,264/1,264), formula target == argmin key on every fight turn,
tribute branch implies `go`, step order monotone, draft pick legal and a first maximum (5/5 picks); 0 bot faults.

**Equivalence fixtures (06).** Schedule: 12 maps (sorted `engine.maps()`, indices i*40//12), both sides, opponents
original and v47 = 48 cells; reference digests from original.wasm. Comparison levels: replay (sha256 of
`replay.repl26a`; checked to contain no bot names, paths or timestamps), canonical summary, candidate and opponent fuel
traces, stdout. Determinism: the original-vs-original cells run twice per map (side A and side B are the same pairing)
are identical at every level on 12/12 maps; a re-run of 8 v47 cells is 8/8 identical. Sensitivity: first-hour 0/16 equal
(6 outcome changes); stripped lab 20/24 different.

## Verified vs not verified

Verified by commands above: byte identity claims, `git apply --check` of all three patches on the current bot/src,
patch commutation, determinism, comparator sensitivity, capture semantics on 5 matches, SDK runtime values on one map.

Not verified / limits:
- Runtime SDK values come from one map/engine build; designs and settings are engine data (read at runtime).
- The post-2000-round tiebreak, gem pickup on kills, item inventory size and ranged-attack-ends-movement are not
  documented in the SDK (marked so in sdk_facts.json).
- Patch 01 against B's final `nn_budget.h` (needs `nn_registry.h`) is not built yet; verified with the lead stub only.
- Shadow/`kFuelCredit` neutrality is **not** shown: the self-test build's captures cost fuel, and its games differ from
  the original (not measured as a neutrality test; that needs B's real credit accounting and H's protocol).
- Hook proposals for heads are positions and semantics; the head code itself (B/D/E/F) is not written or tested here.
- stdout equality is weak evidence for these bots (both print nothing).

## Open issues
See `CONTRACT_ISSUES.md` (B header dependency, GLOB-compiled nn TUs, strategy head semantics, compiled-out heads.json call
sites, release vs strip-lab, credit cannot cover savings).
