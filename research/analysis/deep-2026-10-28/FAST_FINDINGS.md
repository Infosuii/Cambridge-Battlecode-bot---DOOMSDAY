# Fast findings: Session 2

**Measured accounting and predictive association. No causal bot fix is established.**
Study platform69 is frozen; the server build and current activation are not newly
verified. All555 replay/native pairs reconcile. The examined set is385 games:
360 DOOMSDAY games (191 losses,169 wins) and25 top-v-top references. Five calibration
games are separate;165 hands-off games have not been analysed.

## Where the race is lost

In191 losses, the mean banked margin is−579.3 gems. The exact additive identity
allocates−448.7 to collected-income margin,−103.0 to lost-bag preservation margin,
and−27.5 to end-of-game carried margin. These are77.5%,17.8% and4.7% of that mean
deficit. They are accounting shares, not recoverable improvement: killing a carrier
can both remove its bag and add to the other team's collected income.

Direct camp-receipt income differs by−358.2 gems/game in those191 losses. Our pooled
banked/collected conversion is63.1%, versus88.4% for the opponents (same191 games).
In83 Climb losses, the mean final margin is−512.5:−382.0 income,−81.6 loss
preservation,−48.9 carried. Banking alone cannot explain the full observed deficit.
See P3_TIMELINES.md and TIMELINE_DATA.json for paired rows and coverage.

## Openings

AtR100, inventory purchase cost is lower by86.7 gold on average in191 losses,
versus higher by90.5 in169 wins. In83 Climb losses, the R100 gap is−91.8, with
map-cluster95% [−121.0,−61.2] and opponent-cluster95% [−124.7,−78.6]. AtR250 the
Climb loss gap is−193.7 (n83). These are paired same-game descriptors, unadjusted
for draft and physical roster. Cost is not combat power. Actual native draft
picks, physical rosters, first three observed camp targets throughR250, subsequent
team gem receipts and first purchases are recorded separately.

## Detector candidates

- **Repeated deaths (D3):**129/191 losses versus74/169 wins. Per-death rate is
  722/2337 (30.9%) versus188/1028 (18.3%). Loss-minus-win difference12.6pp;
  map-cluster95% [7.2,18.3] and opponent-cluster95% [3.8,16.9]. It also appears
  in Climb (83 losses,119 wins; six observed opponents). This is the strongest
  detector association, not evidence for reviving a rejected death-watchdog fix.
- **Large-bag deaths / visible threat:**cards C004 (736-gem carrier on02guardians)
  and C034 (343-gem carrier on00vault) merit exact rule traces. Both focus
  champions saw threats and subsequently died; neither observation proves a guard
  violation. The frozen source defaults disable V75_BAG; V75_LONE has a one-turn-kill
  exception and can coexist with attacks while fleeing.
- **Capture handoff:**enemy gem reward after our native last-clear is a Climb review
  candidate, but its opponent-cluster interval crosses zero. Native last-clear
  ownership is not damage-majority ownership; gold-only receipts have other coverage.
- D1 stationary flags are common in both outcomes; D10 high gold is more frequent
  in wins. The D11 unseen-killer gap weakens after per-death exposure normalization.
  None supports a blanket inactivity, shopping or warding fix.

The official step-label audit corrected an implementation error:23 means
“Movement blocked,” not an arrival. Thresholds remain preregistered. Both corrected
extractors pass five calibration and385 examined games. CORRECTION_VALIDATION.json
proves all385 model feature matrices and native-dependent detector event sets are
unchanged. The corrected P2_DETECTORS.md supersedes affected D1/D4/D6 rates.

## Moment categories and their limits

The calibrated model was trained/calibrated/tested on231/77/77 disjoint games.
In77 internal test games, log-loss is0.4243, Brier0.1400 and10-bin ECE0.0490;
bank-only log-loss is0.5318. The model is weaker atR0–100 (log-loss0.6581,n77),
shares maps/opponents between folds, and omits unspent gold under its registered
feature plan. Test data were not used to tune the correction or refit the model.

105 prediction-first cards cover90 moments from65 distinct losses and15 control
wins. Expectations were committed in b490a1d before subsequent action extraction.
Overlapping labels on the90 loss moments have these selection-weighted shares:

| Event label | Moments /90 | Share of selected model drop |
|---|---:|---:|
| Opponent purchase |79|81.8%|
| Opponent camp receipt |63|70.5%|
| Opponent bank |36|44.0%|
| Our death |23|28.2%|
| Our bag loss≥40 |12|17.1%|

These are **surrogate review ceilings, not avoidable loss or win-rate ceilings**.
They overlap. Purchases dominate partly because inventory cost is a model feature
while cash is not. A “buy sooner” policy does not follow. D3 appears in only2/90
selected windows (1.9% of selected drop), despite its strong whole-game association:
this selection emphasizes sharp changes, not cumulative repeated-death harm.

Nearest-state controls are available for101/105 cards from our wins (77 same-map)
and96/105 from top winners (32 same-map). These use67 and23 distinct games,
respectively. A fixed-distance caliper leaves unmatched cases, including the extreme
736-gem carrier. Controls select winners and retain draft/opponent/memory confounding.
See P4_CARDS.md, cards/, error_analysis.csv and MATCHED_CONTROLS.json.

## Next evidence gate and planned probes

WAVE2_HYPOTHESES.json records diagnostic questions and decision rules for the ten
remaining groups. No new group has been created or reserved during Session2.
Verify the active submission and study identity before executing any future wave;
do not mix another bot into the frozen69 study. These would test persistence and
context, not the causal value of an unimplemented fix.

Session3 should first reproduce at least ten selected losses plus two control wins,
or document actual reproducibility failures. Trace effective V71_MAP_KNOBS/A2 values,
per-turn resets, V75 checks, TTK exception and flee/stand/tactical-search branches.
Prioritize C004/C034 carrier losses and repeated-death cases C070/C082, then inspect
paired opening allocation. Exact takeover assertions and failed-live regression
cases require that work. Do not label the automated cards as confirmed mistakes.
