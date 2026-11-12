"""EXP274 prerequisite: initial non-Varg soak-order suspicion, not policy tuning."""
import ablate_dev as bench
from engine3_pool import HERE, read
from freeze_engine3_discovery import write


def coefficient(camps):
    remaining=sum(c['strength'] for c in camps)
    total=0
    for c in camps:
        total+=remaining*c['hp']
        remaining-=c['strength']
    return total


if __name__=='__main__':
    path=HERE/'CAMP_GEOMETRY_RAW.json';raw=read(path)
    analysis=read(HERE/'CAMP_GEOMETRY_ANALYSIS.json')
    assert analysis['recount_pass'] and analysis['raw_sha256']==bench.digest(path)
    source=bench.ROOT/'bots/codex-live111-frozen/src/bot.cpp'
    text=source.read_text(encoding='utf8')
    assert 'std::sort(live.begin(), live.begin() + n);' in text
    assert 'float key = c.hp - c.strength * 1000.0f;' in text
    rows=[]
    for r in raw['rows']:
        for g in r['groups']:
            live=[c for c in g['camps'] if c['strength']>0]
            if not live:continue
            hp=sorted(live,key=lambda c:(c['hp'],c['strength']))
            executor=sorted(live,key=lambda c:c['hp']-1000*c['strength'])
            a,b=coefficient(hp),coefficient(executor)
            rows.append({'map':r['map'],'group':g['handle'],'dangerous_camps':len(live),
                         'hp_order':[c['handle'] for c in hp],'executor_order':[c['handle'] for c in executor],
                         'hp_coefficient':a,'executor_coefficient':b,'equal':abs(a-b)<1e-6})
    report={'scope':'Initial public HP/strength only, non-Varg, ideal sequential damage. No current damaged/cooldown/position claim.',
            'raw_sha256':bench.digest(path),'analysis_sha256':bench.digest(HERE/'CAMP_GEOMETRY_ANALYSIS.json'),
            'source_sha256':bench.digest(source),'maps':len(raw['rows']),'groups':sum(len(r['groups']) for r in raw['rows']),
            'dangerous_groups':len(rows),'coefficient_differences':sum(not r['equal'] for r in rows),'rows':rows}
    write(HERE/'INITIAL_CAMP_ORDER_AUDIT.json',report)
    print({k:v for k,v in report.items() if k!='rows'},flush=True)
