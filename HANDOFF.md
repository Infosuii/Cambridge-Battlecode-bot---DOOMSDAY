# Latest task: replay scouting completed — 2026-10-25

Read [analysis/top-teams-2026-10-25/REPORT.md](analysis/top-teams-2026-10-25/REPORT.md)
and [ops/HANDOFF.md](ops/HANDOFF.md) for the current competition lineage. Current
main was refreshed from `795ed8f` to `2e1dcc1` before this analysis; the historical
framework handoff below is not the current v52 competition status.

Downloaded 36 official replays (24 top-six focal games, 12 DOOMSDAY games after
the documented v52 deployment). All 36 passed score/outcome/round/draft/checksum
and decoder/census reconciliation. Found an opposing-pick exclusion in the v52
draft despite legal mirror picks; early Treasure/income differences; boss_battle
score-access failures; and stampede capture/repeat-cycle concerns. Read the report
for counterexamples, sample limits and precise source attribution.

Only analysis tools/documentation/evidence changed. No bot changes, new games,
training, parameter updates or submissions ran. Raw bundles and full decodes stay
under ignored `artifacts/local-only/top-team-study-2026-10-25`. The user completed
CLI sign-in for downloads; credentials were not read or recorded by the tools.
There are no remaining analysis jobs. Proposed bot experiments are not implemented.

---

# Historical framework handoff — 2026-10-24

Workspace: C:/projects/cambridge battlecode/work/neural-full-stack. Private GitHub: Infosuii/neural-networkk-battlecode, main. Training stays on this laptop; the large backup was cancelled. No agents were spawned in this continuation. Codex owns architecture/training logic; the later Freebuff/DeepSeek agent handles training operations. Winning matters, not a neural percentage quota.

## Delivered

Eight direct gameplay heads are integrated: strategy/objective/role/bank/shop/move/combat/engage. Compact1056-parameter model is seeded synthetic/untrained; new heads remain off in the checked-in bot and packaged release. The inherited trained draft remains separate. NFS2/interpretation2 is separate from legacy NFS1/residual-v1.

Per-head fuel admission, reset/overflow checks, guarded SDK execution, persistent champion RNG, bounded per-head recording and deferred output are integrated. Safe held turns preserve semantic options AND their live recording intervals; actual abandonment/override/cap censors them. Successful policy deposit completes macros normally.

GPU training, streaming JSONL metrics, explicit device selection, atomic version3 checkpoints, epoch recovery, crash/deadline checkpoint export, regular evaluation hooks and machine-operable status/action/version/checkpoint commands are implemented. Read OPERATIONS_HANDOFF.md for the authoritative first role-head training recipe. DEEPSEEK_TRAINING_PROMPT.md and NEXT_AGENT_PROMPT.md are the requested operator prompt. Earlier TRAINING_LATER.md recipes are superseded where that operations document differs.

The true non-neural baseline is frozen at artifacts/baselines/heuristic-v1: all audited neural macros are0, including inherited drafting. Wasm SHA25600c7d487990959cb4be7aac9955a4ad06f36d863b1936632f4c9cdfc93dca283. ZIP/Wasm hashes are checked before comparisons. Original is separately labelled because it contains trained drafting.

## Actual verification

-287 Python tests PASS: artifacts/tmp/operations_delivery_python.log. Legacy460 C++ checks and97 tactics synthetic checks passed earlier; strategy/economy SDK fixtures passed. No claim of an independent agent review; lead checklist self-review only.
- Tiny synthetic CPU and RTX5070Ti CUDA tests passed: uninterrupted vs epoch-resumed actor, critic, both optimizers and NumPy/Torch/CUDA RNG exactly equal. Two full synthetic steps plus one recovery step per device; real model/registry untouched. No match-data parameter updates or substantial training. Evidence: evaluation/results/operations_verified.json.
- Four minimal comparison games and two role-record games: no faults, fuel exhaustion or invalid records. Role records yield193 eligible starts and220 actual logit comparisons, max error1.1920928955078125e-07. Frozen baseline binary matches the baseline actually used in those games. Same-version control draws; untrained policy loses to heuristic baseline. No strength claim.
- All-off current source SHAf3cd26027a4415a6efd16f29de77a8408974429d0c3c8316ba4a03e58232f77b. Full Wasm identical to original: eb0ea88fc734661cf93935e5eab3c79e7a2658c7d05b7965593fbeb22d9d4442. Receipt operations_teacher_exact.json.
- Final clean heads-off package: artifacts/release/2026-10-24-final/neural-framework-untrained.zip and .wasm, manifests, SHA256SUMS. Independent official rebuild full SHA matches6d64d2a08aeda1998c1e6ab537cf716e195ba6e6047621a6bb83e51c440ad8c5. ZIP SHA2fb97aa22624b2624ce376600cfaf02949000371afb14ec41ad383fa259fadd7. Package strips inherited lab exports and is distinct from teacher_exact. Nothing submitted/activated.
- Historical18-game integration matrix, component measurements and earlier failed diagnostics remain distinguishable in evaluation/results. Larger-map refusals and some islands fuel exhaustion remain limitations; do not claim universal fuel safety. Current development maps are reused benchmarks.

## Operator start

Read OPERATIONS_HANDOFF.md. Use CUDA interpreter from config/paths.json without changing the old environment. Set PYTHONPATH to repo/python and TMP/TEMP to repo/artifacts/tmp. First approved cycle: role only, encoder/other heads frozen, two6-game seeded collection batches, grouped preflight, at most5minutes/four epochs of CUDA fitting, approved regular comparison configuration. The user has asked the later agent to begin this bounded cycle after handover; Codex did not run it.

All learning requires the explicit CLI authorization flag. Stop on data/parity/implementation failures or documented KL/entropy/deadline gates. No automatic promotion or submission. Preserve frozen references/SDK/maps and baseline. Do not alter architecture/losses/rewards/candidates/budgets independently: return such problems to Codex.

## Limits / honest follow-up

No real-data training has run, so playing strength is unestablished. Imitation CLI/loss support requires a separate explicit teacher-annotation collection adapter; current direct logs have no teacher labels. Conservative dash/combat action subsets and large-map refusals are documented in ARCHITECTURE.md. The latest operations additions have not had a new fresh-laptop clone run; prior development-clone evidence is historical. All required new source/baseline/package artifacts are versioned, and current local287-test suite passed.

No long-running job remains from these verification checks. Before future C++ changes, preserve the all-off byte requirement. Use official cambc --release/default fuel only, never override fuel. No browser/desktop/login/submission. Write only in the workspace. Update this handoff if further work is done.
