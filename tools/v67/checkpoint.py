"""Refresh a truthful checkpoint using measured runs matching the live source."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
research=ROOT/'research/v67'
records=[json.loads(line) for line in (research/'RESULTS.jsonl').read_text().splitlines() if line.strip()]
best=max(records,key=lambda r:(r['wins'],r['margin']))
hashes={p.relative_to(ROOT/'bots/v67/src').as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((ROOT/'bots/v67/src').rglob('*')) if p.is_file()}
frozen=json.loads((research/'V65_SOURCE_SHA256.json').read_text())
assert all(hashlib.sha256((ROOT/'bots/v65/src'/name).read_bytes()).hexdigest()==sha for name,sha in frozen.items())
matching=[r for r in records if r['source_sha256']==hashes]
training=[r for r in matching if r['opponent']=='v65' and r['seeds']==[1,2] and r['games']==240]
assert training, 'live source has no complete fixed-schedule development benchmark'
latest=training[-1]
holdouts=[r for r in matching if r['holdout'] and r['seeds']==[3,4] and r['opponent']=='v65']
guards={op:[r for r in matching if r['opponent']==op] for op in ['v61','v58','v66b']}
chunks=['v67 actual saved benchmark stdout/stderr',
        'b00 baseline output was not saved by the initial runner. Its measured result is in RESULTS.md/jsonl; no replacement output is invented here.', '']
outputs=[]
for folder in sorted((ROOT/'artifacts/evaluations/v67').iterdir()):
    p=folder/'benchmark-output.txt'
    if p.is_file():
        chunks+=['='*80,folder.name,'='*80,p.read_text(encoding='utf8'), '']
        outputs.append(str(p.relative_to(ROOT)).replace('\\','/'))
(research/'BENCHMARK_OUTPUTS.txt').write_text('\n'.join(chunks),encoding='utf8',newline='\n')
strict=latest.get('positive_margin_wins',0)
manifest=dict(created_utc=datetime.now(timezone.utc).isoformat(),status='fixed_local_threshold_met' if strict>=220 else 'unfinished',
              target_wins=220,target_games=240,target_met=strict>=220,clear_impossibility_evidence=False,
              complete_experiments=len(records),current_run=latest['run'],current_wins=latest['wins'],
              current_margin=latest['margin'],best_run=best['run'],best_wins=best['wins'],best_margin=best['margin'],
              current_strict_wins=strict,source_matched_runs=[r['run'] for r in matching],
              holdout_seeds_3_4_used=bool(holdouts),guards_against_v61_v58_v66b_run=all(guards.values()),ladder_submitted=False,
              current_source_matches_latest_benchmark=True,current_source_sha256=hashes,
              benchmark_outputs=outputs,live_benchmark_processes=0)
(research/'CHECKPOINT.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8',newline='\n')
lines=['# Current checkpoint','',
       f"Current source: **{latest['run']}, {strict}/240 strict gem-margin wins**, mean margin {latest['margin']:+.1f}.",'',
       'Read README.md, FINAL_REPORT.json and FINAL_BENCHMARK_OUTPUT.md for validation and limitations.',
       'The fitted local threshold does not establish 220/240 on unseen seeds or the ladder. Fuel exhaustion is higher.',
       'Do not tune on reserved seeds 3/4 after their frozen validation. v65/mimic unchanged; no ladder submission.',
       'CHECKPOINT.json records exact live source hashes. Historical source snapshots remain in local artifacts.','',
       '| Source-matched run | Opponent | Seeds | Strict wins | Fuel ours/opponent |','|---|---|---|---:|---:|']
for r in matching:
    lines.append(f"| {r['run']} | {r['opponent']} | {r['seeds']} | {r.get('positive_margin_wins','unrecorded')}/{r['games']} | {r['fuel']}/{r['opponent_fuel']} |")
(research/'WORKLOG.md').write_text('\n'.join(lines)+'\n',encoding='utf8',newline='\n')
print(json.dumps({k:manifest[k] for k in ['complete_experiments','current_run','current_wins','best_run','best_wins','current_source_matches_latest_benchmark']},indent=2))
