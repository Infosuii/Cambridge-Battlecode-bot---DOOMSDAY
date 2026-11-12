"""Build the Session-1 metadata intake, frozen candidate split and honest checkpoint.

No replay is accepted by this tool. The candidate split is fixed before trajectory
review and remains attached to IDs when replay reconciliation becomes available.
"""
import argparse
import hashlib
import json
import math
import random
import shutil
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from deep_preflight import ROOT, save

sys.path.insert(0,str(ROOT/'tools'))
from patch_text import patch
OUT=ROOT/'research/deep-2026-10-28'
WORK=ROOT/'artifacts/local-only/deep-2026-10-28'


def write_doc(name,text):
    p=OUT/name
    if p.exists():
        old=p.read_bytes().decode('utf-8').replace('\r\n','\n')
        patch(p,[(old,text)])
    else:
        p.write_text(text,encoding='utf-8')


def table(rows):
    return '\n'.join('| '+' | '.join(map(str,row))+' |' for row in rows)+'\n'


def primary_cohort(row,c):
    if row.get('cohort')=='top-v-top':
        return 'Top-v-top'
    if row['opponent_id'] in {t['teamId'] for t in c['learn_cohort']}:
        return 'Learn'
    if row['opponent_id'] in {t['teamId'] for t in c['climb_cohort']}:
        return 'Climb'
    return 'Other'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proof',type=Path,default=OUT/'wave1-proof.jpg')
    args=parser.parse_args()
    c=json.loads((OUT/'COHORTS.json').read_text())
    old=json.loads((WORK/'catalog.json').read_text())
    wave=json.loads((OUT/'WAVE1_METADATA.json').read_text())
    top=json.loads((OUT/'TOP_V_TOP_METADATA.json').read_text())
    native=json.loads((OUT/'NATIVE_AUDIT.json').read_text())
    # All five games in the initial calibration group stay outside tuning/holdout.
    calibration={r['match_id'] for r in old if r['group_id']=='5f7d89e8-c49d-440b-9198-5a1cd778e7a8'}
    candidates=[]
    for r in old+wave['rows']:
        candidates.append({'match_id':r['match_id'],'group_id':r['group_id'],'cohort':primary_cohort(r,c),
                           'map':r['map'],'side':r['own_side'],'result':r['result'],
                           'source':'existing-v69' if r in old else 'wave1-v69',
                           'reconciled':False})
    for r in top['rows']:
        candidates.append({'match_id':r['match_id'],'group_id':r['group_id'],'cohort':'Top-v-top',
                           'map':r['map'],'side':None,'result':None,'source':'top-v-top','reconciled':False})
    if len({r['match_id'] for r in candidates})!=len(candidates):
        raise ValueError('Duplicate intake IDs')
    strata=defaultdict(list)
    for r in sorted(candidates,key=lambda r:r['match_id']):
        if r['match_id'] in calibration:
            r['partition']='calibration-excluded'
        else:
            strata[(r['cohort'],r['map'])].append(r)
    seed=20261028
    rng=random.Random(seed)
    target=math.floor(0.7*sum(map(len,strata.values()))+0.5)
    counts={k:math.floor(0.7*len(v)) for k,v in strata.items()}
    extras=target-sum(counts.values())
    ordered=sorted(strata,key=lambda k:(-(0.7*len(strata[k])-counts[k]),hashlib.sha256((str(seed)+repr(k)).encode()).hexdigest()))
    for k in ordered[:extras]:
        counts[k]+=1
    for k in sorted(strata):
        rng.shuffle(strata[k])
        for i,r in enumerate(strata[k]):
            r['partition']='examined' if i<counts[k] else 'hands-off'
    manifest={'status':'metadata_candidate_assignments_only','seed':seed,
              'selection':'all captured v69 games + entire wave1 + bounded top-v-top selection',
              'strata':['primary cohort','map'],
              'cohort_precedence':'Learn before Climb where membership overlaps; Control is a wins overlay',
              'allocation':'Hamilton allocation nearest70%; SHA256 tiebreak, seeded shuffle in sorted strata',
              'calibration_exclusions':sorted(calibration),
              'eligible_after_reconciliation':0,
              'caveat':'Outcome metadata was seen during catalog/coverage selection. No current replay trajectories were reviewed. Keep these ID assignments; do not resplit after exclusions or tune on hands-off trajectories.',
              'rows':sorted(candidates,key=lambda r:r['match_id'])}
    target_path=OUT/'CANDIDATE_MANIFEST.json'
    if target_path.exists() and json.loads(target_path.read_text())!=manifest:
        raise ValueError('Frozen candidate assignments changed; preserve the existing split')
    save(target_path,manifest)
    partition=Counter(r['partition'] for r in candidates)
    counts_by=defaultdict(Counter)
    for r in candidates:
        counts_by[r['cohort']]['games']+=1
        counts_by[r['cohort']]['wins']+=r['result']=='win'
        counts_by[r['cohort']]['losses']+=r['result']=='loss'
        if r['side']:
            counts_by[r['cohort']]['side_'+r['side']]+=1
    cohort_table=table([['Primary cohort','Games','Wins','Losses','Side A','Side B'],['---','---:','---:','---:','---:','---:']]+
                       [[k,v['games'],v['wins'] if k!='Top-v-top' else 'n/a',v['losses'] if k!='Top-v-top' else 'n/a',v['side_a'] if k!='Top-v-top' else 'n/a',v['side_b'] if k!='Top-v-top' else 'n/a'] for k,v in sorted(counts_by.items())])
    map_counts=defaultdict(Counter)
    for r in candidates:
        map_counts[r['map']][r['cohort']]+=1
    map_table=table([['Map','Learn','Climb','Other','Top-v-top'],['---','---:','---:','---:','---:']]+
                    [[m,v['Learn'],v['Climb'],v['Other'],v['Top-v-top']] for m,v in sorted(map_counts.items())])
    wave_table=table([['Opponent','Wins/games','Mean gem margin','95% Wilson win interval'],['---','---:','---:','---']]+
                    [[name,f"{r['wins']}/{r['games']}",f"{r['margin_sum']/r['games']:+.1f}",f"{100*r['win_rate_wilson_95'][0]:.1f}%–{100*r['win_rate_wilson_95'][1]:.1f}%"] for name,r in wave['by_opponent'].items()])
    stamp=datetime.now(timezone.utc).isoformat()
    write_doc('WAVE1_RESULTS.md',f"""# Wave 1: measured outcomes; replay diagnosis pending

Recorded {stamp}. All {wave['groups']} unranked groups / {wave['games']} games finished.
Maps, ordered sides, opponent identities and unranked status agree with all
{wave['metadata_request_checks_passed']} reservations. Authenticated pages, each anchored
to its own immutable group ID, show our version 69 for all 14 groups.
No uploads, activations or ranked requests were made.

{wave_table}
Each row has n=10 games: five maps, both sides, one game per map/side.
These are descriptive **measured** scores. The intervals assume independent games;
shared maps, paired opponents and selective map coverage limit that assumption.
These are not broad ladder win-rate estimates or causal tests of bot changes.

Opponent pins use the immutable source-group references in SCRIMMAGES.json.
The first subscribe to caterpillow and Zarzorki groups used their then-current bot;
each mirror pins that first group's opponent. Other pairs pin existing groups.
The service hides numeric opponent submission versions in public metadata.

The Mite pair won only on 01islands (2/2 on that map, 0/8 elsewhere; n=10 games).
This is a small **association**, not an explanation of why the other maps lose.
No detector rates or causal code findings are available: replay reconciliation n=0.

Source rows and intervals: WAVE1_METADATA.json. Full IDs, maps, sides and scores:
SCRIMMAGES.json. No further wave 1 requests. Wave 2 retains 10 groups and requires
FAST_FINDINGS.md plus written hypothesis/prediction/decision rules first.
""")
    write_doc('P1_DATA.md',f"""# Session 1 data and exclusions

**Measured metadata intake; accepted decoded/reconciled dataset n=0.**

Existing catalog: n={len(old)} games,239 wins and216 losses,91 version-filtered
groups, created09:20:04.612Z–12:00:05.488Z on28 October2026.
It is the captured UI catalog, not a proven complete activation-bounded census.
Wave1 adds n={wave['games']} games. Top-v-top adds n={top['games']} games in6 groups.
All metadata rows identify engine 2.0.0; no old-engine replay was substituted.

{cohort_table}
Counts include the five calibration games. Learn takes precedence for tabulation
when Learn and Climb overlap; Control means our wins across all cohorts.
Full membership/ranks/ratings and timestamps: COHORTS.json.

## Candidate partition frozen before trajectory review

Seed 20261028; cohort×map strata; nearest70% Hamilton allocation and seeded shuffle.
Examined candidates n={partition['examined']}; hands-off candidates n={partition['hands-off']};
calibration-excluded n={partition['calibration-excluded']}. CANDIDATE_MANIFEST.json
fixes IDs, selection, partitions and method. These are candidate assignments,
not accepted games. Preserve assignments through reconciliation failures.
Outcome metadata was visible during coverage selection; current replay trajectories
were not reviewed. Hands-off trajectories and detector outputs remain unopened.

## Attribution and exclusions

- The authenticated Matches filter group-version=69 and each study-group UI page
  supply actual platform-version evidence. The same time window also contains v67
  games, so a timestamp-only filter would mix sources. Activation time remains unknown.
- The user supplied the live source; all 33 frozen files are exact. No independent
  server-source hash was obtained. Platform identity and source identity remain distinct.
- Native summaries n={native['native_summaries']} pass metadata score/round/outcome and internal
  draft/roster/gem/gold checks. This is not replay reconciliation; independent pairs n=0.
- Initial five-game native-download selection produced two usable unique JSONs,
  one binary instead of requested JSON, one duplicate/mismatched JSON and one absent
  file. The latter three stay quarantined; see DOWNLOAD_EXCLUSIONS.json.
- Both current replay download controls returned paths with no corresponding file.
  No current replay entered analysis. CLI 4.0.0 remains unauthenticated.
- Fourteen older cached ZIPs contain engine 0.0.3/format 0.0.3 replays; exclude all 14.
- Unequal exposure is substantial: error404 accounts for215/455 existing games
  (measured, n=455). Loss-count cohort additions are not opponent-strength rankings.

## Counts by map (metadata only)

{map_table}
No loss-versus-win detector intervals, final win-probability decomposition or
next-bot causal recommendations can be supported until current replays reconcile.
""")
    write_doc('P0_SETUP.md',f"""# Session 1 setup and provenance

Updated {stamp}. Source freeze and metadata/scrimmage setup complete;
replay validation remains blocked. Historical access notes are superseded here.

| Check (measured) | Result | Sample |
|---|---|---:|
| CLI | official cambc 4.0.0 Linux x86_64 |1 binary|
| Binary SHA256 |552056aab1b99a6626597b6aaf0ae38f967709626f90f2d6926c4510ca929eb4|1 binary|
| Engine |2.0.0, all shared-loader pins match; instantiates|3 assets|
| User archive |bot.zip,284031 bytes,33 files|1 archive|
| Match against v58 |29/33 source files byte-identical|33 files|
| Remote frozen copy |33/33 Git blob hashes match ZIP|33 files|
| Native internal checks |scores, rounds, roster, gems, gold pass|2 summaries,19 champions|
| Replay/native reconciliation |pending missing current replay files|0 games|
| Website account |Ishanp signed in; live platform 69 Active/Verified|1 submission|
| CLI session |not authenticated; login initiation refused before credentials|2 prior attempts|

Archive SHA256:0433755c1cbc5f120247c132a6c875912f14c3ac5f36abaa7edbfe20845b325c.
Canonical tree SHA256:5b07f2bfb84f8168a2d24e8fa67a2d431cc836999137576a238f666d2fb08eb2.
Definition and per-file hashes: LIVE_SOURCE.json. Frozen copy: bots/live-69/src.
Remote source-copy staging tree:b31cff2ee61823585117100158bd08ba286318bc.
The user supplied this archive as live 69. The blocked server archive was not
independently hashed. Submission:f91de3f0-0453-409e-b712-b86067eecbca,
note“v75 ladder duel candidate”, uploaded by Om. Absolute activation time unknown.

The correct attachment supersedes the five earlier 16/17-file input archives.
Their original hashes and comparisons remain in INPUT_PROVENANCE.json.

## Decoder migration and its limit

decode_replays.mjs now imports engine/defaultAssets/verifyAssets/PINNED/VERSION
from engine.mjs, eliminating its duplicate 1.0.3-only loader. Its summary comparison
checks the selected version. Engine 2 remains explicit: NFS_REPLAY_ENGINE=2.0.0.
Default asset search supports Linux and Windows; NFS_REPLAY_ASSETS overrides it.
Syntax, official asset pins and engine instantiation pass. Current replay decoding
and five-game native reconciliation have not been validated. Do not bulk-process
until those checks pass. The older cached 0.0.3 replays fail the engine 2 load and
are excluded rather than coerced through another engine.

Native rosters are dynamic: a draft may have fewer than ten picks/champions;
Cassi & Issac share one draftPick while having separate champion IDs. The native
auditor checks each recorded roster entry against its actual pick and does not
assume a ten-champion roster (measured, n=2 summaries with 10 and 9 champions).

## Repository and boundaries

Parent working branch:claude/compare-fix-replay-decoder, pinned commit
294500b8c4da4af19a81f2cdb262305ea54d27f9. Main lacks the newer v59–v67 reports.
The checkout is partial; connector tree commits preserve every untouched parent
entry. Publish only analysis/deep-2026-10-28, without force. Frozen bot bytes remain
unchanged. No account settings, submissions, activations or ranked requests.
""")
    write_doc('P2_DETECTORS.md',"""# Session 1 detector status

**Blocked before validated replay ingestion. No detectors have been accepted.**
Decoded/reconciled games n=0; loss-versus-win detector-rate denominators n=0/n=0.
There are no valid rates, intervals, example rounds or causal bug candidates yet.
Native-summary internal checks are not independent replay reconciliation.

The next implementation must build on the pinned engine 2 loader and existing
still_runs/death_context/respawn_delay/fuel_outs/home_trips/capture_funnel/
capture_pressure/tp_effects tools. Validate each event and perspective definition
against the official engine before estimating rates; keep hands-off outputs unopened.

| ID | Required signal | Key validation |
|---|---|---|
|D1|alive, no move/attack, not channelling|exclude death, recall, bank and channel turns|
|D2|long high bag without bank attempt; gems lost at death|native gem identity, attempt vs completion|
|D3|repeated spatial/configuration deaths|rounds/positions/foe composition, dynamic roster|
|D4|repeated target/mode alternation|replay movement proxy must not claim hidden mode|
|D5|capture attempts, resets and enemy rewards after clearing|separate clearing, progress and reward owner|
|D6|dead/empty camp waiting and blocked spawn tiles|official respawn/spawn occupancy semantics|
|D7|fuel exhaustion and faults|native fault/events reconciliation by champion|
|D8|blocked altar/gate, failed tribute and locks|legal path/action semantics; map topology|
|D9|hole-island stranding; local1-vs-2 isolation|traversability and actual visible enemy state|
|D10|high unspent gold, late purchases/equipment|count buying while dead; actual item costs|
|D11|deaths after unseen threats; wards by 250|own-perspective visibility over previous 5 rounds|

Thresholds must be registered before examining trajectories, with duration/rate
denominators in champion-rounds and per-game occurrence rates. Report Wilson
intervals for game occurrence plus map/opponent clustering sensitivity; frequency
differences are associations until a valid intervention tests a causal rule.

Do not repeat the historical blanket claim that winners hold spells: the newer
own-perspective cooldown audit did not support it. Historical reports guide
definitions; they are not current-v69 measurements.
""")
    write_doc('STATE.md',f"""# Deep analysis: Session 1 checkpoint

Updated {stamp}. **Session 1 is partially complete; replay access is the blocker.**

## Phase and next action

Setup/source freeze, cohorts, metadata catalog and wave1 complete. Resume at §2.1
five-game replay/native reconciliation, then §3 accepted ingestion and §4 detectors.
Obtain current replay bundles with native summaries through a working official
download or user-supplied files. Browser replay controls returned nonexistent
paths; CLI is unauthenticated and login starts refused before credential entry.
Do not extract browser cookies/tokens or bypass the blocked source download.
Do not queue more wave1 groups or repeat confirmed requests.

## Preserved state

- Branch:analysis/deep-2026-10-28; parent working branch:claude/compare-fix-replay-decoder.
- Parent commit:294500b8c4da4af19a81f2cdb262305ea54d27f9. Partial checkout;
  remote tree commits must preserve all untouched entries. No force push.
- Live platform 69/submission f91de3f0-0453-409e-b712-b86067eecbca Active/Verified;
  note“v75 ladder duel candidate”. Exact activation time unknown.
- Correct user bot.zip: 33 files; 29 match v58. Frozen unchanged in bots/live-69/src.
  ZIP0433755c1cbc5f120247c132a6c875912f14c3ac5f36abaa7edbfe20845b325c.
  All 33 remote Git blobs equal the ZIP. Server source hash independently unverified.
- Existing v69 metadata:{len(old)} games (239W/216L),91 captured groups.
  Actual authenticated version filter avoids v67 games in the same time window.
- Wave 1:{wave['groups']} groups/{wave['games']} games, all finished; {wave['wins']}W/{wave['losses']}L.
  Every group's actual own version 69, maps, sides and opponent checked. SCRIMMAGES.json
  holds all IDs/results/pins. Wave 1 budget 0 remaining; wave 2 budget 10 remaining.
- Learn:current top5. Climb:eight spaced ranks 15–40 plus top3 observed loss counts.
  Source snapshot and overlap/unequal-exposure caveats are in COHORTS.json.
- Top-v-top metadata:n={top['games']}; accepted decoded/reconciled games:n=0.
- Native integrity:2 summaries/19 champions pass; independent replay pairs:n=0.
- CLI 4.0.0 and engine 2.0.0 pinned. Decoder imports shared loader; syntax/pins/
  instantiation pass. Do not treat that as five-game decoder validation.
- Candidate partition seed 20261028:{partition['examined']} examined/{partition['hands-off']} hands-off;
  {partition['calibration-excluded']} calibration-excluded. Preserve IDs through reconciliation. No trajectories reviewed.

## Files and resumption rules

Read P0_SETUP.md, P1_DATA.md, P2_DETECTORS.md, WAVE1_RESULTS.md and the JSON ledgers.
Raw evidence stays artifacts/local-only/deep-2026-10-28 (never commit raw replays).
DOWNLOAD_EXCLUSIONS.json records failed/ambiguous downloads and old-engine caches.
P2 is a blocker/status registry, not completed detector implementation or rates.
No FAST_FINDINGS.md exists; wave2 requires it plus written hypotheses first.
Never submit, activate, request ranked games, edit frozen bots or expose credentials.
""")
    if args.proof.resolve()!=(OUT/'wave1-proof.jpg').resolve():
        shutil.copyfile(args.proof,OUT/'wave1-proof.jpg')
    print(json.dumps({'candidate_games':len(candidates),'partitions':dict(partition),
                      'cohorts':{k:dict(v) for k,v in counts_by.items()},'reconciled':0}))


if __name__=='__main__':
    main()
