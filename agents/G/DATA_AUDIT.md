# Data audit: what the historical summaries contain, and which heads they can label

Agent G, 2026-10-24. Evidence: `data/manifests/archive_index_v1.json` (bounded index), `data/archive_sample_v1/sample_rows.jsonl`
(per-entry metadata of the 800 converted entries), `data/audit_samples/*.json` (three entries converted in full with
`cambc summary`), and one existing official 1.0.3 local summary from the previous diagnosis (read-only).

## 1. Bottom line

- The four usable 21 October parts contain **93,606 entries, 93,606 unique match IDs, 0 cross-part duplicates**.
- **No engine-1.0.3 entry was found.** In my fresh sample of 760 entries (190 per part, never sampled before) the mix was
  590 × 1.0.2 and 170 × 1.0.1. In the first experiment's 4,000 sampled entries, all 3,070 it accepted are 1.0.2 and 920 are 1.0.1 (and 3 part-1 forfeits are 1.0.2);
  7 forfeits in parts 2–4 have no recorded version (they passed its 1.0.2/1.0.3 filter). Across the 4,753 sampled
  entries with a known version, the 1.0.3 count is 0. If the sample is random (SHA-256 order of UUIDs), the 95 % upper
  bound on the 1.0.3 share is about 3/4,753 = 0.063 %, i.e. at most about 59 of the 93,606 entries. **These archives give essentially no current-engine gameplay labels or rewards.**
- They can give coarse, **observational** labels for the draft (composition → outcome) and for match-level outcome
  value, at engine 1.0.2, flagged `draft_observational`. Winning drafts are **confounded** by team strength: strong
  teams win with whatever they pick. Such labels show correlation. They do not show that a pick is good.
- Summaries contain **no per-turn observations, actions, positions, paths, ability uses or shop decisions**. Every
  low-level head (strategy, objective, role, bank, shop, move, combat, engage, ward, ts_leaf) must be trained from
  **our own instrumented rollouts** (NFS1 records written by the bot on its own stdout, plus the summary for
  rewards). That path is `collect` → `build-dataset` → `pretrain`/`rl`.
- All 40 maps in the accepted sample are the 40 local arena maps (map hashes match `sha256(map file)`). No
  archive map is new, so every map-level holdout is a `reused_benchmark`.

## 2. Date, engine and integrity evidence

| Check | Result |
|---|---|
| Date | Each entry's date is proven at bundle level only. ZIP member timestamps are the 1980 placeholder. A converted summary has only in-game `timestamp{round, substep, input, ordinal, phase}` and no wall-clock field (I checked every key recursively). All four parts are named `summaries-2026-10-21-partN.zip`, and the platform listing `archive-links.json` from the previous experiment (read-only) gives `date: 2026-10-21` for each. The filter admits a bundle only if both dates agree and are ≥ 2026-10-21. No archive dated 20 October or earlier exists locally; synthetic tests show they would be rejected whole. |
| Engine | `engineVersion` and `engineBuildHash` are recorded per entry. 1.0.2 = `ff41468c…`, 1.0.1 = `c3e9ffc8…`, local 1.0.3 = `fcb6c3e8…`. `rule_version` = `<engine>+<build12>/metrics<metricSemanticsVersion>/fmt<formatVersion>`. |
| Zero-byte | `21 october matches/summaries-2026-10-21-part1.zip` is 0 bytes. It is flagged `zero_byte_duplicate_part` and skipped; part 1 is read from `C:/projects/cambridge battlecode/summaries-2026-10-21-part1.zip`. |
| Truncation | The end-of-central-directory record, central-directory bounds and last-member data bounds were checked. All four parts are OK. |
| CRC | CRC-32 was verified for the 800 decompressed sample entries: 0 errors. Members outside the sample were not decompressed, so their CRCs were not checked. |
| SHA-256 | part1 `47e0899d…2b35`, part2 `4234d17b…d7ad`, part3 `951e9f32…7d22`, part4 `e8f1d001…1ecb`. Full values are in the manifest and cached in `data/manifests/sha256_cache.json`. |
| Experiment-1 overlap | All 4,000 IDs sampled by experiment 1 were found. They are stored as `already_used_by_experiment_1` in `data/manifests/experiment1_used_ids_v1.json`, kept out of the fresh sample, and never assigned to `final_eval`. The 40 re-converted IDs agree on engine version 40/40. One entry that experiment 1 accepted (`263c214a…`) is now rejected for `bot_fault`; experiment 1 did not filter faults. |

Bounded-sample verdicts for the 760 fresh entries:

| Reason | Count |
|---|---:|
| accepted, scope `draft_observational` (1.0.2) | 571 |
| accepted, scope `gameplay_1_0_3` | 0 |
| `engine_1.0.1_excluded` | 170 |
| `zero_score_tiebreak` (0:0 at 2000 rounds; the engine tiebreak decides, so the outcome carries no information) | 15 |
| `too_few_rounds` (< 50: forfeit or resignation) | 2 |
| `bot_fault` | 2 |
| CRC, conversion or capture failures | 0 |

Accepted rows: 343 unranked and 253 ranked (including the consistency rows), 463 distinct teams, 542 distinct team
pairs, and draft sizes 5 / 4 / 3 = 381 / 115 / 100.

## 3. What one summary contains

Three entries were converted in full: `000011b5…` (1.0.2, 60×60, 0:0 at 2000 rounds), `1291c7f9…` (1.0.2,
31×31, 198:1012) and `1913feda…` (1.0.1, 45×30, 1006:210).

| Section | Content | Granularity |
|---|---|---|
| `match` | engine version and build hash, metric/format versions, map hash, width/height, seed, outcome, rounds started/completed, final-round partial flag | per match |
| `roster.draft` | draft order as (team, champion) pairs; the first row is the first pick | per pick |
| `roster.champions` | champion id, name, team, draft pick index (Cassi and Issac appear as two champions from one pick) | per champion |
| `champions[]` | final metrics (17: assists, damage done/taken vs champions and monsters, collected/submitted/carried gems, gold, earned/spent gold, deaths, kills, healing, shielding, sale refunds); items/consumables held and bought | final totals |
| `championTimelines` | 17 metrics per champion, run-length encoded with `sampleCount = rounds + 1`. Verified: `gems` = currently carried gems, and collected = submitted + carried + lost to `gemLoss` | **per round, but aggregate counters only** |
| `teamTimelines` | `submittedGems` per team | per round |
| `events` | `death, kill, assist, wardPlacement, buyItem, buyConsumable, sellItem, campClear, gemSubmission, gemCollection, gemLoss, itemCombination, botFault, fuelExhausted, resignation`; each entry has `{amount, context, target, timestamp{round,…}, value, x, y}` | discrete events with a position |
| `heatmaps` | `death, kill, wardPlacement` counts per tile for the whole match (run-length over width×height) | spatial, no time |
| `diagnostics` | bot faults per team, codes, `detailedCaptureComplete` | per match |

Not present: per-turn champion positions or paths, observations or fog state, actions or ability casts, targets
chosen, movement endpoints, shop decisions with their alternatives, team memory and fuel per turn (only
`fuelExhausted` events). Event positions give where a death, ward or collection happened, not the decision or the
state behind it.

## 4. Which heads can get defensible labels from where

| Head | From archives (1.0.2, observational) | Needs own instrumented rollouts (NFS1) |
|---|---|---|
| draft_pick | composition → outcome value (confounded; side and first pick available). Not a 1.0.3 label. | the inherited `draft_net_original` stays the teacher; RL draft labels need engine games |
| value (win/margin) | coarse match-level outcome given draft and map only; there is no in-game state to condition on | per-turn value: our records' observations + summary outcome |
| strategy, objective, role | none (no per-turn state or decision) | teacher labels (candidate 0) and sampled actions from records |
| bank, shop | none (purchase events lack state and alternatives; deposits lack the decision) | records |
| move, combat, engage, ward, ts_leaf | none (no positions or actions per turn) | records |
| belief | none (no enemy positions per turn; replays could reconstruct them, but this was not audited) | records + own sightings |
| reward shaping | 1.0.2 timelines would only illustrate scale; they are not used for rewards | rewards come only from 1.0.3 summaries of our own games (`rewards.series_from_summary`) |

Enforcement in code:
- `archives.gameplay_label_records` raises `EngineCompatibilityError` for any 1.0.2 record unless an explicit,
  tested `EngineAdapter` (1.0.2→1.0.3) is passed. None exists. 1.0.1 is refused even with an adapter.
- `records_dataset.convert_match` refuses summaries that are not 1.0.3.
- `value.train_draft_outcome` labels its output `draft_observational`, `confounded=True`.

## 5. Observation integrity of the record path

- Inputs come only from the acting team's own stdout (turn-context and decision records). They are the bot's legal
  observation by construction. The other team's stream, the replay's full state and the summary are never inputs.
- The summary is used only for targets: the return, outcome, margin and reward components of each interval.
- The `Shard` structure keeps `inputs` / `targets` / `meta` separate, rejects undeclared fields and input names
  containing outcome or future tokens, and the tests show that flipping the outcome changes targets but leaves
  every input array byte-identical.
- Gap: replay files (`.repl26a`) contain full state. Reconstructing a team's legal observation from them was **not
  implemented**. It would need C's visibility rules and was not needed for the own-rollout path.
