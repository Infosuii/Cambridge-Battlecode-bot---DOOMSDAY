"""EXP272: demonstrate the601boundary case and recheck frozen prior111 cohorts."""
from pathlib import Path
import ablate_dev as bench
from engine3_pool import HERE,read
from freeze_engine3_discovery import write
from native_round_deaths import correlate

if __name__=='__main__':
    roots={'LIVE111':'live111-discovery-20261105','LIVE111B':'live111-discovery-20261106','LIVE111C':'live111c-discovery-20261106','LIVE111D':'live111d-discovery-20261106'}
    reports=[]
    for prefix,dirname in roots.items():
        for part in ('discovery','control','confirm'):
            path=HERE/f'{prefix}_REPLAY_{part.upper()}.json';saved=read(path);root=bench.CACHE/dirname
            raw=root/f'analysis-{part}/death_context.json';assert bench.digest(raw)==saved['tool_output_sha256']['death_context']
            contexts={r['id']:r['deaths'] for r in read(raw)}
            corrections=0
            for row in saved['rows']:
                mid=row['matchId'];native=read(root/'summaries'/f'{mid}.json')
                assert bench.digest(root/'replays'/f'{mid}.zip')==saved['archive_sha256'][mid]
                for label,team in (('ours',int(row['side'].upper()=='B')),('rival',int(row['side'].upper()!='B'))):
                    dead,alignment=correlate(contexts[mid],native,team)
                    assert len(dead)==row[label]['deaths600']
                    assert sum(d['pvp_attacks']==0 and d['casts']==0 for d in dead)==row[label]['no_pvp_basic_or_cast_deaths600']
                    corrections+=sum(a['sampled_round']!=a['native_round'] for a in alignment)
            reports.append({'prefix':prefix,'partition':part,'games':len(saved['rows']),'native_round_corrections':corrections,'saved_metrics_unchanged':True,'raw_context_sha256':bench.digest(raw)})
    root=bench.CACHE/'live111e-discovery-20261106';mid='01a1afba-9133-79ad-aba9-4e57efde7fd0'
    raw=root/'analysis-discovery/death_context.json';r,=[r for r in read(raw) if r['id']==mid];native=read(root/'summaries'/f'{mid}.json')
    dead,alignment=correlate(r['deaths'],native,1);assert len(dead)==0 and len(alignment)==1 and alignment[0]['sampled_round']==600 and alignment[0]['native_round']==601
    write(HERE/'NATIVE_ROUND_DEATH_RECOUNT.json',{'pass':True,'baseline_games':sum(r['games'] for r in reports),'reports':reports,
          'demonstration':{'matchId':mid,'native_sha256':bench.digest(root/'summaries'/f'{mid}.json'),'raw_context_sha256':bench.digest(raw),'exact_alignment':alignment},
          'limits':'Exact native cutoff and actor bijection only; sampled activity context is still round-window data, not exact private decision causality.'})
    print({'baseline_games':sum(r['games'] for r in reports),'metrics_unchanged':True,'boundary_demonstration':alignment},flush=True)
