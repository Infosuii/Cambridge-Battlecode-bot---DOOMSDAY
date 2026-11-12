"""Reconcile a definite validation rejection, without retrying uncertain uploads."""
from pathlib import Path
import sys
import json
BASE=Path(r'C:\projects\cambridge battlecode\work\agentic-improvement')
sys.path.insert(0,str(BASE/'autonomy'))
from store import connect, finish
with connect() as db:
    rows=[dict(r) for r in db.execute("SELECT id,status,data FROM actions WHERE kind='group' AND status='uncertain'")]
for row in rows:
    d=json.loads(row['data'])
    if d.get('tag')=='delivery-20261108:baseline':
        error=d.get('result',{}).get('error','')
        assert 'Unknown or inactive map: 00the-line' in error and 'HTTP 400' in error
        finish(row['id'],'failed',{'reason':'Definite received HTTP400 validation rejection; corrected request uses live map IDs and a different tag.','previous_error':error})
        print('Reconciled rejected request',row['id'])
path=BASE/'autonomy/data/experiments/bounded-delivery-retune-20261107-platform-spotcheck/plan.json'
dest=path.with_name('invalid-filename-plan.json')
assert path.exists() and not dest.exists()
path.rename(dest)
print('Preserved rejected filename-based plan')
