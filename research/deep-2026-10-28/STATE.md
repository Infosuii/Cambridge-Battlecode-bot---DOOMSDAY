# Deep analysis: Session 1 checkpoint

Updated 2026-10-28T12:53:39.380580+00:00. **Session 1 is partially complete; replay access is the blocker.**

## Phase and next action

Setup/source freeze, cohorts, metadata catalog and wave1 complete. Resume at §2.1
five-game replay/native reconciliation, then §3 accepted ingestion and §4 detectors.
Obtain current replay bundles with native summaries through a working official
download or user-supplied files. Browser replay controls returned nonexistent
paths; CLI is unauthenticated and login starts refused before credential entry.
Do not extract browser cookies/tokens or bypass the blocked source download.
Do not queue more wave1 groups or repeat confirmed requests.

## Preserved state

- Branch:analysis/deep-2026-10-28; parent working branch:claude/compare-fix-replay-decoder.
- Parent commit:294500b8c4da4af19a81f2cdb262305ea54d27f9. Partial checkout;
  remote tree commits must preserve all untouched entries. No force push.
- Live platform 69/submission f91de3f0-0453-409e-b712-b86067eecbca Active/Verified;
  note“v75 ladder duel candidate”. Exact activation time unknown.
- Correct user bot.zip: 33 files; 29 match v58. Frozen unchanged in bots/live-69/src.
  ZIP0433755c1cbc5f120247c132a6c875912f14c3ac5f36abaa7edbfe20845b325c.
  All 33 remote Git blobs equal the ZIP. Server source hash independently unverified.
- Existing v69 metadata:455 games (239W/216L),91 captured groups.
  Actual authenticated version filter avoids v67 games in the same time window.
- Wave 1:14 groups/70 games, all finished; 10W/60L.
  Every group's actual own version 69, maps, sides and opponent checked. SCRIMMAGES.json
  holds all IDs/results/pins. Wave 1 budget 0 remaining; wave 2 budget 10 remaining.
- Learn:current top5. Climb:eight spaced ranks 15–40 plus top3 observed loss counts.
  Source snapshot and overlap/unequal-exposure caveats are in COHORTS.json.
- Top-v-top metadata:n=30; accepted decoded/reconciled games:n=0.
- Native integrity:2 summaries/19 champions pass; independent replay pairs:n=0.
- CLI 4.0.0 and engine 2.0.0 pinned. Decoder imports shared loader; syntax/pins/
  instantiation pass. Do not treat that as five-game decoder validation.
- Candidate partition seed 20261028:385 examined/165 hands-off;
  5 calibration-excluded. Preserve IDs through reconciliation. No trajectories reviewed.

## Files and resumption rules

Read P0_SETUP.md, P1_DATA.md, P2_DETECTORS.md, WAVE1_RESULTS.md and the JSON ledgers.
Raw evidence stays artifacts/local-only/deep-2026-10-28 (never commit raw replays).
DOWNLOAD_EXCLUSIONS.json records failed/ambiguous downloads and old-engine caches.
P2 is a blocker/status registry, not completed detector implementation or rates.
No FAST_FINDINGS.md exists; wave2 requires it plus written hypotheses first.
Never submit, activate, request ranked games, edit frozen bots or expose credentials.
