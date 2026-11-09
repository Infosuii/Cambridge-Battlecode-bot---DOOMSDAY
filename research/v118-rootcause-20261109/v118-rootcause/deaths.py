import json,sys,collections,concurrent.futures
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from local_panel import read_native
def one(r):
    n=read_native(r['summary']);us='team'+r['side'].upper()
    d=collections.Counter()
    for e in n['events']:
        if e['kind']!='death':continue
        for v in e['entries']:
            t=v['target']
            if t.get('kind')=='champion':d['us' if t.get('team')==us else 'them']+=1
    held=next((int(float(t.get('gems',0) or 0)) for t in n['teams'] if t['team']==us),0)
    return r['candidate'],r['map'],r['opponent'],r['side'],d['us'],d['them'],r['score'],r['rounds']
def deaths(labels):
    rows=[r for l in labels for r in json.load(open(f'panels/{l}/results.json'))]
    with concurrent.futures.ThreadPoolExecutor(16) as p: return list(p.map(one,rows))
if __name__=='__main__':
    out=deaths(sys.argv[1].split(','))
    agg=collections.defaultdict(lambda:[0,0,0,0])
    for c,m,o,s,du,dt,sc,rd in out:
        a=agg[c];a[0]+=1;a[1]+=du;a[2]+=dt;a[3]+=sc
    for c,a in sorted(agg.items()):print(c,'games',a[0],'our deaths/g %.2f'%(a[1]/a[0]),'their deaths/g %.2f'%(a[2]/a[0]),'score',a[3])
    json.dump(out,open('v118-rootcause/deaths-'+sys.argv[1].replace(',','+')+'.json','w'))
