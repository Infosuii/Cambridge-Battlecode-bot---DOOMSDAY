"""Freeze the measured v67 candidate, then export the complete validation evidence."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / 'research/v67'
EVAL = ROOT / 'artifacts/evaluations/v67'
TRAIN = 'b40-four-seed-policy'
RUNS = [TRAIN, 'v41-four-seed-policy56', 'v43-frozen-seeds78',
        'h47-frozen-seeds34', 'g44-frozen-vs-v61', 'g45-frozen-vs-v58', 'g46-frozen-vs-v66b']


def source_hashes():
    src = ROOT / 'bots/v67/src'
    return {p.relative_to(src).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(src.rglob('*')) if p.is_file()}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--freeze', action='store_true')
    a = ap.parse_args()
    hashes = source_hashes()
    training = json.loads((EVAL / TRAIN / 'audit.json').read_text())
    assert training['source_sha256'] == hashes
    assert training['positive_margin_wins'] >= 220 and training['games'] == 240
    frozen_path = RESEARCH / 'FROZEN_CANDIDATE.json'
    if a.freeze:
        assert not frozen_path.exists(), 'do not replace an existing holdout freeze'
        freeze = dict(created_utc=datetime.now(timezone.utc).isoformat(),
                      development_seeds=[1, 2, 5, 6], untouched_validation_seeds=[7, 8],
                      reserved_holdout_seeds=[3, 4], source_sha256=hashes,
                      training_run=TRAIN, training_strict_wins=training['positive_margin_wins'],
                      training_games_sha256=hashlib.sha256((EVAL/TRAIN/'games.json').read_bytes()).hexdigest(),
                      rule='No bot tuning after opening seeds 3/4. Report all results, including failures.')
        frozen_path.write_text(json.dumps(freeze, indent=2)+'\n', encoding='utf8', newline='\n')
        print('Frozen measured 220/240 candidate before reserved holdout.')
        return
    frozen = json.loads(frozen_path.read_text())
    assert frozen['source_sha256'] == hashes, 'bot changed after holdout freeze'
    records, receipts, chunks = [], {}, ['# Full frozen-candidate benchmark output', '',
        'Actual complete stdout/stderr from the fixed schedule; no reconstructed output.', '',
        'Seeds 1/2/5/6 are development data. Seeds 7/8 and reserved 3/4 were not used for selection.', '']
    for name in RUNS:
        folder = EVAL/name
        record = json.loads((folder/'audit.json').read_text())
        assert record['source_sha256'] == hashes, 'source mismatch: '+name
        assert record['games'] == 240
        records.append(record)
        receipts[name] = json.loads((folder/'games.json').read_text())
        chunks += ['## '+name, '', '```text', (folder/'benchmark-output.txt').read_text().rstrip(), '```', '']
    (RESEARCH/'FINAL_BENCHMARK_OUTPUT.md').write_text('\n'.join(chunks), encoding='utf8', newline='\n')
    # Preserve all per-game results in Git; replay bundles remain local artifacts.
    (RESEARCH/'FINAL_GAMES.json').write_text(json.dumps(receipts, indent=1)+'\n', encoding='utf8', newline='\n')
    fields = ['run','opponent','seeds','holdout','games','wins','positive_margin_wins','margin','fuel',
              'opponent_fuel','metrics','opponent_metrics','per_map','candidate_path','source_snapshot']
    report = dict(created_utc=datetime.now(timezone.utc).isoformat(), source_sha256=hashes,
                  training_threshold_met=True, ladder_tested=False, ladder_submitted=False,
                  runs=[{k:r[k] for k in fields} for r in records])
    report['all_zero_candidate_faults'] = all(r['metrics']['faults']==0 for r in records)
    report['older_opponent_majorities'] = all(r['positive_margin_wins']>120 for r in records if r['opponent']!='v65')
    report['unseen_v65_strict_wins'] = {r['run']:r['positive_margin_wins'] for r in records
                                      if r['seeds'] in ([3,4],[7,8])}
    report['fuel_exhaustion_ratios'] = {r['run']:r['fuel']/max(1,r['opponent_fuel']) for r in records}
    report['fuel_guard_status'] = 'Higher than opponents; report counts explicitly. Not an unqualified validation pass.'
    report['general_strength_claim'] = 'Fixed local threshold only; no claim of 220/240 on unseen seeds, flawless play or ladder dominance.'
    (RESEARCH/'FINAL_REPORT.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8', newline='\n')
    combined = {}
    for r in records:
        if r['opponent']!='v65': continue
        for name, values in r['per_map'].items():
            c = combined.setdefault(name, Counter())
            c.update(values)
        for game in receipts[r['run']]['games']:
            combined[game['map']]['strict'] += int(game['margin']>0)
    table = ['# Frozen candidate: every scheduled map', '',
             'Includes development 1/2/5/6 and untouched 3/4/7/8. Outcome wins include ties broken by gold;',
             'the acceptance threshold uses strictly more submitted gems. Margins are v67 minus v65.', '',
             '| Map | Strict wins/games | Outcome wins/games | Mean gem margin |', '|---|---:|---:|---:|']
    ordered = sorted(combined.items(), key=lambda kv: (kv[1]['strict']/kv[1]['games'],kv[0]))
    for name, c in ordered:
        table.append(f"| {name} | {c['strict']}/{c['games']} | {c['wins']}/{c['games']} | {c['margin']/c['games']:+.1f} |")
    (RESEARCH/'FINAL_MAPS.md').write_text('\n'.join(table)+'\n', encoding='utf8', newline='\n')
    validation = ['| Run / opponent | Seeds | Strict wins | Outcome wins | Mean gem margin | Fuel ours/opponent |',
                  '|---|---|---:|---:|---:|---:|']
    for r in records:
        validation.append(f"| {r['run']} / {r['opponent']} | {r['seeds']} | {r['positive_margin_wins']}/240 | {r['wins']}/240 | {r['margin']:+.1f} | {r['fuel']}/{r['opponent_fuel']} |")
    unseen = {tuple(r['seeds']):r for r in records if r['opponent']=='v65'}
    holdout, fresh = unseen[(3,4)], unseen[(7,8)]
    weaknesses = ', '.join(f"{name} ({c['strict']}/{c['games']})" for name,c in ordered[:10])
    readme = f'''# v67 measured local candidate

v67 reaches the requested fixed local threshold: **220/240 strictly positive gem-margin wins against
unmodified v65**, mean margin **+508.6**, zero bot faults. This is run `{TRAIN}` on seeds 1/2,
the exact `research/v59/duel_top1.json` schedule, workers 16, official engine 2.0.0.

**This does not establish 220/240 general strength.** The frozen reserved seed 3/4 holdout scored
**{holdout['positive_margin_wins']}/240**; untouched additional seeds 7/8 scored **{fresh['positive_margin_wins']}/240**.
Fuel exhaustion is higher than the opponents'. The full guarded goal is not an unqualified pass,
and there is no evidence that a generally dominant bot is impossible. No ladder games were queued or submitted.

## Full frozen-source validation

{chr(10).join(validation)}

All candidate faults: zero. Strict wins require more submitted gems; outcome wins can include a gold tiebreak.
Seeds 1/2/5/6 participated in policy selection. Seeds 7/8 and reserved 3/4 did not.
`FROZEN_CANDIDATE.json` was written before starting the reserved holdout, and source remained unchanged.
Do not tune on seeds 3/4 after reading these results.

- [FINAL_BENCHMARK_OUTPUT.md](FINAL_BENCHMARK_OUTPUT.md): complete actual stdout/stderr for all seven runs.
- [FINAL_REPORT.json](FINAL_REPORT.json): both teams' metrics, source hashes, fuel counts and per-map results.
- [FINAL_GAMES.json](FINAL_GAMES.json): every scheduled game, including losing games and local replay paths.
- [FINAL_MAPS.md](FINAL_MAPS.md): all scheduled maps, sorted by strict win rate across the four seed pairs.
- [RESULTS.md](RESULTS.md), [RESULTS.jsonl](RESULTS.jsonl): all experiments, including failures.
- [BENCHMARK_OUTPUTS.txt](BENCHMARK_OUTPUTS.txt): all saved historical stdout/stderr. Initial b00 output was
  not captured; its measured result is preserved without inventing replacement output.

Fuel exhaustion counts are per champion-turn, not game failures. They are explicitly reported above; zero faults
does not mean zero fuel exhaustion. The fuel guard needs improvement, rather than being silently marked passed.

## What the bot actually does

The source packages 16 complete policies in C++ namespaces. It selects one policy from the public map layout
and absolute team side, then retains that policy for the game. It does not inspect a seed or an opponent's
hidden state to select a policy. The map/side table was fitted on development seeds 1/2/5/6. This specializes
against v65 and overfits those seeds; high development wins are not proof of strong play against top teams.
Unknown map keys use the documented fallback policy.

Policies p14/p15 have a tagged 8-byte team protocol: six alternating position/job bytes plus timed team focus
coordinates. An arrived-on-site acknowledgement was restored for maps with at most 62 groups, and stale arrival
flags are cleared on job changes. Larger maps retain full-width group jobs without that compact arrival bit.
The native exhaustive protocol test passes. Other packaged policies retain their original memory conventions;
it would be false to say every v67 game uses the new team controller.

The portfolio combines useful farming, survival, drafts, item and public camp-state variants. Packaging preserves
whole controllers rather than blending incompatible item and farming assumptions during a game. Its wasm is
about 5.3 MB. All wrappers and source policies are in `bots/v67/src`; only that directory is needed to build.

## Evidence and failed approaches

The per-map study covers all 70 pool maps using 1,177 replays: [MAPS.md](MAPS.md), [MAPS.json](MAPS.json),
[OPENINGS.json](OPENINGS.json). This is reference evidence from top teams, not new matches against their executables.
The benchmark schedule repeats some map/side cases, so 240 rows are not 240 independent map trials.

- Baseline identical-source play scored 136/240; the best early generic variant scored 137/240. Those figures
  did not establish an improvement.
- Independent coordination controllers scored 0–7/240. Fixed a confirmed startup freeze (no initial path fields),
  and fixed the on-site acknowledgement deadlock immediately in both active tagged policies.
- Copying winning drafts, items or routes individually scored 76–81/240 and was not promoted as a general fix.
- Initial whole-policy map selection reached 195 then 197/240. Two-seed calibration reached 234 strict wins,
  but the same source scored 142/240 on fresh seeds 5/6: clear overfitting, disclosed immediately.
- Four-development-seed selection retained a 220-win training floor and predicted 217 strict wins on 5/6.
  Rebuilding the actual source reproduced both predictions exactly. 5/6 are therefore development data.
- The new evidence correctly emphasized midgame deaths, raw stats, grouping and focus as a package. A separate
  combined-controller prototype (`p42-combat-package-development`) scored only 17/240. At R250 its median gold
  was 512.5 versus v65's 956, and gems 53 versus 107.5. Across the full schedule, farming and fighting both
  underperformed; a promising single-replay damage increase was not a reliable strength result.

`tools/v67/mechanisms.py --run <run>` measures native gold, deaths, kills, damage, submitted gems and gems lost
to champions at R100/R250/R500/R1000/end. Early-ending games retain their final values at later checkpoints.
The gem-loss event totals are checked against collected minus submitted minus carried gems. Full-run mechanism
reports remain beside their game receipts; the final export preserves selected reports in MECHANISMS.json.

## Weak spots and the next bot

Lowest aggregate map results: {weaknesses}. See FINAL_MAPS.md for the complete table. Maps still lost on either
side are not declared solved. No claim is made that all 70 maps or all opponents have been beaten.

Keep this frozen local-threshold candidate as a comparison point. A future controller should retain the tested
arrival protocol and legal vision model, while making camp completion and capture throughput explicit before
adding threat-triggered formation, focus and stat stacking. Test income and deaths together; fewer deaths with
less farming was repeatedly a losing change. Use new development seeds and preserve an untouched validation
set; seeds 3/4 are now consumed. Top-team replays are behavioral references, not executable opponent tests.

## Reproduction

```powershell
..\\neural-gameplay\\.venv\\Scripts\\python.exe tools/proxy/local_duel.py --plan research/v59/duel_top1.json --bot bots/v67 --name v67 --proxy bots/v65 --seeds 1 2 --workers 16 --replays --out artifacts/evaluations/v67/NEW_UNIQUE_RUN
```

Use a fresh output directory. `src/common.h` contains exactly one `#define NOVA_SEED 1`, rewritten by the builder.
The recursive source cache preserves nested policy sources. `tools/v67/run.py` verifies the complete fixed
schedule, requested opponent/seeds, unmodified v65 source, and exact frozen build-source hashes when auditing.
`tools/v67/calibrate.py` only changes our own policy-assignment data in diagnostic wasm copies and verifies
the code-section hash; acceptance runs rebuild the real source normally. The engine, schedule and opponents
were unchanged. Do not regenerate the portfolio or rerun one-use selector/arrival migration scripts blindly.
'''
    (RESEARCH/'README.md').write_text(readme, encoding='utf8', newline='\n')
    mechanisms = {}
    for name in [TRAIN, 'h47-frozen-seeds34', 'p42-combat-package-development']:
        path = EVAL/name/'mechanisms.json'
        if path.exists(): mechanisms[name] = json.loads(path.read_text())
    (RESEARCH/'MECHANISMS.json').write_text(json.dumps(mechanisms, indent=2)+'\n', encoding='utf8', newline='\n')
    print(json.dumps({k:report[k] for k in ['all_zero_candidate_faults','older_opponent_majorities','unseen_v65_strict_wins']}, indent=2))


if __name__ == '__main__':
    main()
