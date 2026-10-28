import json
from pathlib import Path

root=Path(__file__).resolve().parents[2]
maps=['00collision','00vault','00crater','01hooks','02arena','00packs']
plan={'note':'Action-sequence mechanism diagnostic, not strength evidence or holdout',
      'groups':[{'opponent':'pool','maps':[m for m in maps for _ in range(2)],'sides':['a','b']*len(maps)}]}
(root/'research/v81/diagnostic_plan.json').write_text(json.dumps(plan,indent=1)+'\n')
