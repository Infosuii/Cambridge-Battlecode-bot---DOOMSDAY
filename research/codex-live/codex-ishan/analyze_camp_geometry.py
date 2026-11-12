"""EXP233 immutable geometry potentials, independently checked against replay output."""
from hashlib import sha256
from statistics import median
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import ENGINE,HERE,read
from freeze_engine3_discovery import write


def distance(a,b):return max(abs(a[0]-b[0]),abs(a[1]-b[1]))


if __name__=='__main__':
    rawpath=HERE/'CAMP_GEOMETRY_RAW.json';raw=read(rawpath)
    balance=read(HERE/'BALANCE_METADATA_ENGINE3.json');abilities=read(HERE/'ABILITY_METADATA_20261106.json')
    assert balance['engine']==raw['pins']['engine']==ENGINE==abilities['pins']['engine']
    roles={n:{'focus':balance['champions'][str(t)][2],
              'modifier':next(a['modifier'] for a in abilities['abilities'] if int(a['champion'])==t and int(a['slot'])==s)}
           for n,t,s in (('ryth',0,0),('stellar',5,1),('prism',6,1))}
    rows=[];pins=[]
    for r in raw['rows']:
        directory=bench.ROOT/r['directory'];native=directory/'native.json'
        assert bench.digest(native)==r['native_sha256']
        doc=read(native);assert doc['match']['engineBuildHash']==ENGINE and doc['match']['mapHash']==r['map_sha256']
        assert not doc['diagnostics']['codes'] and not any(doc['diagnostics']['botFaults'].values())
        assert not sum(len(e['entries']) for e in doc['events'] if e['kind']=='fuelExhausted')
        archive,=directory.glob('*.repl26a');assert bench.digest(archive)==r['archive_sha256']
        with ZipFile(archive) as z:text=z.read('team-a.stdout').replace(b'\0',b'').decode('utf8')
        assert text==r['stdout']
        # Reparse every raw design/coordinate rather than trusting the derived JSON.
        emitted=[]
        for line in text.splitlines():
            f=line.split()
            if f and f[0]=='CAMP':emitted.append(tuple(map(float,f[1:])))
        expected=[tuple(map(float,(g['handle'],c['handle'],c['type'],c['x'],c['y'],c['hp'],c['strength'],c['range']))) for g in r['groups'] for c in g['camps']]
        assert emitted==expected
        for g in r['groups']:
            camps=g['camps'];points=[(c['x'],c['y']) for c in camps]
            other=[(c['x'],c['y']) for h in r['groups'] if h['handle']!=g['handle'] for c in h['camps']]
            candidates={(x+dx,y+dy) for x,y in points for dx in (-1,0,1) for dy in (-1,0,1)
                        if 0<=x+dx<r['width'] and 0<=y+dy<r['height']}
            safe=lambda p:not any(distance(p,q)<=1 for q in other)
            hit=lambda p:sum(distance(p,q)<=1 for q in points)
            centre=max(map(hit,points),default=0);offset=max(map(hit,candidates),default=0)
            centre_safe=max((hit(p) for p in points if safe(p)),default=0)
            offset_safe=max((hit(p) for p in candidates if safe(p)),default=0)
            # Independent rectangular enumeration checks the union-of-neighbourhoods calculation.
            brute=[(x,y) for x in range(max(0,min(x for x,y in points)-1),min(r['width'],max(x for x,y in points)+2))
                   for y in range(max(0,min(y for x,y in points)-1),min(r['height'],max(y for x,y in points)+2))]
            assert offset==max(map(hit,brute),default=0)
            assert offset_safe==max((hit(p) for p in brute if safe(p)),default=0)
            upper={}
            for role,meta in roles.items():
                damage=meta['focus']*meta['modifier']
                upper[role]=max((sum(min(c['hp'],damage) for c in camps if distance(p,(c['x'],c['y']))<=1) for p in candidates if safe(p)),default=0)
            rows.append({'map':r['map'],'handle':g['handle'],'count':len(points),'gems':g['gems'],'hp':sum(c['hp'] for c in camps),
                         'centre_hits':centre,'offset_hits':offset,'safe_centre_hits':centre_safe,'safe_offset_hits':offset_safe,
                         'safe_first_cast_damage_upper':upper})
        pins.append({'map':r['map'],'stdout_sha256':sha256(text.encode()).hexdigest(),'native_sha256':r['native_sha256'],'archive_sha256':r['archive_sha256']})
    summary={'maps':len(raw['rows']),'groups':len(rows),'total_gems':sum(r['gems'] for r in rows),
             'groups_multi_hit_centre':sum(r['centre_hits']>1 for r in rows),'groups_multi_hit_safe_offset':sum(r['safe_offset_hits']>1 for r in rows),
             'groups_improved_offset':sum(r['offset_hits']>r['centre_hits'] for r in rows),
             'groups_improved_safe_offset':sum(r['safe_offset_hits']>r['safe_centre_hits'] for r in rows),
             'maps_improved_safe_offset':len({r['map'] for r in rows if r['safe_offset_hits']>r['safe_centre_hits']}),
             'gems_in_improved_safe_groups':sum(r['gems'] for r in rows if r['safe_offset_hits']>r['safe_centre_hits']),
             'gems_in_safe_multihit_groups':sum(r['gems'] for r in rows if r['safe_offset_hits']>1),
             'draft_fuel_min_median_max':[min(r['charged_draft_cost'] for r in raw['rows']),median(r['charged_draft_cost'] for r in raw['rows']),max(r['charged_draft_cost'] for r in raw['rows'])],
             'fuel':raw['fuel'],'errors':raw['errors']}
    write(HERE/'CAMP_GEOMETRY_ANALYSIS.json',{'summary':summary,'role_metadata':roles,'raw_sha256':bench.digest(rawpath),'recount_pass':True,
          'limits':'Public initial spawn geometry and damage upper bounds only; no reachable position/vision/safety/clear-speed/win claim. No outcomes or policy fitting.',
          'artifact_recount':pins,'groups':rows})
    print(summary,flush=True)
