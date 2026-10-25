"""Add opponent-specific reporting and deployment state after the frozen tests."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'phase2-two-hours'
def read(name): return json.loads((ROOT/name).read_text())

report = read('report.json')
protocol = read('protocol.json')
held = {Path(p).stem for p in protocol['final_holdout_maps']}
opponents = {}
for label in ['v47', 'original', 'first-hour']:
    result = read('evaluation/all-maps-vs-' + label + '.json')
    rows = [r for r in result['rows'] if r['map'] in held]
    opponents[label] = dict(all_maps=result['summary'], reserved_maps=dict(
        games=len(rows), wins=sum(r['win'] for r in rows),
        faults=sum(r['faults'] for r in rows), fuel=sum(r['fuel'] for r in rows)))
deployment = read('deployment.json')
report.update(opponent_specific_results=opponents, deployment=deployment,
              selection_promotion_is_not_platform_activation=True)
(ROOT/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
text = (ROOT/'FINAL_REPORT.md').read_text(encoding='utf-8')
text += '\n## Full opponent comparisons\n\n'
text += '| Opponent | All 40 maps, both sides | Eight reserved maps, both sides | Candidate faults | Fuel-exhaustion entries (all maps) |\n'
text += '|---|---:|---:|---:|---:|\n'
for label, scores in opponents.items():
    all_, held_ = scores['all_maps'], scores['reserved_maps']
    text += f"| {label} | {all_['wins']:g}/{all_['games']} wins | {held_['wins']:g}/{held_['games']} wins | {all_['faults']} | {all_['fuel']} |\n"
text += '''
The new policy does not show a reliable general improvement. It narrowly beat v47 and the first-hour bot over all maps, but lost to the original. On the reused eight-map pooled benchmark it scored 47/80, matching the original 47/80 and below the first-hour bot's 52/80. The exploratory map-cluster 95% interval for its pooled win-rate difference from original is -15 to +15 percentage points. Fuel exhaustion is distinct from a crash; zero bot faults does not mean zero fuel exhaustion.

## Upload and activation

The exact verified source was uploaded successfully as **version 50** through the official CLI. CLI packaging was compared byte-for-byte by source member with the verified source archive before upload. See deployment.json and submission.log.

**Live activation is unverified and remains blocked.** The CLI provides no activation command, the existing CLI bearer login receives HTTP 401 from the submission-list API, and the official site interface asset receives HTTP 403. Server compilation status and active-version state could not be read. No desktop/browser control was taken, consistent with the user's restriction. Open https://2026a.battlecode.co.uk/game/submissions to check server compilation and activate version 50. This upload alone is not evidence that version 50 is live.
'''
(ROOT/'FINAL_REPORT.md').write_text(text,encoding='utf-8')
print(json.dumps(opponents,indent=2))
