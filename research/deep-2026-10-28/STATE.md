# Deep analysis: Session 1 detector screen complete

Updated 2026-10-28T17:34:21.775493+00:00. Replay access is restored. Session 1 setup, intake and detector screen are complete; Session 2 is next.

## Read first / next action

- Read SESSION1_FINDINGS.md and P2_DETECTORS.md first; then DETECTOR_SPEC.json, DETECTOR_DATA.json and the earlier provenance reports.
- Start Session 2: timelines/decomposition/openings, then a calibrated win-probability model with splits by game and diverse loss/win cards. D3 repeated-death associations are the leading review candidate, not a causal fix. Do not modify registered thresholds based on the examined screen.
- Preserve the frozen split: 385 examined, 165 hands-off; five calibration games stay outside the study. Do not inspect hands-off decision trajectories or detector rates until final confirmation.
- Do not queue further wave 1 groups. Wave 2 has 10 groups remaining and requires FAST_FINDINGS.md plus written hypotheses/predictions/decision rules first.

## Verified intake (measured)

- Signed-in official website controls downloaded all 111 frozen groups / 555 games and 555 native JSON summaries. Every file exists on disk; both ZIP levels pass CRC checks. See DOWNLOADS.json for IDs, sizes and SHA256.
- Engine 2.0.0 / build 85aa7167b44db7cea97509f55e997750520e33d644e9f4f90d6128c50eba1d21; all three official asset pins pass.
- All 555 independent replay/native pairs pass: engine, outcome, rounds, final input, scores, champion gold/gems/kills, actual draft picks and dynamic physical roster.
- All 5,356 champion-body gem and gold conservation checks pass; five-game calibration passed before bulk decoding. No current pair is excluded for integrity failure.
- Accepted study n=550: existing version-69 catalog 450, wave 1 70, top-v-top 30. The remaining five catalog games are calibration only.
- All 385 examined games now have D1-D11 review flags: 360 DOOMSDAY games (191L/169W),25 top-v-top references. All current-code event/perspective checks pass; 3,945,308 own-turn states agree with omniscient states. Hands-off detector execution remains zero.

## Local files and reproducible commands

- This desktop checkout: work/battlecode-deep-analysis under the Battlecode project workspace. It is a full clone on analysis/deep-2026-10-28, not the earlier partial checkout.
- Raw ZIPs and partitioned replay/native files: artifacts/local-only/deep-2026-10-28/bundles and replays/{calibration-excluded,examined,hands-off}.
- Decoded actions: artifacts/local-only/deep-2026-10-28/decoded.jsonl (local-only; do not open hands-off rows for analysis).
- The first 375 decoded rows were retained; only the remaining 180 were newly decoded. Tools: deep_download_ingest.py, deep_decode_missing.py, deep_reconcile.py; usage in tools/README.md.
- Raw evidence is Git-ignored. Fresh public reads restored metadata for all 111 frozen groups / 555 games; IDs/maps/sides/engine/outcomes and native scores/rounds agree. The new restored-catalog.json is local-only. This is not the earlier machine's original raw snapshot.

## Preserved study identity and boundaries

- Branch analysis/deep-2026-10-28; original parent working branch claude/compare-fix-replay-decoder at 294500b8c4da4af19a81f2cdb262305ea54d27f9. Preserve all unrelated entries; no force push.
- Study platform version 69, submission f91de3f0-0453-409e-b712-b86067eecbca, note “v75 ladder duel candidate”. This is the study identity, not a newly verified current activation. Later page listings include other versions; do not mix them.
- User bot (8).zip re-hashed to 0433755c1cbc5f120247c132a6c875912f14c3ac5f36abaa7edbfe20845b325c. Frozen bots/live-69/src remains unchanged; 33/33 blobs match. Server source hash and exact activation time remain independently unverified.
- Existing metadata: 455 games, 239W/216L, 91 groups. Wave 1: 14 groups/70 games, 10W/60L. No new group, ranked request, upload, activation or account change was made during retrieval.
- Learn/Climb membership and unequal exposure caveats remain in COHORTS.json. Historical failed downloads and old-engine archives remain quarantined; their access failures no longer block current replay intake.
- P2 now contains measured examined-game flags, intervals and subtype limits. Registration commit 148d845 precedes processing; current source SHA256 c8308cd23efdb4b3824dcca96f8ab9dbba28ae99e22d5b640d6487f52f10c6ff. Calibration5/5, examined385/385,13 semantic cases,6 statistical cases pass. First screen preserved under detector-examined-v1; v2 adds explicit exposures without changing flags. FAST_FINDINGS.md, timelines, model, cards, deep track and final bot brief remain pending.
- Never submit, activate, request ranked games, edit frozen bots, expose credentials or bypass browser security barriers.

## Publication

Retrieval commit d9eba7b was explicitly approved and pushed. Registration 148d845
precedes examined processing. Check the local project STATE.md for later publication
status; do not assume a commit-specific approval authorizes later exports.
