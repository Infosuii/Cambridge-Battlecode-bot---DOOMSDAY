import json,sys,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from local_panel import read_native
from policy_rows import stdout
label=sys.argv[1] if len(sys.argv)>1 else 'v118-outnumbered-trace'
rows=json.load(open(f'panels/{label}/results.json'))
stat=collections.defaultdict(lambda:[0,0]); samples=collections.defaultdict(list)
for r in rows:
    n=read_native(r['summary']); us='team'+r['side'].upper()
    deaths=collections.defaultdict(list)
    for e in n['events']:
        if e['kind']!='death':continue
        # owner = the champion that died; entry target = its killer
        if e['owner'].get('team')==us and e['owner'].get('kind')=='champion':
            for v in e['entries']: deaths[e['owner']['name'].split()[0].lower()].append(v['timestamp']['round'])
    last={}
    for l in stdout(r['replay_bundle'],r['side']).splitlines():
        if not l.startswith('OUTN'):continue
        p=l.split(); rnd=int(p[1]); typ=p[3].split('_')[0]; mode=p[4]; n7=int(p[6]); a6=int(p[7])
        if mode=='wait-respawn' or n7<3:continue
        key=(typ,r['map'],r['opponent'],r['side'])
        if key in last and rnd-last[key]<10: continue   # one episode per 10 rounds
        last[key]=rnd
        died=any(rnd<=x<=rnd+15 for x in deaths.get(typ,[]))
        s=stat[(mode,p[5])]; s[0]+=1; s[1]+=died
        if len(samples[mode])<6: samples[mode].append((r['map'],r['opponent'],*p[1:]))
for k,v in sorted(stat.items(),key=lambda kv:-kv[1][0]): print(k,v,round(v[1]/max(1,v[0]),2))
for m in ('approach','fight-champ','join','tribute','to-capture','hold'): print(m,samples[m][:4])
