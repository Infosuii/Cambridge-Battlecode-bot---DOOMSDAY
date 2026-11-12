# Agent H adversarial review checklist (apply to the integrated bot in the review wave)

Mark each item PASS, FAIL or N/A, and cite evidence: a file, a command and its output. A claim without evidence
counts as FAIL.

## A. Training/runtime parity
- [ ] The same `nn_config` decides sampling vs argmax: kTraining builds sample, release/dev builds take argmax. Check
      that the logged `logp_behaviour` is the probability of the executed choice under the exact masked logits
      (prior + R*tanh(r/R)), not under the unmasked or unbounded logits.
- [ ] Python `PolicyNet.head_logits` == C++ `nnh::decide` logits on recorded NFS1 decision records from a real
      training-profile match. Use real records, not only synthetic vectors. Measure the max abs error and the argmax
      agreement rate.
- [ ] Observation encode parity on real `RawTurn` captures (C vs Python), including padding rows, masks and the team
      B mirror transform.
- [ ] Multi-turn commitments: every round where an off-teacher choice persists is either logged as a decision or
      explicitly marked as committed (not a fresh sample). Discounting and option timing in G's trainer match.
- [ ] Stochastic semantics: the RNG seed and stream are per champion/episode, not shared across champions or reset
      every turn.
- [ ] Training-profile overhead (NFS1 logging) is measured on the `fuel_profile` schedule. Report how many decisions
      are lost or changed relative to the same profile with logging stubbed.

## B. Hidden lab or diagnostic work in release
- [ ] `tools/verify_release.py` passes on the packaged ZIP: profile release, no NFS1/NFT1 strings, no lab_* exports
      if strip is selected, independent rebuild identical.
- [ ] Grep the release translation units for `printf`, `puts`, `std::cout`, `cn_log`, `pol_log`, `macro_feat`,
      `lab::ctl`, `cn_force` and `builds` reachable with NN_TRAINING=0/NN_TELEMETRY=0. Each remaining one is justified
      (for example the original's `bot error:` handler).
- [ ] The data section strings of the release wasm are diffed against the original's. Every new string is explained.
- [ ] Profiling arrays (`prof`, `a2tel`, Meter scopes) compile out in release: the code section contains no
      references to telemetry globals.
- [ ] No forced-action / exploration hook (cn_force, lab ctl interventions, kSelfTest) is reachable in release.
- [ ] The lab strip changes behaviour vs the original (Agent A: 4/24 cells equal). The release build is evaluated as
      a variant. Its divergence is reported, not presented as teacher-equivalent.

## C. Neutral-mode overhead
- [ ] `teacher_exact`: wasm code section == original (or identical replays on all 24 equivalence cells).
- [ ] `neutral_credit`: identical replay+summary on all 24 cells; per-turn overhead (mean/p99/max) reported.
      Confirm kFuelCredit cannot leak into a release build.
- [ ] `neutral_real`: divergence reported (cells, first divergent round, outcome flips, margin delta). Do not
      describe it as neutral.
- [ ] Per-head shadow builds: which single head causes the largest divergence and fuel overhead.
- [ ] Shared-context cache: encoded once per (champion, round), invalidated at turn start. Count encoder runs per turn
      in telemetry (expected <= 1).
- [ ] Budget admission happens BEFORE feature work. Check that refused calls cost O(1) (telemetry fuel for refused
      calls ~ constant).

## D. Fuel tails
- [ ] fuelExhausted entries per scenario <= 1.25 x original + 4 (release). Report dev_untrained separately.
- [ ] `.fuel` tail: p99.9 and max per scenario vs the original baseline (`evaluation/results/reference/fuel_profile`);
      turns >= 95% of budget; last-quarter tail; first-turn (200k) and draft (1M) maxima.
- [ ] Compare low-fuel maps (01yellow-brick-road, 01islands) turn by turn. Neural work must not move turns from below
      the cap to at the cap.
- [ ] The teacher reserve is honoured: on turns where the teacher's own search would have run (fuel_remaining >
      A2_ROUTE_FUEL), neural spend did not push the remaining fuel below that threshold before the teacher choice
      was made.
- [ ] No unbounded loops: max turn fuel never at the cap in shadow/neutral builds where the original was below it on
      the same turn (action-identical cells only).

## E. Gate leakage and evaluation hygiene
- [ ] `python tools/eval_protocol.py verify` passes. The protocol sha256 equals the value in EVALUATION_PROTOCOL.md.
- [ ] `evaluation/ledger.jsonl` verifies (`Ledger.verify()`). Each final reservation precedes its results, one per
      sha256 and family. Overrides carry reasons, and the reasons are reported.
- [ ] Training configs and data manifests (G) contain no final-partition map, and checkpoint selection uses only
      selection maps. Grep configs, manifests and logs for every final map name.
- [ ] The number of selection evaluations per training run is logged and reported with any final result.
- [ ] Every results.json carries candidate sha256, reference sha256s, engine versions, profile and protocol sha256.
      Spot-check 3 cells by re-reading their summaries.
- [ ] Reports label maps `reused_benchmark`, label untrained smoke results "untrained framework check", and never
      present synthetic data as match evidence.
- [ ] No use of the fuel override anywhere (`verify_release` scripts check, plus a grep of logs for the flag).
- [ ] Reference binaries unchanged (`tools/eval_check.py refs`).

## F. Lifecycle honesty
- [ ] The registry lists each model's status. No untrained/teacher_initialized model is active in release, and
      `release_selection` lists only validated models.
- [ ] The independently recomputed weights checksum matches every manifest.
- [ ] The status report lists active trained heads (expected: none new; the inherited draft net is used by the teacher)
      and does not call untrained plumbing "learned".
