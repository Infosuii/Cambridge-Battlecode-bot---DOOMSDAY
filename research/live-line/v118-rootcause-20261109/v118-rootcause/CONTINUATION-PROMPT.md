# Continuation prompt: DOOMSDAY Battlecode, v118 cycle (written 2026-11-09)

Paste everything below into a fresh agent session on this same Windows machine.

---

You are continuing the DOOMSDAY (team) Cambridge Battlecode 2026 bot-improvement cycle on this laptop. You have the user's full creative freedom to find and fix what goes wrong in the bot. They want more time spent coding real fixes and less on testing, and local compute is unlimited (20 threads, RTX 5070 Ti). Don't submit to the ladder until a candidate passes its pre-registered checks and the user has seen the result. The user has said ladder release is fine once checks pass.

## Key locations (absolute paths)

- Work root (all scripts run from here; Python 3.13 + numpy + torch 2.11.0+cu128 at `C:\Users\omdha\AppData\Local\Programs\Python\Python313\python.exe`):
  `C:\Users\omdha\.codex\worktrees\agentic-findings-publish-20261107\x1resume\v113-integration-20261108`
- This cycle's work folder (scripts, traces, results, protocols): `...\v113-integration-20261108\v118-rootcause\`
  - **Read first:** `FINDINGS.md` (all mechanisms, numbers and classifications; §8 covers session 2).
  - Candidate source transforms: `candidates.py` (H, D, R, N, O, L, C, A, W), `cand_k.py` (K), `cand_k2.py` (Q = lethal-only camp safety, T = late-bank ordering), `cand_z.py` (Z, parked). C++ snippets: `home_siege.py`, `cs_funcs.inc`, `cs_funcs_lazy.inc`. Build any combo with `candidates.build('<name>', '<letters>')` after importing `cand_k2` / `cand_z`. Builds always start from `arena\bots\hp01` (v117).
  - Evaluation: `eval2.py <label> <cands> <base> both` (incident maps + 2,704-game paired dev panel, reusing cached base cells); `dev_panel.py`; `incident_checks.py`; `activation.py <maps>` (debug activation counts).
  - Trace builds (debug-only printf; free in debug builds): `trace_objectives.py`, `crew_test.py`, `trace_islands*.py`, `trace_outnumbered.py` + `outn_deaths.py`, `trace_bag.py` (+ `bag_snippet.inc`), `trace_camplow.py` (+ `camplow_snippet.inc`), `map_census.py`.
  - Protocols: `release-protocol.json` (v1; v18HDR failed G4 on the published holdout, `holdout-result.json`) and **`release-protocol-v2.json` (pre-registered, not yet run)**. Map split: `map-split.json` (88 dev / 40 holdout published maps).
  - Training: `train_v118.py`, `training-plan.json`, `weights_arms.py`, `rl_logger.py` (the NRQ recorder patch v117 lacked). Checkpoints are in `...\v113-integration-20261108\training\v118-hdr\`; resume from `resume_6.pt`. Trained and blended weights did not beat the frozen weights.
- Bots: `...\v113-integration-20261108\arena\bots\<name>\src`
  - `hp01` = v117 (live, ladder version 117).
  - `v18HDR`, `v18HDRW`, **`v18HDRWTQ` (current candidate)**, plus all other variants.
- Release packages: `...\v113-integration-20261108\release\`
  - `v18HDRWTQ\` (source.zip, bot-injected.wasm, manifest.json, `approved_for_upload: false`, confirmation pending).
  - `v18HDR\`
  - `hp01\` (v117, with `ladder-receipt.json` = rollback reference).
- Sealed fresh confirmation maps (unused): `...\v113-integration-20261108\arena\maps_v118_confirm\` (96 maps, seed 261110118, manifest sha256 `e780c1231e8ae352f328ec5c4dcb7466682a5f692307a96487f8bb5224c08afb`).
- Other map sets:
  - `...\arena\maps_v113_stability` (113 generated, used for dev)
  - `...\arena\maps_sw08_followup` (used once for report-only confirmation)
  - published pool list: `...\v113-integration-20261108\published-maps.json` (files under `C:\projects\cambridge battlecode\work\agentic-improvement\arena\maps`).
- Panels (every game's native summary + replay): `...\v113-integration-20261108\panels\<label>\` (`results.json` per panel). The 25 GiB workspace cap is enforced by `local_panel.storage_guard` (~13 GiB used).
- New ladder data (v117, 175 games, 73 losses): `...\v113-integration-20261108\ladder-new-20261109\`
  - `fetch_new.py`, `summarize.py`, `matches.json`, `games.json`
  - `death_context.mjs` + `death-context.json` (decoded pre-death windows)
  - `matches\<id>\native.json.gz`, `replay.zip`
- Earlier evidence: `...\v113-integration-20261108\ladder-loss-analysis-20261109\` (LOSS-ANALYSIS.md, 286 loss replays) and `...\v113-integration-20261108\DOOMSDAY-v117-handoff\`.
- Portable handoff of session 1: `...\v113-integration-20261108\DOOMSDAY-v118-handoff\`. GitHub branch `research/v118-rootcause-20261109` on `https://github.com/Infosuii/neural-networkk-battlecode` (repo checkout: `C:\Users\omdha\.codex\worktrees\agentic-findings-publish-20261107\x1resume`; it is a **sparse checkout**, so use `git add --sparse`; leave it on branch `research/agentic-improvement-20261107` afterwards).
- Shared tools in the work root: `project.py` (paths, engine identity, `build`), `local_panel.py` (`run()`: paired panels, 18 workers), `sw08_followup.py` (`build_from`), `ladder_transport.py` / `deliver_cycle.py` (ladder receipts), `policy_rows.py` (`stdout()` reads bot logs from replays), `stall_campaign.py` (`analyze()` replay stall audit), `references.json` (local opponent Wasm, now including `hp01`).
- CLI: `C:\projects\cambridge battlecode\work\agentic-improvement\runtime\cambc.exe` (5.0.0; run from `...\work\agentic-improvement\arena` for ladder commands, with `CAMBC_NO_UPDATE_CHECK=1`). The user signed in on 2026-11-09 (sessions last 7 days). If it says "Sign in first", ask the user to approve `cambc login` (it prints a browser link). Never enter credentials yourself.
- Replay decoder: `C:\projects\cambridge battlecode\work\agentic-improvement\autonomy\replay\engine.mjs`; map generator: `...\autonomy\replay\generate_maps.mjs <dest> <count> <seed>`.
- Memory notes: `C:\Users\omdha\.claude\projects\C--projects-cambridge-battlecode\memory\battlecode-v118-rootcause.md`.

## State and verified facts

- Live ladder: v117 (hp01), active and not pinned at the last check (14:51Z). Teammate branch `claude/v115-fuel-merge-1109`: v115 was cancelled and the team pinned to v106 overnight (before v117). Recheck before any change.
- `v18HDRWTQ` = v117 + H (Homonoliths home siege; spawn heal is 1.0) + D (relaxed dash at chained hole bridges) + R (route cooldown vetoes neural target) + W (winning bags never shelved, may bank at any HP near altar) + T (late-bank ordering) + Q (lethal-only camp safety). Dev: +31 vs v117 over 2,740 paired games, zero faults. Targeted incidents are fixed in release builds (Homonoliths median first home capture r1,353 → r417; Islands 7/18 → 15/18).
- Native `death` events: **owner = the champion that died**, entry target = killer. Timelines miss the final partial round; use `teams[].submittedGems`.
- Any code change diverges 65–90% of games (fuel-limited chaos): paired 2,700-game panels carry about ±50-point 90% intervals. Cold-path fixes (W, T) diverge little and measure cleanly. **Per-turn hot-path work costs games** (C's world-update cost lost 76).
- Parked: N/O/L numbers gates (passivity loses kills), Z, K/C (general camp penalties), retrained/blended weights.

## Do next, in order

1. Run the pre-registered confirmation once, from the work root: `python v118-rootcause\confirm_v2.py v18HDRWTQ`. It writes `v118-rootcause\confirm2-v18HDRWTQ.json` with gates P2–P6. Check P1 from `incident-checks.json` and `v118-eval-wtq.json`.
2. If all gates pass: recheck the active version (`python -c "import sys;sys.path.insert(0,'.');from ladder_transport import detail;d=detail();print(d['active']['version'])"`). Then mark the package approved, upload with a unique note, verify compilation and activation (reuse the `deliver_cycle.deliver` pattern: pin incumbent, submit, reconcile by note, activate), and record the receipt and the previous version (117). If a gate fails, don't submit; investigate as FINDINGS §6–8 describe.
3. Keep improving (see FINDINGS §8 "Next levers"): fights inside awake camp range without losing kills; burst deaths in outnumbered team fights vs item-fed Vesper Vale (consider `bots/proxy` or ladder match groups for opponent-realistic tests); the `flee` mover. Prefer cold-path or lazy code; trace with debug `debug_block` prints before changing behavior.
4. Shell gotcha: Bash heredocs on this machine collapse `\\n`. Write Python and C++ with the file-writing tool, or keep C++ snippets in `.inc` files.
