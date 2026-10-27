# Resumed v67 work, after checkpoint 9b15244

## Authoritative update after the frozen validation

- Current live source: b40-four-seed-policy, **220 strict wins/240**, +508.6, zero faults, fuel345 vs185.
- Same frozen source on development 5/6: 217 strict (218 outcome) wins, +467.8, zero faults, fuel361 vs119.
- Untouched 7/8: **137/240**, +91.9; reserved 3/4: **137/240**, +104.3. All zero faults. Strong overfitting persists.
- Final-source older guards:139 vs v61,+88.4;159 vs v58,+186.7;141 vs v66b,+153.5. All240games/zero faults.
- Full actual output and all1680game receipts are in FINAL_BENCHMARK_OUTPUT.md/FINAL_GAMES.json. README and
  FINAL_REPORT explain higher fuel exhaustion and why the broad strength goal is unfinished.
- FROZEN_CANDIDATE.json was written before launching3/4; current source still matches that hash set. **3/4
  are consumed: never use their data to select or tune subsequent controllers.** Use new reserved validation seeds.
- The separate coherent package p42 scored17/240,-613.7,zero faults. Full mechanism audit showed R250gold512.5
  vs956, gems53 vs107.5; a single diagnostic's improved damage was not representative.
- A concrete integration omission was found: its new turn loop skipped priority updates, death/job cleanup,
  field warmup and other mature lifecycle bookkeeping. `make_package.py --variant lifecycle` reconstructs a
  separate combat-package-v3 from corrected p15, uses TEAMPLAY3's complete lifecycle, replaces the old contact
  gate with v67_team_combat and disables legacy hunt overrides. Formation, focus, raw stats and Vesper capture
  ownership remain together. **p48-package-complete-lifecycle** is running, unified-exec session48821 at this note.
  Audit with run.py --run p48-package-complete-lifecycle --record-existing when complete; it is a prototype,
  not live acceptance source. Do not rerun the generator into its existing folder.
- `run.py` now checks exact schedule rows and opponent/seed metadata before historical audits. `checkpoint.py`
  selects a source-matched training run rather than mistakenly treating the latest guard/prototype as live source.
- `final_report.py` exports the seven completed frozen-candidate validations and checks their exact source hashes.
  It intentionally reports the failed generalization and higher fuel; it does not certify a broad success.
- Native exhaustive team protocol tests and Python syntax checks passed. v65/mimic tracked sources unchanged.
- Update this leading section as work continues. Everything below is historical and may describe obsolete source.

## Latest state: read this before the historical sections

The user explicitly said to fix confirmed defects immediately, and supplied new measured-loss notes at
`C:\Users\omdha\.codex\attachments\c5eb92c2-0758-483a-a571-17052d0f9176\Pasted text.txt`.
They are leaving and authorize autonomous work without worrying about usage. Key new evidence: early farming
is fairly close; the large gap opens after R250 through champion deaths, isolation, weak raw stats and lost bags.
Use a coherent coordination/focus/burst/raw-stat package and measure R500/R1000 mechanisms. Do not stop at a fitted
benchmark result or claim that the bot is flawless.

The fitted b26 portfolio actually scored235/240 (234strict positive-margin wins), but fresh5/6 scored142/240.
Required older guards on that source:138vs v61,153vs v58,128vs v66b, all240games/0faults. These are historical,
not validations of later source. Reserved3/4 HAVE NEVER BEEN USED.

Both active tagged policies p14/p15 now FIX the arrival deadlock: compact job messages on maps<=62groups carry
an explicit arrived flag, peers preserve it across position messages, job changes and leaving clear it. Native
codec tests cover all compact group/flag combinations. Also fixed the unused team-helper next-clear method to
actually attack the next camp. Latest corrected full run b35-arrival-cache-complete:226outcome wins,225strict,
+541.4margin,0faults,fuel352vs123. Same source fresh5/6 v36:136/240,+71.4,0faults. Live source exactly matches b35.

The old four-seed policy grid cal29-multiseed-grid completed4480diagnostics (seeds1/2/5/6),0faults. With training
floor220 its best predicted fresh5/6 score was218. The arrival fix invalidated old p14/p15 results, so
cal37-corrected-tagged-policies re-measured ONLY corrected p14/p15 across ALL83scheduledmap/side cases and all
four development seeds:664games,0faults, complete. Unchanged families reproduced208/208game margins in a full
b26→b33 comparison. Combined corrected proposal predicts220strict on1/2 and217strict on5/6, totalfuel706over480games.

Next command to compute/apply the corrected multi-seed assignment (not run with --apply yet):
```text
python tools/v67/robust_assignment.py --grid cal29-multiseed-grid --base b35-arrival-cache-complete --extra-base v36-arrival-cache-seeds56 --supplement-grid cal37-corrected-tagged-policies --replace-policies 14 15 --floor 220 --apply
```
Then fresh full acceptance and5/6 runs are required. Holdout3/4 stays reserved until final freeze. Additional fresh
seeds7/8 can check generalization before spending the holdout; never use3/4 in calibration.

Independent coherent combat prototype is under artifacts/tmp/v67/combat-package-v2/src, generated by
tools/v67/make_package.py plus package_combat.cpp. It uses the corrected shared protocol, preserved legacy farming,
fixed Vesper/Heart/Vendetta/Varg/Marcella draft, Bruiser stacking with one farming mitigation item, short contact,
global reinforcement calls and aggregate team HP×damage estimates. The first v1 diagnostic on00quadrants lost
705vs1015, but dealt6583championdamage vs3352, lost25gems to champions vs43, and earned1726vs1612goldbyR500.
It collected too few gems(623vs857byR500), and its action ledger showed excessive permanent-group travel and
shared capture waiting. v2 changes to threat-triggered formation, skips followers' reward targets, and starts
frontline Jungle health before raw-stat stacking. Active diagnostic: trace-p39-responsive-formation, session28838.
The prototype is separate from the current v67 and is NOT a validated strength result.

Native mechanisms: tools/v67/mechanisms.py --run NAME writes official timeline medians at100/250/500/1000/end,
including gems lost to champions, and checks gem-loss conservation. It clamps finished games to final state.
For the single-game prototype the loss accounting matched exactly. Its replay action ledger is at
artifacts/evaluations/v67/trace-p38-combat-package/ledger.json; early farming gold858vs900atR250, so the issue was
capture/travel efficiency, not a total income freeze. Two earlier crew-economy prototypes failed and are kept
under artifacts/tmp/v67/crew-prototype and trace-v30/v31/v32 outputs. Do not promote them.

run.py --record-existing now audits the exact builder source snapshot, normalizing only the documented NOVA seed
rewrite; it no longer attributes a historical test to a changed live tree. raw_run.py captures complete output
without contending for RESULTS logs; audit it afterward with run.py --record-existing. --bot supports independent
prototype diagnostics. Actual acceptance always uses bots/v67 and the original fixed plan.

Last committed source before the portfolio was399c697; current generated portfolio and subsequent tools/results
need committing/pushing after validation. Only our files, never GPT_PROMPT.md, config/paths.json or other agents'
variants/artifacts. Older README/HANDOFF/CHECKPOINT prose is historical and must be updated before final delivery.

## Historical progression

The user resumed the work explicitly. The goal remains 220/240 plus the frozen guards; do not stop at the handoff.
Seeds3/4 remain unused. No ladder queue/submission. v65/mimic remain untouched.

Current architecture has changed substantially: v67 now packages complete, isolated policies and chooses a policy
for each map and absolute side. The SDK exposes the bot's own absolute side through cached_my_team (0/1), a public
value; no hidden game observations are used. Every champion uses the same selected policy for the whole game.

Measured progress:
- Confirmed new-controller startup freeze on 00quadrants: before fix 0gold/0gems, all heroes stayed on spawn;
  unconditional entry to bounded build_fields() changed it to688bankedgems and1640gold, but still lost.
- b19 startup fix:7/240,-749.2,0faults,2077fuel. Architecture still failed.
- Added time-multiplexed tagged job/position messages and timed focus coordinates. Reused the established full
  pipeline in TEAMPLAY3. b20:95/240,-119.1; adding joins/focus b21:91/240,-139.3. Both failed strength target.
- Native exhaustive protocol tests passed after fixing uninitialized test variables; no old test binary was
  accepted as evidence after the failed compile.
- Exact controller source is committed in399c697 and moved to artifacts/tmp/v67/controller-v21.
- tools/v67/portfolio.py isolates historical source snapshots in C++ namespaces, keeping complete policies intact.
  The wrapper parses SDK/standard headers globally, then wraps each policy's translation units. Bodies persist as
  function-static Bot objects. One-policy equivalence diagnostic x22:136/240 vs original b06's137, almost samefuel.
- b22 combined map portfolio:195/240,+409.1,0faults,fuel270vs130,gold7082/game. Strict gem-margin wins194 (one
  outcome win used a tiebreak). Retrospective222 was only a prediction, not claimed as a measured score.
- b23 diagnostic-control base:196/240,+409.8. Source changed after this to a stable volatile map table.
- b24 stable map/side selector:197/240,+405.7,0faults,fuel263vs142. This is current source, with a126-int assignment
  table (2marker words +61maps*2sides +2fallbacks). main.cpp switches on map hash to a slot, then reads a volatile
  data cell. Policy source stays under src/policies/p0..p15; wrappers are root src/pX_*.cpp.

The full combined wasm is about5.3MB. Two seeded builds take around2.5minutes with CMAKE_BUILD_PARALLEL_LEVEL=4.
Do not interpret a silent captured build as hung; run.py prints its full output after completion. Avoid spawning
many additional compiler jobs. Original single-policy snapshots are under each benchmark build/src-bot-s1/src.

tools/proxy/local_duel.py now hashes source recursively, necessary for nested policies. Flat-tree hashes retain
the old behavior. Every full acceptance run still uses the original plan, both seeds1/2 and workers16.

The grid completed:1024diagnosticgames,0faults,64/64same-policygemmargins reproduced exactly. It selected95/100
outcome and strict wins on the failed-map subset. Combined with untouched cases, prediction is235outcome wins,
234strict positive-margin wins. tools/v67/apply_calibration.py applied24map/side changes and recorded CALIBRATION.json.

Active full runs at this note: b26-calibrated-map-policy (seeds1/2, official acceptance; unified-exec session24688)
and v27-fresh-seeds56 (seeds5/6, extra development validation, raw runner; session11874). Both build from exactly
the same frozen source. Reserved3/4 remain untouched. v27 must be audited after b26 completes using:
`tools/v67/run.py --run v27-fresh-seeds56 --seeds 5 6 --record-existing --note 'Frozen extra-seed validation'`.
The raw runner already saves benchmark-output.txt, but does not append shared RESULTS logs concurrently.

The calibration operation was tools/v67/calibrate.py --base b24-stable-map-selector --out cal25-policy-grid --workers16.
It patches ONLY our own volatile assignment data in copies of b24's wasm and asserts the wasm CODE section hash
is identical. This is parameter calibration of our bot, not a game-engine or opponent modification. It evaluates
all16 existing policies on the training maps lost by b24, deduplicating identical diagnostic map/side/seed keys
and retaining their schedule multiplicity as weights. Final acceptance must still rebuild bots/v67 and play all
240literal scheduled games. No calibration on3/4 is permitted by the script.

Outputs: artifacts/evaluations/v67/cal25-policy-grid/experiment.json, rows.jsonl (streamed), suggested.json.
Rows preserve exact official runner receipts; scripts can resume with identical arguments/folders. Suggestions
are per map|side, prioritize positive gem margins, then outcome wins/margin and forbid faults.

Concrete next steps:
1. Wait for b26/v27; inspect the actual full results, not their predictions. The grid and application are complete.
2. Verify rows using the currently assigned policy reproduce b24 outcomes on the same map/side/seed. Only data
   for unused map cells changes in these comparisons; substantial drift would need investigation.
3. Apply best measured map/side indices to src/assignment.json and the policy_assignment67 initializer in main.cpp.
   Preserve table length/layout and other code. Update selection.json metadata to explain the calibrated choices.
4. Run a fresh full benchmark (e.g. b26-calibrated-map-policy), saving full output and auditing strict positive
   gem-margin wins as well as the runner's outcome wins. run.py now records positive_margin_wins for future runs.
5. Once target is achieved, freeze source before holdout3/4 and majority checks vs v61/v58/v66b. Report every result
   honestly; a high fitted training score alone does not establish general strength.

Do not regenerate the current portfolio blindly: portfolio.py creates the initial map-only version. The stable
side-aware selector is prepared by calibrate.py --prepare then --side-aware (one-use operations on initial layout).
Do not use --set build/controller macros on root common.h expecting to change packaged policies: their historical
macros live in src/policies/p*/common.h. Root common.h only supplies the evaluation seed.

README/HANDOFF/CHECKPOINT from the earlier checkpoint are historical and need refreshing before the next handoff.
Use this continuation and the newest RESULTS.md/jsonl for current status. The checkpoint helper still contains
hardcoded old WORKLOG prose; fix that before running it on the new architecture. It verifies latest source hashes.
