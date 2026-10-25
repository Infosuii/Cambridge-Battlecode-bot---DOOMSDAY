"""Write compact, reproducible v52 loss and winner comparisons from offline audits."""
from collections import defaultdict
import json
from pathlib import Path
import statistics

ROOT=Path(__file__).resolve().parents[2]
DRAFT=['Ryth','Vesper','Vendetta','Cassi+Issac','Stellar','Prism','Marcella','Willow','Ren','Varg','Tavi','Heart']
CAMP=['wolf','elk','golem','gem','gold','monolith']

def main():
    p=ROOT/'data/ladder';local=ROOT/'artifacts/local-only/v53-review'
    matches=json.loads((p/'v52_since_live_20261025.json').read_text())
    top=json.loads((p/'v53_top_wins_20261025.json').read_text(encoding='utf-8-sig'))
    meta={m['matchId']:m for m in matches+top}
    audits=json.loads((local/'audit-refresh.json').read_text())
    def names(d):return ', '.join(DRAFT[x] for x in d)
    def inventory(t,r=500):
        snap=next((s for s in t['snapshots'] if s['round']==r),None)
        if not snap:return '-'
        return str(30*sum(n*(5 if i%2 else 1) for c in snap['champions'] for i,n in c['items']))
    def bank(t):
        b=t['banks']
        return f"R{b[0]['round']}, median {statistics.median(x['amount'] for x in b):g}, {len(b)} channels" if b else 'none'
    def targets(t):return '; '.join(f"R{x['round']} {CAMP[x['type']] if x['type']<len(CAMP) else x['type']}({x['x']},{x['y']})" for x in t['first_targets'][:8])
    losses=[]
    for a in audits:
        m=meta[a['id']];mine=next((t for t in m['teams'] if t['name']=='DOOMSDAY'),None)
        if not mine:continue
        i='ab'.index(mine['side']);j=1-i;opp=next(t for t in m['teams'] if t['name']!='DOOMSDAY')
        losses.append((a['submitted_gems'][i]-a['submitted_gems'][j],m,a,i,j,mine,opp))
    def record(kind):
        rows=[m for m in matches if m['kind']==kind]
        return f"{sum(any(t['name']=='DOOMSDAY' and t['result']=='win' for t in m['teams']) for m in rows)}/{len(rows)}"
    expected=sum(any(t['name']=='DOOMSDAY' and t['result']=='loss' for t in m['teams']) for m in matches)
    assert len(losses)==expected,(len(losses),expected)
    lines=['# V52 loss audit — 2026-10-25', '',
           f"Refreshed snapshot: ranked {record('ranked')}; unranked {record('unranked')} since 12:02 UTC. Named queued groups are 1/5 against Hidden Altar Keepers and 0/5 against meow. The initial snapshot was ranked 2/5 and unranked 4/15 and is preserved separately. API timestamps place the groups at 12:05 UTC, earlier than the approximate 12:15 handoff note. Version association uses start time; API list responses do not expose a submission hash.", '',
           f"All {len(losses)} losses and seven top-team wins decoded with the pinned engine, {len(audits)}/{len(audits)} successful. This report is omniscient offline analysis. Deaths are alive→dead transitions sampled once per round; attack counts include basic attacks classified by target tile, exclude spells, and are proxies for fight allocation. Equipment value is original shard purchase gold (five shards per emblem), not raw inventory-entry counts. Full audits and replays are local-only.", '',
           '## Losses ranked by score deficit', '',
           '| Map | Kind | Opponent | Score us/them | Deaths us/them | First bank / median amount: us | Winner | Gear purchase value R500 us/them |',
           '|---|---|---|---|---|---|---|---|']
    for margin,m,a,i,j,mine,opp in sorted(losses,key=lambda r:r[0]):
        u,v=a['teams'][i],a['teams'][j]
        lines.append(f"| {m['map']} | {m['kind']} | {opp['name']} | {a['submitted_gems'][i]}/{a['submitted_gems'][j]} | {u['deaths']}/{v['deaths']} | {bank(u)} | {bank(v)} | {inventory(u)}/{inventory(v)} |")
    for label,key in [('Map',lambda r:r[1]['map']),('Opponent',lambda r:r[6]['name']),('Our draft set',lambda r:names(sorted(r[5]['draftPicks'])))]:
        grouped=defaultdict(list)
        for row in losses:grouped[key(row)].append(row)
        lines+=['',f'## {label} ranking (losses only, not win rates)','', '| Pattern | Losses | Mean deficit |','|---|---|---|']
        for k,rs in sorted(grouped.items(),key=lambda kv:sum(-r[0] for r in kv[1]),reverse=True):
            lines.append(f'| {k} | {len(rs)} | {-statistics.mean(r[0] for r in rs):.1f} |')
    lines+=['','## Per-loss farming, banking, fighting and draft comparisons','']
    for margin,m,a,i,j,mine,opp in sorted(losses,key=lambda r:(r[1]['map'],r[0])):
        u,v=a['teams'][i],a['teams'][j]
        lines += [f"### {m['map']} vs {opp['name']} ({a['id']})",'',
                  f"Our draft: {names(mine['draftPicks'])}. Winner: {names(opp['draftPicks'])}.",
                  f"Our first distinct camp attack targets: {targets(u)}.",
                  f"Winner's first targets: {targets(v)}.",
                  f"Banks us: {bank(u)}; winner: {bank(v)}. Basic camp/champion attacks us {u['camp_attacks']}/{u['champion_attacks']}, winner {v['camp_attacks']}/{v['champion_attacks']}. Deaths {u['deaths']}/{v['deaths']}; gear purchase value at R100 {inventory(u,100)}/{inventory(v,100)}, R500 {inventory(u)}/{inventory(v)}. Final carried gems {sum(c['gems'] for c in a['champions'] if c['team']==i)}/{sum(c['gems'] for c in a['champions'] if c['team']==j)}.",'']
    lines+=['## Top-team reference wins','']
    for a in audits:
        m=meta[a['id']]
        if a['id'] not in {r['matchId'] for r in top}:continue
        j=a['outcome']-1;winner=next(t for t in m['teams'] if t['side']=='ab'[j]);t=a['teams'][j]
        lines += [f"- {m['map']}: {winner['name']} ({a['id']}), {a['submitted_gems']}, {a['rounds']} rounds. Draft {names(winner['draftPicks'])}. Bank {bank(t)}; deaths {t['deaths']}; gear value R100/R500 {inventory(t,100)}/{inventory(t)}. First targets: {targets(t)}."]
    lines+=['','## Local reproduction and conclusions','',
            '- `tools/v53_diagnose.py` reproduced boss-battle, concentrated-wealth, elkring, swirl and yellow-brick-road at default fuel using the documented logging/profile copies. Full logs are under artifacts/local-only/v53-review/{log,profile}. Local holdout maps were not used for tuning.',
            '- Boss-battle: the logging build has carriers with 136–482 gems at R1200 and repeated cmicro positions around the gated altar. The winning reference starts attacking a monolith at R518 and first banks 581 at R684; a Marcella has 4,900 maximum health at R500. Merely copying its draft fails in our controller. Objective readiness and income allocation, rather than an early whole-team rush, remain unresolved.',
            '- Concentrated-wealth: large death and farming deficits dominate both target scrimmages. In the Hidden Altar Keepers game we spend 685 basic attacks on champions versus 252 by the winner, yet die 9 times versus zero. Our own capture/wait behavior and lower equipment value are worth measuring; a short wait is not by itself evidence of a freeze.',
            '- Elkring: deaths 10–12 versus 1–2; examine solo commits and nearby camp aggro before changing banking thresholds. A new learned draft loses all six local tests, so the observational draft association is insufficient.',
            '- Swirl: the logging reproduction has frequent approach/capture travel and linked Cassi/Issac still at only 925/1300 maximum health at R1200. The new draft model also loses all six. No validated cheap fix yet.',
            '- Yellow-brick-road: profile shows world work above 60k fuel on heavy turns, with suspended decisions. The reference winner has much more spent equipment by R500 and starts banking at R33. Redundant mask initialization is directly confirmed in the SDK and is the next isolated fuel candidate.',
            '- Big-world/islands fixes remove specific reachability failures, but do not make farming competitive with top teams: in the two big-world losses the winner makes 1,409–1,455 basic camp attacks versus our 1,057–1,139. Their R500 equipment lead supports a tempo hypothesis.',
            '- Monolith/fracture are inspected through ladder replays only. Monolith loss has 19 deaths versus eight and fewer bank channels. Fracture loss has more champion attacks despite fewer banks; local holdout tests remain reserved for release.',
            '', '## Rules and API cross-check','',
            'User-supplied game rules and C++ API reference were consulted. Group damage wakes all members; capture speed is unchanged by extra allies; spawn occupancy delays respawns; tribute is not cancelled by ordinary damage; unused fuel does not carry over. The installed SDK bitboard default constructor calls clear(), so immediate explicit clear() calls are redundant host calls. These findings are implementation evidence, not instructions from the reference documents.']
    (ROOT/'artifacts/claude_ops/V53_LOSS_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print('wrote V53_LOSS_REPORT.md',len(losses),'losses')

if __name__=='__main__':main()
