You are the lead engineer continuing a partly finished build of a training-ready neural Battlecode bot. Coordinate
specialist sub-agents where useful, integrate their work yourself, and verify everything with real commands.

Workspace: `C:\projects\cambridge battlecode\work\neural-full-stack` (local git repo; continue from HEAD).

Read these before doing anything else, in this order:
1. `HANDOFF.md`: current state, verified facts, test commands, findings, open problems, ordered next steps.
2. `CONTRACTS.md`: binding interfaces and file ownership.
3. `agents/USER_REQUEST.md`: my full original specification. It is the definition of done. Sections 4, 5, 6, 9 and 10
   matter most for the remaining work.
4. `agents/*/REPORT.md` and `agents/*/CONTRACT_ISSUES.md`.

Hard rules (never relax):
- No training: no fine-tuning, no self-play learning runs, nothing that updates parameters on match data. Synthetic
  shape, parity and round-trip tests only, labelled synthetic.
- Do not submit, upload or activate anything. No `cambc submit`, no login, no browser or desktop control.
- Write only inside the workspace. The previous experiment (`work/neural-gameplay`), the historical archives and the
  CLI/SDK/maps are read-only. Never modify `references/**`.
- Use the official cambc CLI only, with `--release` and default fuel. Never pass `--fuel`.
- Be honest: untrained heads are untrained, and all local maps are reused benchmarks. Report mixed or failed results
  plainly; never claim strength gains.
- Keep `bot/src` flat. With every head off (profile `teacher_exact`), the bot must stay byte-identical to
  `references/builds/original.wasm`. Re-check this after every C++ change.

Start by running the verification commands in HANDOFF.md section 3, so you know the baseline still passes
(186 Python tests, 451/451 C++ checks, obs parity, teacher_exact byte-identical).

Then work through HANDOFF.md section 8:
1. Measure neural fuel costs in the engine with a probe build. Replace the provisional `models/budget.json` and shrink
   the default model if a decision is too expensive for the ≈100k-fuel turn.
2. Wave 2: strategy, draft, objective, role and value (D); move, combat, engage, ward and tactical-search leaf (E);
   bank and shop (F). For each head:
   - write a candidate builder that calls `nnh::decide()`, where candidate 0 is always the teacher's already-computed
     choice and legality stays deterministic;
   - add a per-head schema and a Python twin, plus a parity test;
   - add a compile-time-gated hook at the point listed in `agents/A/decision_inventory.json`.
   Keep the inherited draft network as a separate model.
3. Build every profile. Run plumbing, fuel and smoke checks against original, v47 and first-hour on both sides,
   labelled "untrained framework check". Use the overhead-matched neutral_real control arm, added to the frozen
   evaluation protocol as a recorded amendment.
4. Do an independent review using `agents/H/REVIEW_CHECKLIST.md` and fix what it finds.
5. Write the docs:
   - `ARCHITECTURE.md`, including the neural coverage matrix;
   - `DIAGNOSIS_AND_DESIGN.md`;
   - `TRAINING_LATER.md`, with commands labelled "not run", a bounded first experiment and its stop criteria;
   - `STATUS.md`;
   - an agent assignment and model record. Name the model actually used and do not invent agent runs.
6. Package the release profile (untrained heads off) into a ZIP, Wasm and checksums with `tools/package_release.py`.
   Verify it with `tools/verify_release.py`, including an independent rebuild. Do not submit.

Key finding to respect: the original bot's decisions shift with a few dozen fuel units spent before or while it
decides (`evaluation/evidence/neutral_equivalence_bisect.json`). Neural work that runs before teacher decisions must
stay minimal. Logging runs after `play_turn` from leftover fuel. "Zeroed weights" is not proof of neutrality.

Working style:
- Commit after each verified milestone.
- Keep scratch work in `artifacts/tmp/`.
- Agent completion messages are not proof: rebuild and test after integrating anything.
- Make routine decisions yourself. Ask me only about a genuine external blocker.
- Before you run out of budget, rewrite `HANDOFF.md` with the exact current state, then stop.

Finish when the full neural decision framework is integrated, tested and packaged, and the later-training workflow is
executable. State clearly that the result is ready to train, not trained.
