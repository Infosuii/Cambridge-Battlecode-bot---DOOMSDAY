"""Catalog at least thirty current-engine games among the frozen Learn top five.

Public metadata only. Bounded to three list pages per team and six match groups;
no private replay requests, no auth values, no match creation.
"""
import json
import urllib.parse
from deep_preflight import ROOT, save
from scout_public import Public


def main():
    work=ROOT/'artifacts/local-only/deep-2026-10-28/top-v-top'
    api=Public(work)
    c=json.loads((ROOT/'research/deep-2026-10-28/COHORTS.json').read_text())
    top={t['teamId'] for t in c['learn_cohort']}
    groups={}
    for team in c['learn_cohort']:
        cursor=None
        for page in range(3):
            query={'scope':'all','team':team['teamId']}
            if cursor:
                query['before']=cursor
            d=api.json('/api/v1/match-groups?'+urllib.parse.urlencode(query),f"lists/{team['teamId']}-{page}.json")
            for g in d['groups']:
                if g['status']=='finished' and len(g['sides'])==2 and all(s['teamId'] in top for s in g['sides']):
                    groups[g['id']]=g
            if len(groups)>=6 or not d.get('more') or not d.get('next'):
                break
            cursor=d['next']
        if len(groups)>=6:
            break
    rows=[]
    for g in sorted(groups.values(),key=lambda g:g['createdAt'],reverse=True)[:6]:
        d=api.json('/api/v1/match-groups/'+g['id'],f"groups/{g['id']}.json")
        for m in d['matches']:
            if m['status']=='finished' and str(m['patchId']).startswith('2.0.0:'):
                rows.append({'match_id':m['id'],'group_id':g['id'],'map':m['map'],'map_id':m['mapId'],
                             'created_at':m['createdAt'],'patch_id':m['patchId'],
                             'teams':[{k:s.get(k) for k in ['side','teamId','teamName','score','result']} for s in m['sides']],
                             'reconciled':False})
    save(work/'catalog.json',rows)
    save(ROOT/'research/deep-2026-10-28/TOP_V_TOP_METADATA.json',
         {'evidence_label':'measured','games':len(rows),'groups':len({r['group_id'] for r in rows}),
          'reconciled_games':0,'selection':'newest completed games between the frozen current top five in bounded public listings',
          'metadata_only':True,'rows':rows})
    print(json.dumps({'top_v_top_metadata':len(rows),'reconciled':0}))


if __name__=='__main__':
    main()
