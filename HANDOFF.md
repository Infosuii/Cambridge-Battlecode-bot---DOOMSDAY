# Current handoff — 2026-10-24

Workspace: `C:/projects/cambridge battlecode/work/neural-full-stack`. Private development repo: `https://github.com/Infosuii/neural-networkk-battlecode`, main. Continue from HEAD; do not restart the cancelled130GB/full-backup work. Training/bulk history stays on the original laptop. No new agents: user explicitly requested solo work.

## Latest scope and current work

Eight-head SDK integration is implemented and verified as an untrained framework. The user now explicitly requires the finished framework to include GPU training, streaming metrics, checkpoint management/resume, automated comparisons against previous models and a genuinely non-neural baseline, and documented machine-operable CLIs for a separate Freebuff training-operations agent. Codex retains architecture/training-logic responsibility. No fixed80% neural quota: winning validated competition performance is the goal.

Training-operations expansion is currently in progress. Do not claim that GPU optimization/resume or automated model-version comparison has already been validated. Only minimal necessary implementation smoke tests are authorized; no substantial training. We have run no match-data parameter updates. Use tiny labelled synthetic batches for the GPU/checkpoint functional test, preserving real models and history.

## Hard rules

- Never submit/login/activate a Battlecode bot. No browser/desktop control. GitHub source pushes are user-authorized.
- Write only in this workspace. `references/**`, old experiments, archives, SDK/maps/CLI inputs are read-only.
- Official cambc only, `--release`, default fuel; never override fuel. Keep `bot/src` flat.
- Default new heads remain untrained/off; inherited trained drafting stays separate. Recheck full teacher_exact byte identity after C++ changes.
- All local maps are reused benchmarks. No strength claim from plumbing, uniform logits, zero weights or lower fuel counts on changed trajectories.
- No new workers. Use the lead; the current session model is Codex based on GPT-6, exact served variant not exposed.

## Verified implementation milestone

- Direct heads: strategy, objective, role, bank, shop, move, combat, engage, under `nn_policy_*` flat modules.
- Canonical F12/K16 candidates independent of teacher ranking; observation173 floats/hash0x1346e3ba, action hash0x16df3b9e. Interpretation2/NFS2 stays separate from residual v1/NFS1.
- Compact untrained G4/E4/context4/head4 model:1056 parameters, checksum0x5a9d6349c9dc07b5, seeded20261024. New four-lane numeric kernels have synthetic and real-record parity.
- Metadata candidate bounds, authenticated candidate/execution reserves, generated direct budget from models/policy_v2_budget.json; reset/round-advance guards. model/budget.json is explicitly legacy v1.
- Cold capped fields refuse whole decisions for unknown distances. Geometry/anchor caches, target sorting and live selected-action guards avoid expensive repeated work.
- Early unverified-model failure reaches whole teacher before preparation. Late refusal ends safely instead of restarting the whole teacher on depleted fuel.
- Semantic commitments separated from recording IDs; exact guarded resumption. NOTE FOR NEXT FIX: current late fallback still closes macro intervals as interrupted even though semantic assignments are preserved. Since this fallback now only holds, it needlessly censors macro learning data. Keep live log intervals through a mere safe hold; close/censor only on actual abandonment/override/log cap, and adjust opportunity accounting/tests accordingly.
- Deferred checksum/base64/output, bounded per-champion records, per-head recording mask, persistent seed mixed with champion ID, queue drains after logging closes. Actual SDK acknowledgments and invalid-sample exclusion.
- Fixed draft telemetry crash and distant winning-carrier freeze. Successful urgent deposit records actual action ID; otherwise bank/movement remain available.
- Later tools: policy_train.py prepare/preflight/fit. Terminal Monte Carlo PPO/critic or explicitly annotated imitation, head-only update with frozen encoder, grouped splits, exact pinned behavior check, authorization, bounded epochs/deadline, atomic epoch checkpoint + recovery, f32 export. No real optimizer run yet. Current direct logs have no teacher annotations, so imitation collection is a follow-up; do not fabricate labels.

## Actual evidence

- Full Python280 tests PASS: artifacts/tmp/integration_verified_python.log. Legacy11targets460checks PASS: evaluation/results/integration_legacy_cpp.json. Tactics97 synthetic checks PASS, plus strategy actual SDK syntax/fixtures and economy fixtures.
- Final all-off source SHA2a834e481a378aa46cc19dd588a60940b40866e8d9894e2ceceb18c2230d7456. Full Wasm equals original:
  eb0ea88fc734661cf93935e5eab3c79e7a2658c7d05b7965593fbeb22d9d4442.
  Receipt: evaluation/results/integration_teacher_exact_final.json.
- Positive-gem banking + all builder/kernel/log components measured; complete/no invalid timings in integration_components.json. Raw probe6 under ignored artifacts/tmp. Not a universal worst-case proof.
- Final18game integration matrix: zero bot faults, zero invalid records,328 actual logit comparisons, max error8.940696716308594e-08. Two candidate exhaustions on islands, paired reference sides total17; not a causal improvement claim. All active untrained policies scored zero gems. integration_smoke.json has hashes, partial per-champion coverage and limits.
- Movement-only sampled checks yield sparse data: final four games only5 PPO-eligible rows. Current records alone do not meet fit minimum16train+4validation. Do not weaken masks or duplicate rows.
- All four direct development profiles officially build. Clean heads-off release packaged/independently rebuilt with full identical SHA:
  6d64d2a08aeda1998c1e6ab537cf716e195ba6e6047621a6bb83e51c440ad8c5.
  artifacts/release/2026-10-24/neural-framework-untrained.{zip,wasm,manifest.json,verification.json}.
  Clean release strips inherited lab exports and is distinct from teacher_exact. Two release smoke games: no faults/exhaustions, scores1003/965 on A and965/1003 on B. No strength claim.
- IMPORTANT packaging maintenance: models/budget.json and policy_v2_budget.json line endings were normalized after initial package; rerun package_release before final delivery to refresh SHA256SUMS. Further C++ baseline/commitment changes will require new identity/package checks too.
- Checklist review is a lead self-review, not an independent agent: evaluation/results/integration_review.md.

## Tools/environment

Verified CPU interpreter: ./artifacts/tmp/cpu_dev_venv/Scripts/python.exe (Python3.12.14, torch2.11.0+cpu, numpy2.5.2).
Native GCC: C:/msys64/ucrt64/bin/g++.exe; prepend C:/msys64/ucrt64/bin to PATH. Original read-only CUDA environment is config/paths.json python (old neural-gameplay/.venv), torch2.11.0+cu128, RTX5070Ti Laptop12GB previously verified; recheck for synthetic GPU smoke. Never install into or modify that old environment.

Set PYTHONPATH=$PWD/python, TMP=TEMP=$PWD/artifacts/tmp, PYTHONDONTWRITEBYTECODE=1. Official compiler/network calls work through reviewed escalation (`require_escalated`). Do not copy/proxy the installed compiler or change ACLs. Always use a fresh official teacher_exact checker directory; stale failed CMake caches can silently lose optimization flags.

Commands (verification, not training):

```powershell
& $py -m unittest discover -s tests/python
& $py tools/run_cpp_tests.py --json evaluation/results/integration_legacy_cpp.json
& $py agents/v2_strategy_integration/run_fixture.py --cxx C:/msys64/ucrt64/bin/g++.exe --sdk-syntax
& $py agents/v2_economy_integration/run_synthetic.py --cxx C:/msys64/ucrt64/bin/g++.exe
& $py agents/v2_tactics_integration/run_synthetic.py --compiler C:/msys64/ucrt64/bin/g++.exe
& $py tools/check_teacher_exact.py --out evaluation/results/integration_teacher_exact_final.json
```

## Ordered remaining work for latest user request

1. Fix macro-log continuity on a safe held turn, with regression tests. Full teacher fallback and actual interruption must remain distinct. Recheck all-off identity.
2. Add streaming metrics/checkpoint index/status interfaces and explicit device controls. Test GPU optimization + checkpoint/resume equivalence only on tiny labelled synthetic tensors, never match data or real exported models.
3. Add automated CLI comparisons against previous direct model exports and a genuinely non-neural baseline. Original is NOT fully non-neural because it includes the inherited draft net. Default gameplay NN macros are0; audit draft.cpp (draft_net.h at566, neural scoring near581/667) and add a gated explicit heuristic-draft baseline without changing default bytes. Keep baseline build separate, labelled ablation, not original-neutral.
4. Expose game/action inspection, structured run status, regular evaluation invocation/config and an operations handover suitable for a separate coding agent. Do not integrate/call Freebuff or a remote model now; use CLI interfaces.
5. Rerun only necessary tests/smokes for new changes, refresh docs/status and package. Current docs describe the earlier verified milestone; update them for new ops scope. All substantial training commands remain NOT RUN.
6. Commit verified milestone(s), push authorized GitHub main, then fresh-clone/configure/test the current development repo using existing CPU/native dependencies; no huge backup upload. Update HANDOFF/NEXT with exact final status and no live jobs before stopping.

No training on match data, parameter promotion, Battlecode submission or activation has occurred.
