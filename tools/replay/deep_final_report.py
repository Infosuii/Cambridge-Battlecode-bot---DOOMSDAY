"""Assemble final research/brief from fixed receipts; never fit or tune on reserved data."""
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path
from deep_preflight import ROOT
from deep_detector_report import save
from deep_json import save_table

S=ROOT/'research/deep-2026-10-28'


def read(name):return json.loads((S/name).read_text(encoding='utf-8'))


def write(path,text):path.write_bytes((text.rstrip()+'\n').encode('utf-8'))


def append(path,marker,text):
    data=path.read_bytes() if path.exists() else b''
    eol=b'\r\n' if data.count(b'\r\n')>data.count(b'\n')/2 else b'\n'
    if marker.encode() in data:
        path.write_bytes(data.rstrip(b'\r\n')+eol);return
    path.write_bytes(data+(eol if data else b'')+text.rstrip('\n').replace('\n',eol.decode()).encode('utf-8')+eol)


def pct(x):return 'n/a' if x is None else f'{100*x:.1f}%'


def interval(x):return 'insufficient support' if x is None else f'[{100*x[0]:+.1f},{100*x[1]:+.1f}] pp'


def d3line(name,d):
    l,w=d['losses'],d['wins']
    return f"| {name} | {l['event_numerator']}/{l['event_denominator']} ({pct(l['event_rate'])}; n={l['n']}) | {w['event_numerator']}/{w['event_denominator']} ({pct(w['event_rate'])}; n={w['n']}) | {100*d['event_rate_difference']:+.1f} pp | {interval(d['event_rate_map_cluster']['interval95'])} | {interval(d['event_rate_opponent_cluster']['interval95'])} |"


def main():
    now=datetime.now(timezone.utc).isoformat();final=read('FINAL_CONFIRMATION.json');det=read('DETECTOR_DATA.json');time=read('TIMELINE_DATA.json');cards=read('CARD_DATA.json');model=read('WINPROB_MODEL.json');profiles=read('PROFILE_DATA.json');m1=read('M1_EXAMINED.json')
    assert final['games_processed']==165 and final['own_games']==160 and final['no_retuning']
    loss_cards=[r for r in cards['rows'] if r['kind']=='loss'];drop_total=sum(r['drop'] for r in loss_cards)
    m1coverage=next(r['drop'] for r in loss_cards if r['card_id']=='C004')/drop_total
    defs=[
      ('M1','Recall cancellation ignores temporary banking disable','new-open','causal (tested), bounded decision only',m1coverage,.9,.3,2,
       'Safe winning-bag recall is cancelled while tribute_off_until still forbids the requested bank; recall restarts.',
       'bots/live-69/src/bot.cpp: play_turn winning-bag recall condition around7005; tribute_if_needed eligibility around4535, disable timer around4639',
       'Require !w.no_bank && round>=tribute_off_until before the win-only cancellation; preserve the existing dangerous-channel cancellation branch. Recommendation only.',
       ['C004'],'TAKEOVER_RESULT.json',None),
      ('M2','Repeated death in the same area or to the same killer','known-rejected-fix; mechanism still open','association',cards['category_summary']['repeat_death']['surrogate_drop_share'],.3,.3,6,
       'Existing D3: same physical actor has a prior death within250 rounds at Chebyshev radius6 or to the same enemy champion ID.',
       'bots/live-69/src/bot.cpp: handle_enemies around3162, V75_LONE around3988; tactics.cpp act_enemy_before_walk around27, survive_contact around127 (compiled off)',
       'No replacement threshold is established. Diagnose exact victims and current visibility/TTK before choosing a narrow fight-admission rule; do not re-enable a blanket watchdog or retreat switch.',
       ['C070','C082','C060'],'DETECTOR_DATA.json','research/v66/RESULTS.md'),
      ('M3','Early economy and equipment deficit','known-open','association',cards['category_summary']['enemy_camp_income']['surrogate_drop_share'],.25,.5,12,
       'Paired R100/R250 collected-gem, earned-gold and inventory-cost deficits in losses; not evidence that price equals fighting power.',
       'bots/live-69/src/bot.cpp: opening allocation/group scoring, V71 profile and A2 per-turn block around6740–6910; source draft/item paths require separate ablation',
       'No universal numerical change is supported. Compare one opening allocation on a specified map and one existing purchase milestone at a time; hold draft and all other knobs fixed.',
       ['C018','C048','C060'],'TIMELINE_DATA.json','research/v66/RESULTS.md'),
      ('M4','Large bags lost before conversion','known-open','association',cards['category_summary']['large_bag_loss']['surrogate_drop_share'],.3,.4,8,
       'Registered D2 high-bag native death loss>=40; card windows with such losses. A large unbanked bag is not itself a mistake.',
       'bots/live-69/src/bot.cpp: tribute_if_needed around4532, channel guard/recall cancellation around7005, combat-before-bank order around7280',
       'Fix M1 first. Test bank feasibility and interruption/escape context per carrier; do not globally lower carry65 or disable flee-attacks based on these observations.',
       ['C004','C034','C011'],'CARD_DATA.json',None),
      ('M5','Enemy receives a camp reward after our native clear','known-open; confounded','association',cards['category_summary']['enemy_camp_income']['surrogate_drop_share'],.15,.15,12,
       'Registered D5 reward-to-enemy-after-native-clear event, distinct from every failed progress transition. Enemy-camp-income card label is only a broad coverage proxy.',
       'bots/live-69/src/bot.cpp: group job claims, capture approach/onsite completion and V69_CAPTURE_STALL; no exact faulty branch established',
       'No production rule established. First reproduce a handoff with exact original camp-group ID and claimant visibility; compare staying until receipt against a valid alternative within a bounded horizon.',
       ['C048','C026'],'DETECTOR_DATA.json',None)
    ]
    mistakes=[]
    for id,title,status,confidence,ceiling,fixability,transfer,effort,definition,code,change,examples,evidence,rejected in defs:
        item={'id':id,'title':title,'status':status,'confidence':confidence,'definition':definition,'code_location':code,'recommended_next_step':change,'examples':examples,'evidence_file':evidence,'rejected_evidence':rejected,
              'planning':{'surrogate_coverage':ceiling,'fixability_judgment':fixability,'transfer_judgment':transfer,'effort_hours_including_fuel_risk':effort,'score':ceiling*fixability*transfer/effort},
              'cost':{'surrogate_drop_coverage':ceiling,'sample_loss_windows':90,'sample_loss_games':65,'causal_recoverable_gems':None,'reason':'No identified mapping from conditional win probability to recoverable gems; event labels overlap and reflect downstream state.'},
              'hands_off_scope':'M1 observable proxy, D3 and native final accounting only; all other mechanisms unconfirmed on reserved data'}
        if id=='M1':item.update(examined_proxy=m1['summary'],reserved_proxy={k:v['M1_proxy'] for k,v in final['summary'].items()},exact_source_cases=1,native_bag_at_risk=736,regression_case='tests/loss_cases/M1-recall-disabled-bank.json',winner_contrast='Proxy is more common in examined wins; a vault control banks343 but is not the same state.')
        if id=='M2':item.update(examined={k:v['D3'] for k,v in det['comparisons'].items()},reserved={k:v['D3'] for k,v in final['summary'].items()},winner_contrast='188/1028 examined-win deaths repeat versus722/2337 loss deaths. Traces also show flee in both outcomes.')
        if id=='M3':item.update(examined=time['opening_gaps'],reserved_accounting={k:v['accounting'] for k,v in final['summary'].items()},winner_contrast='R100 paired inventory-cost gap: loss mean-86.7 (n191), win+90.5 (n169); map/opponent intervals in TIMELINE_DATA.')
        if id=='M4':item.update(examined={k:v['D2:high_bag_death'] for k,v in det['comparisons'].items()},winner_contrast='Climb high-bag-death games38/83 losses versus38/119 wins; opponent-cluster interval crosses0. Vault loss carrier was already banking then fleeing.')
        if id=='M5':item.update(examined={k:v['D5:reward_to_enemy_after_native_clear'] for k,v in det['comparisons'].items()},winner_contrast='Climb52/83 losses versus52/119 wins; opponent-cluster interval crosses0. No exact same-state winner experiment.')
        mistakes.append(item)
    ranked=sorted(mistakes,key=lambda r:-r['planning']['score'])
    catalogue={'evidence_policy':'One tested decision inconsistency, four associated/contextual candidates; not five proven bot bugs','priority_formula':'surrogate coverage × subjective fixability × subjective transfer / hours including fuel risk','priority_limits':'Planning sensitivity score, not expected win-rate gain. Coverage labels overlap; M1 uses its later associated swing window, M3/M5 share broad camp-income coverage, not an identified causal ceiling. Effort and probabilities are judgments, not measurements. Scores must not be added or read as percentages of recoverable wins.','mistakes':mistakes,'ranking':[m['id'] for m in ranked]}
    save(S/'mistakes.json',catalogue)
    priority=['| ID | Coverage proxy | Fixability* | Transfer* | Effort h* | Planning score |','|---|---:|---:|---:|---:|---:|']
    for m in ranked:
        p=m['planning'];priority.append(f"| {m['id']} | {pct(p['surrogate_coverage'])} | {p['fixability_judgment']:.2f} | {p['transfer_judgment']:.2f} | {p['effort_hours_including_fuel_risk']} | {p['score']:.5f} |")
    priority+=['','*Judgments fixed from examined evidence. The score ranks research work; M1 is the first implementation-ready patch. Other entries need a concrete diagnosis before a production change. Coverage is an overlapping surrogate label, not a causal gain ceiling; no defensible gem equivalent is identified.']
    lines=['# Mistake catalogue and priorities','',catalogue['evidence_policy']+'.', '',catalogue['priority_limits'],'',*priority]
    for m in mistakes:
        lines += ['',f"## {m['id']}: {m['title']}",'',f"**{m['confidence']}; {m['status']}.** {m['definition']}",'',f"Evidence: {m['evidence_file']}; cases {', '.join(m['examples'])}. Source: {m['code_location']}.",'',m['winner_contrast'],'',m['recommended_next_step'],'',f"Cost coverage: {pct(m['planning']['surrogate_coverage'])} of summed conditional model drop in90 selected windows from65 losses. This is a generous context label, not avoidable WPA. Recoverable gem equivalent: not identified."]
        if m['rejected_evidence']:lines += ['',f"Prior non-transfer/rejection: [{m['rejected_evidence']}]({('../../'+m['rejected_evidence'])})."]
    lines+=['','## Final fixed-frequency confirmation','','Only D3, the M1 observable proxy and final native accounting were opened on the165 reserved games (160 own,5 references not used in own contrasts). M3 opening inventory, D2/D5/D11 and full D1–D11 families were not re-screened there. Exact bank-disable state is private bot memory: the M1 proxy cannot confirm the mechanism in additional games. See FINAL_CONFIRMATION.md and FINAL_CONFIRMATION_PLAN.json, committed before access.','', 'Matched controls are retained in MATCHED_CONTROLS.json:101 own-win examples and96 top-winner examples, with77 and32 same-map matches. Matching is approximate, uses conditional state features and does not establish a strategy intervention.']
    write(S/'MISTAKES.md','\n'.join(lines))

    confirm=['# Final reserved-set confirmation','','Plan/code were committed in590d106 before the reserved extraction. Five calibration files and all385 examined games passed exact M1/D3 equivalence;360 own native accounting results also matched. No detector thresholds, cards, model parameters or category definitions were changed after opening the reserved set. Reserved action traces stay local-only.','','## Repeated deaths','','Per-death normalization, physical body identity, radius6/window250 and repeated enemy ID match the registered D3 exactly. Intervals resample maps or opponents; these remain marginal historical associations.','','| Cohort | Loss repeated/deaths | Win repeated/deaths | Difference | Map95 | Opponent95 |','|---|---|---|---:|---|---|']
    for cohort,v in final['summary'].items():confirm.append(d3line(cohort,v['D3']))
    direction=all(final['summary'][c]['D3']['event_rate_difference']>0 for c in ('All','Climb'))
    confirm+=['',f"Predeclared directional criterion (positive overall and Climb): {'met' if direction else 'not met'}. Interval support is reported separately; a direction alone is not a causal or significance claim.",'','Overall rate difference is+12.0pp with both cluster intervals above0. Climb is+6.4pp, but map95[-4.1,+15.2] and opponent95[-4.4,+25.8] include0: Climb-specific precision did not replicate the examined strength. Learn has only one win; its bootstrap contrasts are unstable despite the printed conditional intervals and must not establish a cohort conclusion.','', '## Recall-loop proxy','','Winning-bag descriptor uses the previous completed round on every round of a qualifying >=3-round episode. It does not reveal tribute_off_until or prove the source conflict.','','| Cohort/result | Games | Any loop | Winning-bag loop | Episodes | Restart turns / accepted recall starts |','|---|---:|---:|---:|---:|---:|']
    for c,v in final['summary'].items():
        for out,q in v['M1_proxy'].items():confirm.append(f"| {c}/{out} | {q['n']} | {q['flagged']}/{q['n']} | {q['winning_bag_flagged']}/{q['n']} | {q['episodes']} | {q['restart_turns']}/{q['accepted_recall_starts']} |")
    confirm+=['','Wilson intervals for both occurrences are in FINAL_CONFIRMATION.json. This proxy screen does not promote generic loops into a cause of losses. The exact timer conflict is still confirmed in one examined loss only.','','## Native final-margin identity','','| Cohort/result | n | Banked margin | Collected margin | Bag preservation | End-carried margin |','|---|---:|---:|---:|---:|---:|']
    for c,v in final['summary'].items():
        for out,q in v['accounting'].items():confirm.append(f"| {c}/{out} | {q['n']} | {q['final_margin']:.1f} | {q['income_margin']:.1f} | {q['preservation_margin']:.1f} | {q['carry_margin']:.1f} |")
    confirm+=['','These are exact additive accounting components, not recoverable improvement. Killed bags can also enter the other side’s collected income. The165 games are now spent for this final research-frequency check. They are not a fresh holdout for a future candidate. Reserve new maps/games for its release gate.']
    write(S/'FINAL_CONFIRMATION.md','\n'.join(confirm))

    all_loss=time['summary']['all']['loss'];climb_loss=time['summary']['Climb']['loss'];f=final['summary']['All']['accounting']['loss'];test=model['metrics']['test'];fp=final['summary']['All']['M1_proxy']
    report=f'''# DOOMSDAY deep analysis — final research handoff

Updated {now}. Evidence labels are measured, association, or causal (tested). The result is a next-bot research brief, not a released bot or demonstrated ladder improvement.

## Findings that change the next decision

1. **Measured race deficit:** in191 examined losses, mean banked margin{all_loss['final_margin']:.1f} = collected income{all_loss['income_margin']:.1f} + bag preservation{all_loss['loss_preservation_margin']:.1f} + end-carried{all_loss['carried_margin']:.1f}. Income accounts for{100*all_loss['income_margin']/all_loss['final_margin']:.1f}% of this accounting deficit. Climb83 losses: banked{climb_loss['final_margin']:.1f}, income{climb_loss['income_margin']:.1f}. Reserved losses n={f['n']}: banked{f['final_margin']:.1f}, income{f['income_margin']:.1f}. This identifies where the race is lost, not how much a fix can recover.
2. **M3 association, broad research priority:** inventory-cost gap exists by R100:−86.7 in191 losses versus+90.5 in169 wins. Climb83 losses−91.8, map95[−121.0,−61.2], opponent95[−124.7,−78.6]. No exact opening/item/draft replacement has been proved.
3. **M2 association:** repeated deaths remain the strongest normalized detector lead. Examined losses722/2337 deaths versus wins188/1028; contrast+12.6pp, map95[+7.2,+18.3], opponent95[+3.8,+16.9]. Reserved losses264/946 deaths (83 games) versus wins72/454 (77 games):+12.0pp, map95[+5.9,+18.1], opponent95[+5.0,+20.3]. Climb reserved39L/54W:+6.4pp, both cluster intervals include0. Overall replication is stronger than the rating-relevant subgroup. Existing broad watchdog/retreat fixes failed; the traces do not rehabilitate them.
4. **M4 association:** loss-side pooled conversion63.1% versus the opponents’88.4% across191 losses. Large-bag losses label12/90 selected windows (17.1% of surrogate drop), but a vault carrier was already banking, then fleeing. Do not infer “always bank earlier” or “stop flee-attacks”.
5. **M1 causal (tested), narrow:** winning-bag recall can cancel for a bank disabled by its own timer. One exact guardians case, with736 carried, passes a bounded decision diagnostic after the unchanged bot fails. The broad winning-bag-loop proxy occurs in1/191 examined losses versus7/169 wins; reserved{fp['loss']['winning_bag_flagged']}/{fp['loss']['n']} losses versus{fp['win']['winning_bag_flagged']}/{fp['win']['n']} wins. It is a concrete cheap patch candidate with small observed breadth, not the main explanation of losses. M5 capture handoffs remain opponent-confounded.

## Dataset, identity and integrity

111 historical groups/555 replay-native pairs retrieved through the official website:550 accepted study games, five excluded calibration games. Fixed split385 examined (360 own:191L/169W, plus25 top-v-top) /165 reserved (160 own plus5 top-v-top). Total top-v-top30. The105 prediction-first cards cover90 windows from65 losses across45 maps and15 control wins. Dataset selection is purposive; error404 alone contributes155/360 examined own games. Cohort ranks are the frozen historical snapshot, not today’s ladder.

Study platform69, submission f91de3f0-0453-409e-b712-b86067eecbca, note “v75 ladder duel candidate”. Provided ZIP SHA2560433755c1cbc5f120247c132a6c875912f14c3ac5f36abaa7edbfe20845b325c; all33 frozen source files match. Current activation time/server Wasm identity remain independently unverified. All12 selected full games nevertheless reproduce byte-for-byte using the rebuilt source. CLI4.0.0; engine2.0.0/build85aa7167b44db7cea97509f55e997750520e33d644e9f4f90d6128c50eba1d21. No engine mixing.

All555 initial reconciliations,5356 physical champion ledgers and111 metadata checks pass. Corrected timelines cover385 examined games with11,853,045 resource-clock matches and zero unclassified earned gold. Step23 is movement blocked; only4/22 with differing endpoints establish physical arrival. DECODER_CORRECTION.md proves corrected action labels leave every385-game model feature matrix and native-dependent detector set unchanged.

## Opponents and matchup comparisons

[P5_OPPONENTS.md](P5_OPPONENTS.md) contains eight paired scorecards: five Learn opponents plus error404, Univardisty of Shingtonwash and SkibidiSloppers. It covers draft/opening, R100/250/500 economy with explicit surviving-game coverage, conversion, deaths, geometric contact damage, basic focus, low-HP separation, vision, middle camp-gem share, time proxies and fuel. All385 contact extracts pass; basic-focus counts match independent accepted-input targets in all ten calibration team comparisons.

The78 opponent×map-size strata include Wilson win intervals and map-cluster margin intervals. Size bands are reproducible proxies; walls/islands/gates are not automatically classified. “Observed one-sided” is a historical label, not proof of structural impossibility. Enemy high-bag loss rates are opportunity ceilings; no source intent, hidden-information exploit or winning counter-policy is established.

## Race, openings and winners

[P3_TIMELINES.md](P3_TIMELINES.md) and TIMELINE_DATA.json preserve paired final identities, opening gaps and both teams’ actual drafts, physical rosters, first three observed camp targets/receipt rounds, first purchase and pre-large-reward spread. The191-loss camp-receipt gap is−358.2 gems/game. The opponent usually collects more and converts more in losses; these components interact. Price cost is not combat power; stationary/travel/channel time is not automatically waste.

Against error404 we have111/155 examined wins, while against Intercontinental Fish0/17, Mite2/14 and newer team0/6. The different opponent mixture matters; all-Learn or all-Climb aggregates are not rank-proportional forecasts. Copying a winner’s draft or whole policy is not supported: prior draft transfer−89 and whole-policy cloning0–12 remain negative evidence.

## Win-probability model and category coverage

Fixed game split231 train/77 calibration/77 internal test, committed before fitting. Symmetric logistic model deep-logistic-v1, L2=0.01, calibration inverse-temperature≈0.872867. On77 internal test games: log-loss{test['model']['log_loss']:.4f}, Brier{test['model']['brier']:.4f}, ECE10{test['model']['ece10']:.4f}; bank-only log-loss{test['bank_only']['log_loss']:.4f}. No reserved game was used for fitting, tuning or card selection. The internal test remains historical evaluation, not a candidate-release holdout.

Across90 selected loss windows (65 games), opponent purchases label79 (81.8% of summed model drop), camp receipts63 (70.5%), opponent banks36 (44.0%), own deaths23 (28.2%), large-bag losses12 (17.1%), repeated deaths2 (1.9%). Labels overlap. Purchases move gold into inventory while the model omits unspent cash, so abrupt purchase-associated drops can be measurement effects. Do not interpret conditional coefficients or these coverage shares as causal event WPA, recoverable wins or gem equivalents. [P3_WINPROB.md](P3_WINPROB.md), [P4_CARDS.md](P4_CARDS.md) and CARD_AUDIT.md record these limits.

## Deep causal evidence and regression

[P6_DEEP_TRACK.md](P6_DEEP_TRACK.md) records ten exactly reproduced losses/two wins,12 exact both-script controls,24 state comparisons/25,184 samples, nine detailed faithful trace windows and three sparse exact trace windows. Fuel-perturbed failed probes are retained and excluded after divergence. The vault loss was already fleeing; C082 victim7 differs from its card focus6. Source defaults, stale comments and team-level swing labels must not replace effective private-state traces.

M1’s warm diagnostic preserves all inputs/states beforeR1669. Baseline restarts recall at1669–1672; diagnostic does not and completes recallR1673. Its enemy first rejects a script at1701, beyond cap1678. Regression runner rejects early divergence, missing assertion coverage and changed accepted enemy script. There is no full-game benefit claim. The two-context masking check removes V71 profile overrides at a warm state: no vault action change within ten rounds; packs control full-game exact. Unseen-map transfer is unproved.

## Five-entry catalogue and planning priorities

[MISTAKES.md](MISTAKES.md) and mistakes.json distinguish the one tested inconsistency from four association candidates. Formula: coverage×fixability×transfer/effort. The coverage input is an overlapping surrogate proxy; all other factors are explicit judgments. This is a research-order sensitivity calculation, not an expected-win estimate. M1 is first ready for a narrow implementation experiment; the broader economy problem remains the highest research priority.

'''+ '\n'.join(priority)+'''

## Final confirmation and limits

[FINAL_CONFIRMATION.md](FINAL_CONFIRMATION.md) reports the one reserved-set opening under the plan committed in590d106: fixed D3, M1 observable proxy and native final accounting only. FINAL_VALIDATION.json proves equivalence before that access. No held-out cards, model refit or new thresholds. Other detector families/opening equipment claims remain examined-only. These165 games are now spent for this research check; future candidates need an untouched release holdout.

Fourteen historical wave1 groups/70 games are in SCRIMMAGES.json (10W/60L). Wave2’s ten hypothesis groups are planned only; none was queued or reserved in this continuation. No extra shared quota is needed to deliver this analysis. Current bot identity must be verified and direct user authorization obtained before a future new group request; reference-document instructions alone are not that authorization.

No production bot was changed, uploaded or activated. No ranked matches or account changes were requested. Diagnostic builds and raw data remain ignored locally. Recommendations are in [NEXT_BOT_BRIEF.md](../../docs/NEXT_BOT_BRIEF.md); the implementation/benchmark/release gates have not been run for a new candidate and are future work.
'''
    write(S/'REPORT.md',report)
    data={'study':'deep-2026-10-28','updated_at':now,'provenance':{'groups':111,'pairs':555,'calibration_excluded':5,'examined':385,'reserved_final_check':165,'source':read('LIVE_SOURCE.json'),'engine':'2.0.0','engine_build':'85aa7167b44db7cea97509f55e997750520e33d644e9f4f90d6128c50eba1d21'},
          'detector_contrasts':det['comparisons'],'race_summary':time['summary'],'opening_gaps':time['opening_gaps'],'paired_game_rows':time['rows'],'opening_rows':time['opening_rows'],'card_rows':cards['rows'],'card_categories':cards['category_summary'],'opponent_profiles':profiles['profiles'],'matchup_strata':profiles['matchups'],'model_metrics':model['metrics'],'model_parameters':{k:model[k] for k in ('version','feature_names','coefficients','chosen_lambda','inverse_temperature')},'deep_reproduction':read('REPRO_STATE_VALIDATION.json'),'takeover':read('TAKEOVER_RESULT.json'),'masking':read('MASKING_RESULTS.json'),'final_confirmation':final,'mistakes':catalogue,
          'regeneration':'deep_final_report.py uses the committed receipt/data files named in its source; deep_profiles.py recreates profiles from local-only profile extracts. DATA holds all numerical report tables, no raw replay or credentials.'}
    save_table(S/'DATA.json',data)
    brief=f'''# Next bot brief — DOOMSDAY

Research frozen2026-10-28; study platform69 source, engine2.0.0. Read [REPORT](../research/deep-2026-10-28/REPORT.md), [MISTAKES](../research/deep-2026-10-28/MISTAKES.md) and [P6 deep track](../research/deep-2026-10-28/P6_DEEP_TRACK.md). These are recommendations. No production candidate is implemented or approved for release by this analysis.

## First concrete patch: M1 recall/bank eligibility

At frozen bot.cpp `play_turn` around7005, permit the winning-bag-only recall cancellation **only when** `!w.no_bank && round >= tribute_off_until`. Keep the existing dangerous-channel cancellation/escape branch intact. `tribute_if_needed` around4535 already uses this eligibility rule; around4639 sets the80-round disable after twenty non-progress bank turns. Match those semantics so recall is not cancelled for a bank the bot refuses.

Run the condition once per champion turn at the existing recall-cancel branch. Do not add map/camp scans or logging in hot loops. Expected tested effect: remove the cancel/restart inconsistency while retaining safe recall, not736 recovered gems or a proven match win. Exact evidence: C004 actor1, guardians, R1669 takeover; unchanged source fails with4 restart pairs, diagnostic passes with0 and recall completesR1673. Observed breadth: exact source mechanism confirmed in1 examined loss; winning-bag proxy1/191 examined losses, reserved{fp['loss']['winning_bag_flagged']}/{fp['loss']['n']} losses. Generic loops also occur in wins. Planning score{mistakes[0]['planning']['score']:.5f} uses generous associated-window coverage and is not expected gain.

Mandatory regression: tests/loss_cases/M1-recall-disabled-bank.json using the documented warm replay fixture. Preserve accepted inputs and every-round state beforeR1669, enemy accepted script through assertion end, full assertion coverage and default fuel. Original must fail, candidate must pass. Compare at most ten rounds; stop sooner on script rejection. A candidate that changes the opening cannot be evaluated as this same-state case without a warm takeover build.

## Broader research queue

'''+ '\n'.join(priority)+'''

- **M3 economy/opening:** paired R100 inventory deficit−91.8 in83 Climb losses, later income gap−382.0. Locate the first map-specific allocation or purchase difference before changing policy. Keep draft fixed and compare one camp-route assignment or existing item milestone per experiment. No new universal carry/shop/aggression value is supported. Place new bookkeeping once per turn or in initialization, not per-group scoring. Require preserved source/knob identities, an exact opening comparison and a separate useful-equipment measure. No confirmed bug case exists yet for this broad category.
- **M4 bags:** C034 carrier343 was banking before an interrupt, then fleeing; banking “earlier” is not an established fix. Start with M1, then test one bank-route eligibility/interruption decision in C034 or C011 with warm state and original danger guards. Do not disable flee-attacks globally. Carry65/shop138 are observed effective values, not recommended new thresholds.
- **M5 capture handoff:** Climb flags52/83 losses and52/119 wins, with opponent-cluster interval crossing0. Reproduce a specific original camp-group reward handoff before writing an ownership/abandonment rule. C048/C026 are starting contexts, not executable confirmed failures. Avoid new per-camp scans.
- **M2 repeated death:** strongest normalized association, but card coverage is only2/90 windows and a generic watchdog already lost−126, strict engage rule−262, softer leave−18 in prior local tests (research/v66/RESULTS.md). Diagnose victim7 in C082 and actor6 in C070; preserve their own vision, current local numbers and TTK/TTD. Do not revive those global switches merely because D3 replicated. V58_SURVIVE is currently0; enabling it is a new unvalidated intervention.

No numerical threshold or exact patch is claimed for M2–M5. These require a concrete measurable decision defect and a baseline-failing regression before implementation. Missing causal evidence must not be filled with a plausible-looking heuristic.

## Candidate test and release gate

1. Copy frozen source into a new diagnostic/development directory; never edit bots/live-69/src or another frozen bot. Record source/toolchain/engine/Wasm hashes and effective V71/A2 settings. Baseline source should reproduce the selected12 cases exactly before judging a new mechanism.
2. Run the M1 baseline-fail/candidate-pass warm regression. Add cases only for confirmed failures. Retain the non-profile packs control and the vault masking context; keep existing dangerous-channel behaviour.
3. Run `bash tools/bench3.sh <absolute candidate dir> <absolute live-base dir> <absolute output prefix> 1 2 3` on the28 development maps/both sides. Use `MAPS_OVERRIDE="02guardians"` for the target-map screen. Capture complete expected game counts and zero native faults on **both** sides; fuel-sensitive logging stays out of production builds.
4. Compare paired candidate/base runs against the same opponent using `python tools/bench_compare.py <candidate-prefix> <base-prefix>` and `python tools/bench_bayes.py <candidate-prefix> <base-prefix>`. Retain a mechanism only if its map-clustered95% interval is above0 and the Bayesian verdict supports it. Preserve the repository target-map and overall non-regression gates in docs/handoff.md; a local same-lineage win does not prove transfer to strong teams.
5. Freeze the entire candidate before `HOLDOUT=1 MAPS_OVERRIDE="<untouched final maps>" bash tools/bench3.sh ...`. Run the release holdout once per frozen candidate, with all-count/fault checks. The165 games opened for this research confirmation are already spent and cannot serve as a fresh candidate holdout.
6. If a small strong-opponent probe is needed, verify current platform identity and obtain direct authorization for its shared quota; pin opponent/version/map/side and write the hypothesis before queuing. Wave2 remains unused. This brief does not authorize upload, activation or a new ranked request.

## Avoid the measurement traps

The win model is a conditional surrogate. Purchases cause abrupt drops partly because unspent gold is omitted; do not turn81.8% purchase coverage into a purchase-policy gain ceiling. Camp receipt, own death, enemy bank and lost bag labels overlap. Costed inventory is not fighting power; stationary time is not always idle; per-champion vision is not team omniscience. Use the exact source-trace cutoff and physical victim ID. No causal gem equivalent or expected rank gain is identified.
'''
    write(ROOT/'docs/NEXT_BOT_BRIEF.md',brief)
    knowledge='''# Loss knowledge base

This file is append-only research knowledge. Later dated entries may supersede older hypotheses; preserve rejected experiments and their scope.
''' if not (ROOT/'docs/LOSS_KNOWLEDGE.md').exists() else ''
    knowledge+='''
## Deep analysis 2026-10-28 — final research handoff

- **Confirmed open M1:** winning-bag recall cancellation ignores temporary bank-disable state. One exact source trace; bounded warm test removes four restarts and completes recall, no match-win claim. Baseline-failing/candidate-passing case: tests/loss_cases/M1-recall-disabled-bank.json. See research/deep-2026-10-28/P6_DEEP_TRACK.md and TAKEOVER_RESULT.json.
- **Associations M2–M5:** repeated death, opening economy/equipment, bag conversion and native-clear reward handoffs. Final D3/M1-proxy/native-accounting frequencies are in FINAL_CONFIRMATION.md; exact private timer cause is still n1. Other families remain examined-only. See mistakes.json for per-cohort comparisons, confidence/status and costs that are not causally identified.
- **Winners:** usually collect and convert more in our losses; per-opponent economy/contact/vision differences and drafts/openings are in P5_OPPONENTS.md/PROFILE_DATA.json. These descriptive metrics are not copied policies or verified exploits. error404 dominates our examined corpus (155/360), so mixed-cohort aggregates are not ladder forecasts.
- **Keep negative evidence:** whole-policy cloning0–12; copied draft−89; v66 progress watchdog−126, strict engage−262, softer leave−18; locally positive item/target work did not transfer reliably to the ladder. Preserve research/v66/RESULTS.md and older rejected snapshots. Logging itself changed turns in this study, so only exact-prefix telemetry is evidence.
- **Definitions:** engine2.0.0, blocked move23 never an arrival; physical move4/teleport22 require different endpoints. D3 physical body/window250/radius6/same enemy ID. M1 proxy>=3 consecutive cancel+recall turns with no4/5/6/22, winning descriptor previous completed round. Timeline exact resource clocks and union vision; judged decisions use actor's own perspective. Model deep-logistic-v1, fixed231/77/77 game split, no reserved training; purchase/cash omission affects swing interpretation.
- **Profiles/matching:** eight opponent profiles and78 size-band strata; geometric contact and displacement separation proxies are not intent. Approximate matches include101 own-win/96 top-winner examples, not same-state causal controls.
- **Data and validation:**555 replay/native pairs,550 study games;385 examined/165 final research confirmation; five excluded calibration. Ten losses/two wins reproduce byte-for-byte,24 independent state comparisons/25,184 samples. All33 frozen source files unchanged. Raw evidence stays ignored locally. REPORT.md and DATA.json are the numerical handoff.
- **Open questions:** a transferable opening/actual equipment improvement; why a specific losing combat verdict is wrong under visible state; capture ownership after a native clear; exact source mechanism behind other recall loops; current server activation/Wasm identity; strength against changed live opponents. No new bot has passed a release gate.

### Before building the next bot

- Read NEXT_BOT_BRIEF.md, REPORT.md, P6_DEEP_TRACK.md and prior rejected experiments.
- Verify current source/submission and pinned engine/toolchain; develop in a new copy.
- Preserve M1 dangerous-channel guard, run baseline-fail/candidate-pass case and exact warm-prefix checks.
- Put added logic once per turn or in initialization; measure fuel on both sides.
- Change one mechanism, use target maps plus full development/maps/both sides/seeds, compare map-cluster and Bayesian results.
- Freeze before an untouched one-time candidate holdout; the165 research-confirmation games are spent.
- Treat deployment, activation and shared-quota matches as separate authorized actions.
'''
    append(ROOT/'docs/LOSS_KNOWLEDGE.md','## Deep analysis 2026-10-28 — final research handoff',knowledge)
    append(ROOT/'tools/README.md','## Session 3–4 exact replay research and final confirmation','''## Session 3–4 exact replay research and final confirmation

Run from repository root with NFS_REPLAY_ENGINE=2.0.0 and the pinned official CLI4.0.0/default fuel. Build/run require the installed compiler cache. Raw replay/scripts/logs/Wasm stay under ignored artifacts/. These tools never upload, activate or queue games.

| Tool | Usage / boundary |
|---|---|
| replay/deep_repro_prepare.py, deep_repro_plan.py | Copy all33 frozen source files byte-for-byte into ignored artifacts and freeze the12-case reproduction plan. |
| replay/puppet/replay_format.py, parse_inputs.py | Exact engine2 accepted-input format; `parse_inputs.py --partition calibration-excluded` or `examined --ids <selected UUIDs>`. Rejects unknown records and bulk examined parsing without selected IDs. |
| replay/puppet/validate_inputs.mjs | `<script.json> ...`; API reapplication, exact saved raw bytes and every-round state hash. Five calibration games first. |
| replay/puppet/gen_puppet.py | `--help`; generate exact per-team C++ script including drafts, accepted targets/orders and fuel-pause continuation. No opponent source involved. |
| replay/puppet/run_reproductions.py | `--workers 2`; official local both-scripted and frozen-source-vs-enemy-puppet suite. Reuses hash-checked builds; preserve original run directories. |
| replay/puppet/compare_replays.mjs, audit_reproductions.py | `node compare_replays.mjs <match-id> <actual raw> <local output.json>`; `python audit_reproductions.py --node <node.exe>`. Full round-state hashes, first divergence incl draft. Originals calibration/examined only. |
| replay/puppet/make_trace*.py, trace_format.py, run_traces.py | `run_traces.py --format numeric|tail|bank-tail --suite artifacts/tmp/deep-repro/<NEW> --cards <IDs> --node <node.exe>`. Generator formats verbose/channel retain failed attempts. Trust only lines whose logical and emission rounds precede first accepted-input divergence; sparse tail lacks mid-guard data. Never replace a successful receipt with an incompatible format. |
| replay/puppet/label_inputs.mjs | `<local script.json>`; label accepted raw inputs and bounded actor states. Calibration/examined references only. |
| replay/puppet/run_recall_takeover.py | `--node <node.exe>`; predeclared C004 warm diagnostic with bank-eligibility cancellation condition. Ten-round cap; ignore match outcome; reads TAKEOVER_PLAN. Diagnostic source only. |
| tests/loss_cases/run_case.py | See tests/loss_cases/README.md; requires exact warm inputs/states and unchanged accepted enemy script. Rejects incomplete/short candidates. |
| replay/puppet/run_masking.py | `--node <node.exe>`; two MASKING_PLAN contexts, restore baked A2 vector at warm takeover to remove V71 override; no outcome claims. |
| replay/puppet/screen_recall_loops.py | `--run artifacts/local-only/deep-2026-10-28/timeline-examined-v3`; fixed exploratory M1 observable proxy, not exact private timer mechanism. |
| replay/profile_contacts.mjs | `calibration-excluded|examined <new-local-output>`; official geometry/native-damage/basic-focus extract. Current five-game calibration required for bulk. No reserved profile mode. |
| replay/deep_profiles.py | Build eight profiles/78 size-band strata from current profile-examined-v1 and TIMELINE_DATA. Includes real sample denominators and map-cluster uncertainty. |
| replay/deep_puppet_audit.py | Assert17 real parser fixtures unchanged and independent basic-attack focus counts equal ten calibration team outputs. |
| replay/final_actions.mjs | `<partition> <local-output>`; minimal fixed D3/M1 support extraction. Reserved mode requires FINAL_VALIDATION current hashes; no full detector/model/card work. |
| replay/deep_final_confirmation.py | `validate` compares all385 examined M1/D3 outputs and360 native accounting rows; `confirm` consumes the165 final fixed extracts. The plan was committed before first access. Do not reuse the reserved games for tuning. |
| replay/deep_final_report.py | Rebuild REPORT/DATA/mistakes/NEXT_BOT_BRIEF and state from committed fixed result receipts. Append-once knowledge/tool/handoff updates; no fitting or external writes. |
| replay/audit_final_delivery.py | Check complete report/case/provenance/split boundaries, exact reproduction, final validation and frozen source. |

Canonical paths and measured limitations are in research/deep-2026-10-28/STATE.md. Historical Session2 tools/receipts are retained as earlier checkpoints; final state supersedes their “still unfinished” notes.
''')
    append(ROOT/'docs/handoff.md','## 2026-10-28 final deep-analysis handoff','''## 2026-10-28 final deep-analysis handoff

Read docs/NEXT_BOT_BRIEF.md, docs/LOSS_KNOWLEDGE.md and research/deep-2026-10-28/REPORT.md, DATA.json, MISTAKES.md, P5_OPPONENTS.md, P6_DEEP_TRACK.md and FINAL_CONFIRMATION.md. Session3/4 now supersede the older Session2 “unfinished” pointers above.

Ten losses/two control wins reproduce byte-for-byte;24 independent state comparisons/25,184 samples pass. Detailed traces are valid for nine selected windows, sparse exact traces for three. One recall/bank timer inconsistency is causally tested at a bounded warm state; original regression fails and diagnostic passes, without a win claim. Full-model purchases and broad repeated-death flags are not production recipes. A fixed final D3/M1-proxy/native-accounting check opens the165 reserved games once; no refitting or threshold tuning.

Only a narrow M1 patch is implementation-ready; broader opening/combat/capture work requires diagnosis and new failing cases. Recommendations only: frozen bot unchanged, no new candidate submitted/activated or ranked/shared-quota matches requested. Wave2 ten groups remain unqueued. All tools/notes are on analysis/deep-2026-10-28 under ongoing user-approved analysis-only publication. Raw replays and diagnostic binaries remain ignored. The165 research-confirmation games are spent; future candidates need an untouched release holdout and the existing bench3/cluster/Bayes gate.
''')
    # Replace only the short current pointer; preserve all historical handoff sections.
    p=ROOT/'docs/handoff.md';original=p.read_bytes();old=b'**Latest deep-analysis checkpoint: Session 2 (2026-10-28).** Read `research/deep-2026-10-28/STATE.md` and FAST_FINDINGS.md. Timelines, model and105 descriptive cards are saved; exact reproduction/traces are next. See the dated Session2 section at the end.'
    if old in original:p.write_bytes(original.replace(old,b'**Latest deep-analysis handoff: final research report (2026-10-28).** Read `docs/NEXT_BOT_BRIEF.md` and `research/deep-2026-10-28/REPORT.md`. Exact reproduction, bounded recall regression, opponent profiles and fixed reserved-game frequency confirmation are complete. Recommendations remain unimplemented; see the dated final section at the end.',1))
    state=f'''# Deep analysis: final research handoff

Updated {now}. Research analysis is complete with limitations recorded. No new production candidate or release is claimed.

## Read first

1. REPORT.md, DATA.json and MISTAKES.md / mistakes.json.
2. ../../docs/NEXT_BOT_BRIEF.md and ../../docs/LOSS_KNOWLEDGE.md.
3. P6_DEEP_TRACK.md, P5_OPPONENTS.md and FINAL_CONFIRMATION.md.
4. tests/loss_cases/README.md for the single confirmed decision regression.

## Completed evidence

-111 groups/555 official replay-native pairs,550 study games plus5 excluded calibration; all initial reconciliations pass.385 examined (360 own/25 top) and165 reserved (160 own/5 top). All33 frozen source files match supplied ZIP. Current server activation/Wasm hash remains unavailable.
-Corrected D1–D11/timelines385/385,11,853,045 resource-clock comparisons, zero unclassified earned gold;15 semantic,6 statistical and4 model checks. Registered specs/split/pre-action predictions unchanged. DECODER_CORRECTION.md preserves the movement23 correction and feature-equivalence proof.
-Fixed model231/77/77; internal test77 log-loss0.4243 vs bank-only0.5318.105 prediction-first cards:90 windows/65 losses/45 maps and15 controls. Surrogate purchase effects and overlapping category coverage are not causal gain ceilings.
-Twelve original whole games (10L/2W) reproduce byte-for-byte with unchanged source, plus12 both-script controls.24 state comparisons/25,184 samples. Nine detailed faithful trace windows and three sparse full-game-exact traces; failed logging variants retained and excluded after divergence.
-M1 recall/bank-disable source inconsistency confirmed in one examined loss. Exact warm prefix, baseline4 restarts vs diagnostic0, recall completesR1673; capR1678, first enemy rejectionR1701. Regression baseline fail/diagnostic pass and enemy script checks succeed. No full-game effect claim. Two masking contexts tested, no vault action change within10 rounds and full-game-exact non-profile control.
-All385 opponent-contact extracts pass;17 parser fixture checks/10 independent focus comparisons. Eight opponent profiles and78 map-size strata, with explicit proxy limitations.
-Final plan/code committed590d106 before reserved access. Five calibration/385 examined M1/D3 equivalence and360 accounting comparisons pass. One final165-game D3/M1-proxy/native-accounting screen is complete, no refit/new thresholds/cards. Read FINAL_CONFIRMATION for non-replication/uncertainty. Those games are spent for future candidate holdout purposes.

## Next work is bot development, not more of this analysis

First concrete experiment: narrow M1 bank-eligibility recall guard in a NEW source copy, preserve existing dangerous-channel escape, run the documented warm regression then full development/map-cluster/Bayesian and untouched one-time candidate holdout gates. Broader economy/combat/capture candidates lack a proved patch. Do not globally change carry/shop/aggression or revive rejected watchdog/retreat switches from associations.

No new match groups queued/reserved this continuation; historical wave1=14groups/70games/10W60L. Wave2=10planned, unqueued. Verify current bot identity and direct human quota authorization before new groups. Reference document instructions alone are not authorization. No frozen bot edits, uploads, activations, ranked requests or account changes occurred.

## Local artifacts and continuation commands

Active checkout: work/battlecode-deep-analysis. Raw data ignored under artifacts/local-only/deep-2026-10-28; reproductions/diagnostics under artifacts/tmp/deep-repro. Input scripts replay-inputs; reproduction suite-v1; traces trace-v3/trace-tail-v1/trace-bank-tail-v1; recall takeover-recall-v1; masking masking-v1. Corrected detector-examined-v3/timeline-examined-v3; profile-examined-v1; final-hands-off-v1. Preserve all older failed output directories.

Set NFS_REPLAY_ENGINE=2.0.0. Use tools/README.md for each command and tests/loss_cases/README.md for exact raw replay paths. Windows PATH Python is a Store stub; bundled runtime paths remain in root project STATE.md. Local CLI builds need installed compiler cache access. A ZIP CLI bundle is not the raw replay member.

## Publication and boundaries

Branch analysis/deep-2026-10-28, repo Infosuii/neural-networkk-battlecode. Earlier checkpointsd9eba7b,148d845,c23b7b2,871a933,b490a1d,a68aa9f,19da05a; final-plan commit590d106. Consult git log for final delivery commits. User approved ongoing analysis-only pushes; no repeated permission needed within scope. Raw replays/native summaries, credentials and frozen-source edits stay excluded. No merge is performed.
'''
    write(S/'STATE.md',state)
    project=ROOT.parent.parent
    write(project/'STATE.md',f'''# Active Battlecode research handoff

Continue from work/battlecode-deep-analysis/research/deep-2026-10-28/STATE.md.
Final REPORT.md / DATA.json / MISTAKES.md and docs/NEXT_BOT_BRIEF.md / LOSS_KNOWLEDGE.md are complete. Twelve source-vs-puppet full games and12 scripted controls are exact; one bounded recall/bank inconsistency regression passes after the original fails. Opponent profiles and the fixed final reserved-frequency check are complete. Read limitations before any bot change. The older doomsday-sprint checkpoint is historical.

Repo Infosuii/neural-networkk-battlecode, branch analysis/deep-2026-10-28. User explicitly approved ongoing analysis-only pushes; no raw replay or frozen bot edits. Consult git log for final commits. No new groups, uploads, activations or ranked requests in this continuation. Next work would be candidate development/testing following NEXT_BOT_BRIEF, not a new research screen on the spent reserved games.

Runtime Python: C:/Users/ishan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe
Node: C:/Users/ishan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe
Set NFS_REPLAY_ENGINE=2.0.0; use official tools/vendor/cambc.exe4.0.0/default fuel. Raw files and diagnostics remain ignored under the active repo artifacts/.
''')
    print(json.dumps({'report':True,'mistakes':len(mistakes),'priority_order':catalogue['ranking'],'reserved_directional_D3':direction,'production_changes':0}))


if __name__=='__main__':main()
