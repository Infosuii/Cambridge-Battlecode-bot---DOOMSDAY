"""Refresh the portable handoff manifest and preserve actual benchmark output."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
research=ROOT/'research/v67'
records=[json.loads(line) for line in (research/'RESULTS.jsonl').read_text().splitlines() if line.strip()]
best=max(records,key=lambda r:(r['wins'],r['margin']))
latest=records[-1]
hashes={p.relative_to(ROOT/'bots/v67/src').as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((ROOT/'bots/v67/src').rglob('*')) if p.is_file()}
frozen=json.loads((research/'V65_SOURCE_SHA256.json').read_text())
assert all(hashlib.sha256((ROOT/'bots/v65/src'/name).read_bytes()).hexdigest()==sha for name,sha in frozen.items())
assert hashes==latest['source_sha256'], 'current sources differ from the latest benchmark'
chunks=['v67 actual saved benchmark stdout/stderr',
        'b00 baseline output was not saved by the initial runner. Its measured result is in RESULTS.md/jsonl; no replacement output is invented here.', '']
outputs=[]
for folder in sorted((ROOT/'artifacts/evaluations/v67').iterdir()):
    p=folder/'benchmark-output.txt'
    if p.is_file():
        chunks+=['='*80,folder.name,'='*80,p.read_text(encoding='utf8'), '']
        outputs.append(str(p.relative_to(ROOT)).replace('\\','/'))
(research/'BENCHMARK_OUTPUTS.txt').write_text('\n'.join(chunks),encoding='utf8',newline='\n')
manifest=dict(created_utc=datetime.now(timezone.utc).isoformat(),status='unfinished_user_requested_handoff',
              target_wins=220,target_games=240,target_met=False,clear_impossibility_evidence=False,
              complete_experiments=len(records),current_run=latest['run'],current_wins=latest['wins'],
              current_margin=latest['margin'],best_run=best['run'],best_wins=best['wins'],best_margin=best['margin'],
              holdout_seeds_3_4_used=False,guards_against_v61_v58_v66b_run=False,ladder_submitted=False,
              current_source_matches_latest_benchmark=True,current_source_sha256=hashes,
              benchmark_outputs=outputs,live_benchmark_processes=0)
(research/'CHECKPOINT.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8',newline='\n')
(research/'WORKLOG.md').write_text('''# Current checkpoint

The user requested a handoff because usage is low. Continue from HANDOFF.md and GPT_PROMPT.md.
The 220/240 goal is unfinished; there is no evidence it is impossible. Best tested: b06-life15,137/240,+108.0.
Latest/current source: b18-public-camp-state,126/240,+55.7,0faults,fuel941vs359. No benchmark is still running.
Seeds3/4 and checks vs v61/v58/v66b remain unused. No ladder queue/submission. v65/mimic unchanged.

RESULTS.md/jsonl contain all 19 complete240-game experiments. BENCHMARK_OUTPUTS.txt preserves all available
actual stdout/stderr, including the two failed builds; b00's original output was not captured to a file.
CHECKPOINT.json records the exact source hash set matching b18. Every historical source/build remains under
artifacts/evaluations/v67/<run>/build. The 70-map study covers all1177 replays after underscore/hyphen normalization.

First next investigation: new controller's >60000fuel gate around build_fields may prevent field_calls becoming
nonzero, while legacy farm refuses to select its first job with field_calls==0. This is an untested hypothesis,
not an implemented fix. Read the full handoff for protocol limitations and other concrete next steps.
''',encoding='utf8',newline='\n')
print(json.dumps({k:manifest[k] for k in ['complete_experiments','current_run','current_wins','best_run','best_wins','current_source_matches_latest_benchmark']},indent=2))
