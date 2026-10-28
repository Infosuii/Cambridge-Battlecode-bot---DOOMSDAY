# Deep analysis: replay retrieval and reconciliation complete

Updated 2026-10-28T16:04:21.416097+00:00. Replay access is restored. Session 1 resumes at D1-D11 detector implementation.

## Read first / next action

- Read REPLAY_RETRIEVAL.md, P0_SETUP.md, P1_DATA.md, P2_DETECTORS.md and RECONCILIATION.json.
- Preregister detector thresholds and validate event/visibility semantics on the five calibration games before running examined-game detectors. The existing own-perspective path still needs its own validation.
- Preserve the frozen split: 385 examined, 165 hands-off; five calibration games stay outside the study. Do not inspect hands-off decision trajectories or detector rates until final confirmation.
- Do not queue further wave 1 groups. Wave 2 has 10 groups remaining and requires FAST_FINDINGS.md plus written hypotheses/predictions/decision rules first.

## Verified intake (measured)

- Signed-in official website controls downloaded all 111 frozen groups / 555 games and 555 native JSON summaries. Every file exists on disk; both ZIP levels pass CRC checks. See DOWNLOADS.json for IDs, sizes and SHA256.
- Engine 2.0.0 / build 85aa7167b44db7cea97509f55e997750520e33d644e9f4f90d6128c50eba1d21; all three official asset pins pass.
- All 555 independent replay/native pairs pass: engine, outcome, rounds, final input, scores, champion gold/gems/kills, actual draft picks and dynamic physical roster.
- All 5,356 champion-body gem and gold conservation checks pass; five-game calibration passed before bulk decoding. No current pair is excluded for integrity failure.
- Accepted study n=550: existing version-69 catalog 450, wave 1 70, top-v-top 30. The remaining five catalog games are calibration only.
- No study trajectories have been manually reviewed. Hands-off decoding was automatic integrity validation only, with no decision or detector outputs exposed.

## Local files and reproducible commands

- This desktop checkout: work/battlecode-deep-analysis under the Battlecode project workspace. It is a full clone on analysis/deep-2026-10-28, not the earlier partial checkout.
- Raw ZIPs and partitioned replay/native files: artifacts/local-only/deep-2026-10-28/bundles and replays/{calibration-excluded,examined,hands-off}.
- Decoded actions: artifacts/local-only/deep-2026-10-28/decoded.jsonl (local-only; do not open hands-off rows for analysis).
- The first 375 decoded rows were retained; only the remaining 180 were newly decoded. Tools: deep_download_ingest.py, deep_decode_missing.py, deep_reconcile.py; usage in tools/README.md.
- Raw evidence is Git-ignored. The prior machine's raw catalog.json was not in Git. Existing-game outcomes agree with the frozen manifest; exact final states agree independently with native summaries. Wave/top metadata scores are additionally checked. Preserve this provenance limitation.

## Preserved study identity and boundaries

- Branch analysis/deep-2026-10-28; original parent working branch claude/compare-fix-replay-decoder at 294500b8c4da4af19a81f2cdb262305ea54d27f9. Preserve all unrelated entries; no force push.
- Study platform version 69, submission f91de3f0-0453-409e-b712-b86067eecbca, note “v75 ladder duel candidate”. This is the study identity, not a newly verified current activation. Later page listings include other versions; do not mix them.
- User bot (8).zip re-hashed to 0433755c1cbc5f120247c132a6c875912f14c3ac5f36abaa7edbfe20845b325c. Frozen bots/live-69/src remains unchanged; 33/33 blobs match. Server source hash and exact activation time remain independently unverified.
- Existing metadata: 455 games, 239W/216L, 91 groups. Wave 1: 14 groups/70 games, 10W/60L. No new group, ranked request, upload, activation or account change was made during retrieval.
- Learn/Climb membership and unequal exposure caveats remain in COHORTS.json. Historical failed downloads and old-engine archives remain quarantined; their access failures no longer block current replay intake.
- P2 is still a detector status/definition registry, not completed rates. FAST_FINDINGS.md, timelines, model, cards, deep track and final bot brief remain pending.
- Never submit, activate, request ranked games, edit frozen bots, expose credentials or bypass browser security barriers.
