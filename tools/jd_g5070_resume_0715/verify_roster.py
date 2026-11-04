"""Verify every logged body-slot roster against the real engine's draft roster."""
import argparse,json,zipfile
from pathlib import Path
EVAL=Path(r'C:\projects\cambridge battlecode\battlecode part 2\jd-eval')
TYPES=['Ryth','Vesper Vale','Vendetta','Cassi','Issac','Stellar','Prism','Marcella','Willow','Ren','Varg','Tavi','Heart of Ruin']

def main():
 p=argparse.ArgumentParser();p.add_argument('runs',nargs='+');a=p.parse_args();checked=0;sizes=set();slots=set()
 for run in a.runs:
  out=EVAL/'runs'/run;meta=json.loads((out/'run.json').read_text())
  for cell in meta['cells_list']:
   stem='cand__'+cell['opp']+'__'+cell['map']+'__'+cell['side']
   stats=json.loads((out/'games'/(stem+'.json')).read_text());team='team'+cell['side']
   expected=[TYPES.index(c['name']) for c in sorted(stats['roster']['champions'],key=lambda c:c['id']) if c['team']==team]
   with zipfile.ZipFile(out/'games'/(stem+'.repl26a')) as z:
    lines=z.read('team-'+cell['side'].lower()+'.stdout').replace(b'\0',b'\n').decode().splitlines()
   found=[]
   for line in lines:
    if not line.startswith('JDROSTER '):continue
    values=list(map(int,line.split()[1:]));slot,n=values[:2]
    assert n==len(expected) and values[2:]==expected,(stem,line,expected)
    found.append(slot);slots.add(slot);sizes.add(n);checked+=1
   assert sorted(found)==list(range(len(expected))),(stem,found)
 result=dict(passed=True,games=sum(len(json.loads((EVAL/'runs'/r/'run.json').read_text())['cells_list']) for r in a.runs),bodies_checked=checked,physical_team_sizes=sorted(sizes),slots_checked=sorted(slots))
 Path('research/jd-g5070-resume-0715/ROSTER_FIXTURES.json').write_text(json.dumps(result,indent=2));print(result)
if __name__=='__main__':main()
