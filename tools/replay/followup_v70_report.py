"""Write the separate current-version research addendum without changing the frozen study."""
import ast
import hashlib
import json
import subprocess
from datetime import datetime,timezone
from pathlib import Path
from deep_preflight import ROOT
from deep_detector_report import save
S=ROOT/'research/followup-v70-2026-10-29';L=ROOT/'artifacts/local-only/followup-v70-2026-10-29'
def read(n):return json.loads((S/n).read_text(encoding='utf-8'))
def write(p,s):p.write_bytes((s.rstrip()+'\n').encode())
def append(p,marker,s):
    b=p.read_bytes();eol=b'\r\n' if b.count(b'\r\n')>b.count(b'\n')/2 else b'\n'
    if marker.encode() not in b:p.write_bytes(b+eol+s.rstrip().replace('\n',eol.decode()).encode()+eol)
def ci(v):return 'insufficient maps' if v is None else f'[{v[0]:.1f}, {v[1]:.1f}]'


def main():
    d=read('ANALYSIS_DATA.json');source=read('SOURCE_COMPARISON.json');fidelity=read('SOURCE_FIDELITY.json');traces=read('CURRENT_BANK_TRACES.json');summaries=d['summaries'];u=summaries['Unique trajectories'];b=summaries['Unique BattleCats'];loss=u['loss'];rank=summaries['Ranked'];now=datetime.now(timezone.utc).isoformat()
    assert d['games']==85 and d['unique_replay_trajectories']==59 and fidelity['current_source_exact']==2 and fidelity['both_script_exact']==2
    assert all(r['trace_replay_byte_exact'] for r in traces['rows']) and [len(r['bank_disable_conflict_contexts']) for r in traces['rows']]==[5,10]
    source_table=['| Current source feature | Effective source setting / difference |','|---|---|','| HOME_SIDE | On; enemy-territory weight 0.3, aggression multiplier 0.8 |','| V71 map knob profiles | Removed; prior per-map effective thresholds cannot be copied across versions |','| V70 per-map draft table | Removed; custom five-pick lineup uses Vendetta, Varg, Cassi & Issac, Marcella, Heart of Ruin |','| V75 lone-fight guard | Removed (was active in the v69 study) |','| A3 items / focus / numbers / single capture owner | All off, despite added code and later guarded default definitions |','| A3 back-off override | On; HP floor 40%, TTK/TTD factor 1.25, wounded target at equal numbers below 40% |','| A2_TEAM | 2, changed from 0 |','| Island escape and incremental siege scan | V69 island escape and V68 incremental siege paths removed |','| Recall cancellation / bank-disable timer | Same inconsistency remains, now at bot.cpp around 6844 / 4530 / 4634 |']
    lines=["# Current v70: fresh evidence and revised priorities",'',f'Updated {now}. This is a separate **exploratory** follow-up to the completed v69 study. No old reserved-game trajectories, model refits, new shared-quota matches or production changes were used.','',
      '## What the extra information changes','',
      '1. **The active source changed.** The website showed v70, “home side,” Active/Verified. Its official archive has 33 files, of which four differ from frozen v69. It is a substantially different policy, not merely the old bot with a small recall fix.',
      '2. **Count distinct trajectories.** The 85 downloaded matches contain 59 distinct raw replay hashes: 26 repeated BattleCats trajectories. All 70 BattleCats games are side A. Their raw record is 32/70 wins; one-per-trajectory is 18/44. These are descriptive records from different weighting schemes, not estimates of mirrored-side performance.',
      '3. **The recall/banking defect is present in the current bot on two ordinary, non-gated maps.** Exact logging reproductions show five affected turns on split and ten on collision. This extends the mechanism beyond the earlier guardians case, but does not establish that a particular patch wins those races.',
      f"4. **The loss-side equipment gap widens after round 100.** In {loss['n']} distinct losses, mean cost gap is {loss['equipment_gap_100']['map']['mean']:.1f} at R100, map95 {ci(loss['equipment_gap_100']['map']['interval95'])}; at R250 it is {loss['equipment_gap_250']['map']['mean']:.1f}, map95 {ci(loss['equipment_gap_250']['map']['interval95'])}. Focus on the R100–250 transition instead of assuming every loss was settled by the first purchase.",
      '5. **Allocation differs by champion.** In 25 same-game Marcella pairs from distinct losses, our Marcella is behind by 68.0 earned gold and 61.2 inventory cost at R100. Vendetta is ahead by 35.2 earned gold and 22.2 cost in 27 loss-side pairs. A team-wide “buy earlier” rule would miss that imbalance.',
      '6. **Guardians is a separate conversion failure worth reproducing.** One current loss banked 0 of 1,389 collected gems and lost 1,265, despite a +90 equipment lead at R100. That is not a simple bad-opening case.','',
      '## Source and dataset provenance','',
      'The official [Submissions page](https://2026a.battlecode.co.uk/game/submissions) showed platform70, submission78116168-a5b6-42f3-bb19-1f7d1b17c45d, note “home side.” Downloaded archive v74_home_side.zip SHA256: `'+source['archive_sha256']+'`. The archive filename is not the platform version. Raw source is retained unchanged under the ignored follow-up folder, not added to a frozen bot directory.',
      '', 'The [version-filtered match history](https://2026a.battlecode.co.uk/game/matches?group-version=70) supplied all 17 selected completed groups: 15 ranked games and 70 existing unranked games against BattleCats. No game was queued by this continuation. All 17 ZIPs, 85 nested replay bundles and 85 server-native summaries were downloaded through official website controls. The JSON summary control failed once; the official binary export worked and CLI4.0.0 converted CAMSTAT files offline. PLAN.json fixes the intake IDs; MANIFEST.json and DOWNLOADS.json preserve provenance and hashes.',
      '', f"All 85 resource extracts pass native final cursor/outcome/score and physical gem identities, with {d['validation']['resource_clock_checks']:,} gold/gem/earned-gold clock checks. Zero unclassified sampled earned gold. Five excluded calibration games match the earlier validated timeline at every requested mark. Four new accepted-input scripts reapply byte-for-byte through official APIs with 4,318 round states matched. Unmodified current source versus enemy puppet and both-script controls reproduce one ranked loss and one win exactly; both new sparse logging builds also reproduce their complete original games. These are whole-game behavioural checks, not a server Wasm hash claim.",
      '', 'The new metadata/ladder snapshot was recorded at 2026-10-29 00:01 UTC (server update 23:55 UTC): DOOMSDAY rank49/rating1998.6; SkibidiSloppers40/2024.7, BattleCats43/2018.4, test4 44/2018.4, ha²t52/1993.8. These are timestamped observations, not live predictions.', '',*source_table,'',
      'Comments in source mentioning earlier searches or test win rates were not independently audited here. A code block can exist while its switch is zero. The two full source reproductions support behavioural fidelity in those contexts; source defaults alone do not prove every server build setting.','',
      '## Opponents, duplicates and side coverage','', '| Sample | Match IDs / distinct trajectories | Wins | Mean final margin | Side coverage |','|---|---|---:|---:|---|',
      f"| All raw IDs | 85 / 59 | 39/85 | {summaries['All']['all']['final_margin']:.1f} | A75, B10 |",
      f"| One per raw replay hash | 59 / 59 | 25/59 | {u['all']['final_margin']:.1f} | Different map/opponent mixture from raw IDs |",
      f"| BattleCats, raw | 70 / 44 | 32/70 | {summaries['BattleCats']['all']['final_margin']:.1f} | A only |",
      f"| BattleCats, deduplicated | 44 / 44 | 18/44 | {b['all']['final_margin']:.1f} | A only |"]
    for name in ('SkibidiSloppers','test4','ha²t'):
        q=summaries['Opponent:'+name]['all'];lines.append(f"| {name}, ranked | {q['n']} / {q['n']} | {q['wins']}/{q['n']} | {q['final_margin']:.1f} | {q['sides']} |")
    lines+=['', 'Nineteen hash groups have duplicates. Repeating deterministic games supplies no new policy evidence. Deduplicated rows use the first occurrence of each exact replay hash; outcome is not used to choose representatives. Every match ID is still retained for audit. Sampling is narrow, mostly one opponent and one side; Wilson intervals in ANALYSIS_DATA are occurrence summaries, not a remedy for this selection bias. No causal v70-versus-v69 improvement is inferred.','',
      '## Where the fresh losses separate','', 'Below, every gap is ours minus the opponent in the **same game**, using 34 distinct loss trajectories. Native gold sources are capture, kills and bank bonuses. Inventory is purchase-cost value, not combat power.','',
      '| Round | n | Collected gems | Earned gold | Capture gold | Kill gold | Bank-bonus gold | Inventory cost | Unspent gold | Deaths |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for mark in ('25','50','75','100','150','250','500'):
        c=loss['curves'][mark];a,t=c['mean']['us'],c['mean']['them'];lines.append(f"| {mark} | {c['n']} | "+' | '.join(f"{a[f]-t[f]:+.1f}" for f in ('collected','earned_gold','capture_gold','kill_gold','bank_bonus_gold','equipment_cost','gold','deaths'))+' |')
    lines+=['',f"R250 cost-gap group-bootstrap95 {ci(loss['equipment_gap_250']['group_id']['interval95'])}; R100 {ci(loss['equipment_gap_100']['group_id']['interval95'])}. These exploratory intervals resample historical maps or groups, not independent tactical experiments. The exact R100 deficit is uncertain; the later gap is clearer in this sample.",
      '', 'At R100 the 34 distinct losses have almost equal collected gems (55.4 ours vs54.8 opponent). Their gold is already lower (254.5 vs300.8 earned), and by R250 the deficit is187.2 earned gold: capture110.4, kills28.0 and bank bonuses48.8. Unspent cash differs by only8.4 at R250 while costed inventory differs by180.0. This points toward income/conversion and allocation, not primarily a large unused team cash pile. First item purchase median is R71 ours versusR58.5 enemy (34 games); location and affordability still need exact-state review.',
      '',f"Final loss margin {loss['final_margin']:.1f} = collected margin {loss['decomposition']['income_margin']:.1f} + bag preservation {loss['decomposition']['preservation_margin']:.1f} + end-carried adjustment {loss['decomposition']['carry_margin']:.1f} (n=34). Pooled conversion is {100*loss['conversion']['us']:.1f}% ours versus {100*loss['conversion']['them']:.1f}% enemy. These are accounting identities, not recoverable gains. The same lost bag can affect income and preservation.",
      '',f"Repeated deaths: {loss['repeated_deaths']}/{loss['deaths']} in distinct losses versus {u['win']['repeated_deaths']}/{u['win']['deaths']} in distinct wins, using the unchanged physical-body/radius6/window250 criterion. Large-bag deaths>=40: {loss['large_bag_deaths']} events, {loss['large_bag_gems']} lost gems across34 distinct losses. Do not infer that all of this is avoidable or restart a rejected generic watchdog.",
      '', '## Which champion to inspect first','', 'Same-game, same-hero R100 pairs reduce roster-type confusion. They still share map/draft/role and outcome-selection confounding. The means are per physical body; Cassi and Issac are separate bodies.','',
      '| Hero / team result | Paired games | Earned-gold gap | Capture-gold gap | Inventory-cost gap | Collected-gem gap |','|---|---:|---:|---:|---:|---:|']
    for h in d['paired_same_hero_r100']:
        if h['name'] not in ('Marcella','Vendetta','Cassi','Issac'):continue
        q=h['mean_own_minus_opponent'];lines.append(f"| {h['name']} / {h['result']} | {h['same_game_same_hero_pairs']} | {q['earned_gold']:+.1f} | {q['capture_gold']:+.1f} | {q['equipment_cost']:+.1f} | {q['collected']:+.1f} |")
    lines+=['', 'The most specific opening lead is Marcella funding: 25 loss-side pairs versus17 win-side pairs. Her loss-side earned-gold deficit is68.0, including52.3 capture gold; the matching win-side deficit is only3.3. Vendetta instead leads both categories. Inspect the first claimed/captured groups and reward distribution before changing everyone’s shopping threshold.',
      '', 'Within our own pair, Cassi averages9.5 earned gold and4.5 inventory cost atR100 in20 distinct losses; Issac70.2/48.0. In15 distinct wins the direction reverses: Cassi70.7/46.0 versus Issac24.7/8.0. This is a resource-allocation association, not proof that transferring gold, copying a draft or changing twin behaviour would help. Per-appearance denominators and zero-receipt counts are retained in ANALYSIS_DATA.','',
      '## Exact current recall/bank timer conflict','', 'The three raw winning-bag-loop matches reduce to **two distinct trajectories** (2/34 distinct losses,0/25 distinct wins). Generic loops remain common in wins too. The following two diagnostic trace builds match their entire original replay bytes; all19 emitted records are trusted. Both maps have no_bank=0 and gated=0, so the observed cause is the private disable timer, not a gated altar.','',
      '| Map / actor | Restart rounds | Banked + bag | Enemy banked | Disable-until | HP | Full replay exact |','|---|---|---:|---:|---:|---:|---|']
    for r in traces['rows']:
        c=r['bank_disable_conflict_contexts'];v=c[0]['values'];lines.append(f"| {r['map']} / {r['actor']} | {c[0]['r']}–{c[-1]['r']} | {v['own_score']} + {v['bag']} | {v['enemy_score']} | {v['off_until']} | {v['hp']:.1f}/{v['maxhp']:.0f} | yes |")
    lines+=['', 'At current bot.cpp around6844, safe recall is cancelled because banked+bag is winning. `tribute_if_needed` around4530 refuses while `round < tribute_off_until`; around4634 assigns the80-round backoff after non-progress. At split R932 the timer runs until1011, beyond the original game’s end at937. The trace explains the restart loop, but it does not prove a feasible bank could beat the opponent or that preserving recall wins. The prior v69 bounded cancellation fix is a decision regression result, not a tested v70 release.',
      '', 'Current implementation research should distinguish (a) checking bank eligibility before win-only recall cancellation, from (b) allowing a winning bag to reconsider a stale bank-disable timer after route feasibility changes. The first addresses inconsistent control flow; the second is an untested race-policy hypothesis. Preserve the dangerous-channel escape guard. Do not shorten80 globally or claim these games as rescued wins.',
      '', 'A first split trace attempt failed only when the CLI published a bundle at a long Windows path; it produced no usable trace evidence. That folder is preserved. Shorter output paths succeeded. Failed runs are not omitted from CURRENT_BANK_TRACES.json.','',
      '## Concrete map and fuel leads','',
      '- **Guardians, 4ed82bb4…:**0–1557, own collected1389/lost1265/carried124,21 deaths and zero fuel-outs. Own R100 cost lead+90 becomes−240 byR250. Our team never banks; enemy first banksR1528. This is a new, separate conversion/capture-state case, not proof that the winning-bag timer conflict caused it. Seven large-bag deaths lose1136 gems. It merits exact bank-route/private-state reproduction before another opening change.',
      '- **Islands:** one distinct loss trajectory repeated twice, margin−184 and10 own fuel-outs per copy. The current source removed the earlier island-escape path. That is a code-risk lead; stranding, fuel origin and whether reintroducing it helps are not yet established.',
      '- **Vault:** the ranked win has28 own fuel-outs; this is28 of50 own fuel-outs across59 distinct trajectories. A second vault trajectory also wins. The incremental siege-scan path was removed in current source, but the native counts alone do not identify the costly call or prove a lost-game effect. Profile that path before modifying it.',
      '', '## Recommended next research order','',
      '1. Keep the two current exact recall cases as source-specific regression contexts. Test eligibility-gated cancellation and stale-timer reconsideration separately with warm state, short horizon and fuel fidelity; then apply the development/cluster/Bayes/release gate to any candidate.',
      '2. Deep-reproduce the new guardians zero-bank loss. Measure altar accessibility, actual bank attempts, private disable timers and visible enemies for each carrier. A high early gem count did not convert into a bank.',
      '3. Review Marcella’s first three assignments/reward receipts in the25 matched loss pairs versus17 win pairs. Diagnose who receives capture gold, who returns to shop and who protects the banker duringR100–250. No global numerical threshold is established.',
      '4. Profile the vault fuel-outs and islands loss with faithful instrumentation. Reintroducing old fixes is a new candidate experiment, not an automatic improvement.',
      '5. For any further match collection, seek existing missing-side and stronger-opponent v70 games. The present BattleCats set is all sideA and contains deterministic repeats. Fresh shared-quota probes would need direct authorization; none was created here.',
      '', 'ANALYSIS_DATA.json contains raw-ID and deduplicated summaries, paired curves, same-hero rows, native fault/fuel counts, duplicate hashes, map tables and per-game numbers. It contains no raw replay or credentials. All85 native summaries report zero bot faults on both sides. The old385/165 split, old predictions, old model and frozen source stay untouched. This addendum supplies new evidence; it does not constitute a production candidate or a ladder-strength claim.']
    write(S/'REPORT.md','\n'.join(lines))
    brief='''# Current-bot research addendum — v70

Read [the fresh report](../research/followup-v70-2026-10-29/REPORT.md) before applying the older v69 brief. Platform70 “home side” was independently downloaded from the official Submissions page; its policy and draft differ from the old study. Source files and all raw replays remain ignored locally.

- **Current defect:** the safe winning-bag recall cancellation around bot.cpp6844 ignores the bank-disable check around4530. Exact logs confirm five affected turns on split and ten on collision, with full replay fidelity. Both are non-gated maps. The cancellation remedy was bounded-tested on v69; its v70 match benefit is untested. Preserve the existing dangerous-channel guard and distinguish cancelling less from safely reconsidering a stale bank timer.
- **Current evidence:**85 IDs,59 distinct replay trajectories;70 BattleCats games represent44 trajectories, all sideA. Ranked record7/15, one-per-trajectory BattleCats18/44. Never call the70 games independent trials or mirrored-side coverage.
- **New priority:** in34 distinct losses, cost gapR100−33.5 (map interval includes0) grows toR250−180.0 (map95[−292.5,−75.8]). Capture/kill/bank-bonus income accounts for most of the earned-gold gap, while unused cash is close. InspectR100–250 income/conversion rather than assuming a universal early-shopping defect.
- **Specific role:** in25 same-game Marcella loss pairs, earned gold−68.0 and equipment cost−61.2 atR100; Vendetta leads+35.2/+22.2 in27 pairs. Inspect assignment/reward distribution first. This does not yet justify a global item/draft change.
- **Specific maps:** new guardians loss banks0/1389 collected, loses1265, despite+90 R100 cost lead. Vault win has28 fuel-outs. One islands loss trajectory has10 fuel-outs and is repeated twice. Each requires exact private-state/call-cost diagnosis; no blanket rollback is established.

Next steps are source-specific warm regressions, guardians conversion diagnosis, Marcella capture allocation and fuel profiling. No new policy was implemented or deployed in this follow-up. Use the existing benchmark gates and an untouched candidate holdout; do not tune on the spent old research-confirmation set.
'''
    write(ROOT/'docs/CURRENT_BOT_ADDENDUM.md',brief)
    p=ROOT/'docs/NEXT_BOT_BRIEF.md';original=p.read_bytes();marker=b'Current-source update (29 October)'
    if marker not in original:
        first=original.find(b'\n')+1;p.write_bytes(original[:first]+b'\n**Current-source update (29 October):** platform70 is now active. Read [CURRENT_BOT_ADDENDUM.md](CURRENT_BOT_ADDENDUM.md) for the new downloaded source, exact current recall traces and fresh85-game evidence before using the historical v69 recommendations below.\n'+original[first:])
    append(ROOT/'docs/LOSS_KNOWLEDGE.md','## Current v70 follow-up — 2026-10-29','''## Current v70 follow-up — 2026-10-29

Official source archive v70 “home side” downloaded;33 files,4 changed from v69. No V71 map profiles or V75 lone guard; A3_BACKOFF on while A3_ITEMS/FOCUS/NUMBERS/ONE_OWNER off. Two current original games reproduce byte-for-byte, both-scripted controls exact. Two sparse current traces also preserve complete raw bytes and confirm the bank-disable/recall conflict on split and collision (5/10 turns); both non-gated. No new candidate or win effect tested.

Fresh85 IDs collapse to59 distinct trajectories;26 BattleCats duplicates. All70 BattleCats games sideA;32/70 raw versus18/44 unique. Ranked7/15. Primary deduplicated losses34: cost gapR100−33.5 (interval crosses0), R250−180.0 (map95[−292.5,−75.8]); paired Marcella deficit atR100−68.0 earned gold/−61.2 cost across25 losses. New guardians0-bank case:1389 collected/1265 lost,21 deaths, no fuel-out, despite early+90 cost lead. Fuel lead: ranked vault win28; one distinct islands loss10, repeated twice. These are diagnostic priorities, not proven improvements.

Read docs/CURRENT_BOT_ADDENDUM.md and research/followup-v70-2026-10-29/REPORT.md / ANALYSIS_DATA.json. Old model/predictions/385-165 split remain frozen. Raw data and current-source copy stay local-only. No new matches queued, source policy changed, submission or activation performed.
''')
    append(ROOT/'docs/handoff.md','## 2026-10-29 current v70 follow-up','''## 2026-10-29 current v70 follow-up

Newest research: docs/CURRENT_BOT_ADDENDUM.md and research/followup-v70-2026-10-29/REPORT.md, ANALYSIS_DATA.json and STATE.md. Current downloaded platform70 “home side” differs from the historical v69 study. Added85 replay/native pairs,59 distinct trajectories, sideA-only BattleCats coverage; two source reproductions and two sparse private-state traces are full-game byte-exact. M1 recurs on split/collision; midgame resource divergence, Marcella funding and guardians zero-bank loss are the new diagnostic priorities. Old study stays frozen. No production policy changes, matches queued or deployments. User approval still covers analysis-only publication to analysis/deep-2026-10-28; raw evidence/current source remain ignored.
''')
    append(ROOT/'tools/README.md','## Current v70 follow-up tools','''## Current v70 follow-up tools

Separate namespace research/followup-v70-2026-10-29 and ignored artifacts/local-only/followup-v70-2026-10-29. Run from repo root; set NFS_REPLAY_ENGINE=2.0.0. No tool queues, uploads or activates anything.

| Tool | Usage |
|---|---|
| replay/followup_v70_intake.py | `source --archive <official-download.zip>`, `metadata`, `ingest`. PLAN fixes17 UI-observed v70 groups; paced public metadata, immutable source hashes, two-layer ZIP CRC and official CAMSTAT-to-JSON conversion. All raw data ignored. |
| replay/followup_v70_metrics.mjs | `validate` against five excluded old calibration files, then `extract` for the new85 only. SampleR25/50/75/100/150/250/500 and final; exact gold sources, physical ledgers, costed inventory, accepted loop actions. No old reserved mode. |
| replay/followup_v70_analysis.py | Build raw-ID and replay-hash-deduplicated summaries, same-game hero pairs, native D3/M1 observable proxy, maps/faults/fuel. ANALYSIS_DATA keeps denominator/selection caveats. |
| replay/followup_v70_reproduce.py | `prepare`, `validate --node <node.exe>`, `run`. Prepares a separate current allowlist and regenerates followup_v70_validate_inputs.mjs from the frozen validator with explicit study/path changes. Five excluded calibration checks precede four selected new input checks; run reproduces the original loss/win using exact enemy scripts. Official local build/run only. |
| replay/followup_v70_validate_inputs.mjs | Generated, committed derivative with its own new-study receipt. Does not alter the old validator or its receipts. Inputs are local JSON paths. |
| replay/followup_v70_trace.py | Two TRACE_PLAN cases, sparse bank-context logging only. Full replay/prefix fidelity and logical/emission-round cutoff; failed long-path run retained. |
| replay/followup_v70_report.py | Regenerate fresh report/addendum/state and append-once knowledge/handoff entries; validate source/splits/receipts and output FOLLOWUP_VALIDATION. |

The puppet generator additionally accepts independently validated `exploratory` scripts; prior script generation is unchanged. CLI builds need installed compiler-cache access. Keep short output names because long Windows bundle paths can fail after producing a summary.
''')
    state=f'''# Current v70 follow-up: research complete

Updated {now}. Read REPORT.md / ANALYSIS_DATA.json, ../../docs/CURRENT_BOT_ADDENDUM.md, CURRENT_BANK_TRACES.json and SOURCE_FIDELITY.json. This supplements the completed historical v69 study; it does not replace or retune it.

Completed: official current-source download (platform70, submission78116168-a5b6-42f3-bb19-1f7d1b17c45d, note home side),33 files/4 changed;17 groups/85 replay-native pairs, all validated. Native binary exports converted through official CLI4.0.0. Engine2.0.0; five excluded calibration equivalence checks,21,543 new resource-clock matches, zero unclassified sampled gold. Four new accepted-input scripts reapply byte-for-byte,4,318 round states. Two plain-source games and their both-scripted controls exact; two current sparse bank traces also full-game exact (19 trusted records,15 timer-conflict turns).

Important:85 IDs are59 trajectories,26 deterministic duplicates. BattleCats70 games=44 trajectories, all sideA. Raw32/70 vs unique18/44; ranked7/15. Distinct losses34: R100 cost−33.5 uncertain, R250−180.0 clearer; Marcella paired25-loss deficit−68.0 earned/−61.2 cost. Current recall conflict confirmed on split/collision, not just gated guardians. New guardians loss0 banked/1389 collected/1265 lost deserves separate conversion diagnosis. Vault win28 fuel-outs; one islands loss10, duplicated.

No policy changes, submissions, activations, account changes or new quota requests. Local unmodified-source compilation and diagnostic logging only. New source and raw data remain ignored under artifacts/local-only/followup-v70-2026-10-29; metrics/replay-inputs, source/src, summaries/, bundles/. Local builds under artifacts/tmp/followup-v70. Failed long UUID trace path preserved; successful map-based trace paths used. No credentials handled.

Next research: warm tests for recall eligibility vs stale bank-disable timer; exact guardians carriers/altar routes; Marcella first-three capture assignments across25 loss/17 win pairs; vault/islands fuel and route profiling. No global threshold, draft copy, rollback or rank gain is established. The old research reserved165 are spent and must not be reopened for tuning. Existing old model/split/predictions/frozen source remain unchanged.

Publication: same repository Infosuii/neural-networkk-battlecode and branch analysis/deep-2026-10-28, under the user's ongoing analysis-only push approval. Consult git log for the follow-up commit. Do not merge or publish raw replays/current-source blobs. Runtime paths remain in root project STATE.md; set NFS_REPLAY_ENGINE=2.0.0.
'''
    write(S/'STATE.md',state)
    root=ROOT.parent.parent/'STATE.md';old=root.read_bytes();heading=b'# Active Battlecode research handoff'
    if b'Latest current-version follow-up' not in old:
        text=b'\nLatest current-version follow-up: work/battlecode-deep-analysis/research/followup-v70-2026-10-29/STATE.md. Current platform70 source verified;85 new games,59 distinct trajectories; exact current recall conflict on split/collision. Read docs/CURRENT_BOT_ADDENDUM.md. Historical v69 report below remains frozen. No production changes or new quota used.\n'
        old=old.replace(heading,heading+text,1);root.write_bytes(old)
    # Delivery audit: only the new namespace plus five excluded calibration fixtures were inspected.
    assert read('DOWNLOADS.json')['replays']==read('DOWNLOADS.json')['native_summaries']==85
    assert read('METRICS_VALIDATION.json')['passed']==5 and len(source['files'])==33
    validator_hash=hashlib.sha256((ROOT/'tools/replay/followup_v70_validate_inputs.mjs').read_bytes()).hexdigest()
    assert read('PUPPET_INPUT_VALIDATION.json')['code_sha256']==validator_hash
    scripts=[json.loads((L/'replay-inputs'/(mid+'.json')).read_text(encoding='utf-8')) for mid in ['2c139f84-3f74-4d5b-925f-aa4484776f80','2425dc90-76c7-4818-a3c4-db2fe40d4f70','9c7c4fcd-c4d5-4ed6-ad94-c21dc6a756ad','951e9c30-fc77-4241-991c-23cac3abfd09']]
    assert all(s['validation']['replay_bytes_identical'] and s['validation']['code_sha256']==validator_hash for s in scripts)
    assert sum(s['validation']['round_states_identical'] for s in scripts)==4318
    for f in source['files']:
        assert hashlib.sha256((L/'source'/f['path']).read_bytes()).hexdigest()==f['sha256']
        assert (L/'source'/f['path']).read_bytes()==(ROOT/'artifacts/tmp/followup-v70/plain'/f['path']).read_bytes()
    maps={p.stem.replace('-','').replace('_',''):p for p in (ROOT/'maps/local-benchmarks').glob('*.map26a')};physical=0
    for row in d['rows']:
        mid=row['match_id'];native=json.loads((L/'replays'/(mid+'.summary.json')).read_text(encoding='utf-8'));raw=(L/'replays'/(mid+'.repl26a')).read_bytes();mp=maps[row['map'].replace('-','').replace('_','')].read_bytes()
        assert raw[14:14+len(mp)]==mp and hashlib.sha256(mp).hexdigest()==native['match']['mapHash']
        assert hashlib.sha256(raw).hexdigest()==row['replay_sha256']
        assert native['match']['engineBuildHash']=='85aa7167b44db7cea97509f55e997750520e33d644e9f4f90d6128c50eba1d21'
        for c in native['champions']:
            m=c['metrics'];lost=sum(int(e['value']) for group in native['events'] if group['kind']=='gemLoss' and group['owner']['id']==c['id'] for e in group['entries'])
            assert int(m['collectedGems'])==int(m['submittedGems'])+int(m['gems'])+lost
            assert int(m['earnedGold'])+int(m['saleRefunds'])==int(m['spentGold'])+int(m['gold']);physical+=1
        for team in ('teamA','teamB'):assert sum(int(c['metrics']['submittedGems']) for c in native['champions'] if c['team']==team)==int(next(t['submittedGems'] for t in native['teams'] if t['team']==team))
    for name in ('CARD_PREDICTIONS.json','MOMENT_SAMPLE.json','DETECTOR_SPEC.json','MODEL_SPLIT.json','WINPROB_MODEL.json'):
        p=ROOT/'research/deep-2026-10-28'/name;assert p.read_bytes()==subprocess.check_output(['git','show','19109c4:research/deep-2026-10-28/'+name],cwd=ROOT)
    subprocess.run(['git','diff','--exit-code','19109c4','--','bots'],cwd=ROOT,check=True,capture_output=True)
    for p in (ROOT/'tools/replay').glob('followup_v70*.py'):ast.parse(p.read_text(encoding='utf-8'))
    assert len({r['replay_sha256'] for r in d['rows']})==59 and sum(len(s['match_ids'])-1 for s in d['duplicate_sets'])==26
    for r in d['rows']:assert r['faults']=={'us':0,'them':0}
    assert all(r['our_side']=='a' for r in d['rows'] if r['opponent']=='BattleCats')
    result={'passed':True,'games':85,'groups':17,'native_summaries':85,'unique_trajectories':59,'deterministic_duplicates':26,'own_and_enemy_native_faults':0,'clock_checks':21543,'calibration_games':5,'current_input_scripts':4,'current_input_round_states':4318,'plain_source_exact_games':2,'both_script_controls_exact':2,'exact_sparse_trace_games':2,'trusted_trace_records':19,'bank_disable_conflict_turns':15,'old_reserved_trajectories_used':0,'old_model_split_predictions_unchanged':True,'frozen_sources_unchanged':True,'new_matches_requested':0,'production_policy_changes':0,'raw_data_and_source_committed':False,'limits':'Exploratory, mostly one opponent and one side. Native source traces confirm current decision inconsistency; no v70 candidate intervention, release gate or ladder-strength improvement tested.'}
    result.update(embedded_maps_and_native_map_hashes=85,native_physical_ledgers=physical,compiled_plain_source_byte_exact_to_download=True)
    save(S/'FOLLOWUP_VALIDATION.json',result);print(json.dumps(result))
if __name__=='__main__':main()
