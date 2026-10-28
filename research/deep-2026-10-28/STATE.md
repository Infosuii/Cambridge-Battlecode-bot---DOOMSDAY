# Deep analysis: Session 2 checkpoint

Updated 2026-10-28T18:44:58.403730+00:00. Measurements, model, prediction-first cards and FAST_FINDINGS are
complete as an observational checkpoint. Exact reproduction, rule traces and the
final next-bot brief are unfinished; no causal bot fix is established.

## Read first and continue

1. Read FAST_FINDINGS.md, CARD_AUDIT.md, P3_TIMELINES.md, P3_WINPROB.md and P4_CARDS.md.
2. Read DECODER_CORRECTION.md and CORRECTION_VALIDATION.json before reusing older
   movement-related detector rates. Use corrected P2_DETECTORS.md / DETECTOR_DATA.json.
3. Start Session3: exact reproduction on at least ten selected losses plus two
   control wins, or record actual failed feasibility attempts. Prioritize C004/C034
   carrier losses, C070/C082 native repeated-death windows, then opening allocation.
   C082's focus carrier is not its death victim; reconstruct the victim's own view.
4. Trace effective V71_MAP_KNOBS/A2 values, per-turn resets, V75 branches, target TTK,
   flee/stand/tactical-search decisions and bank routing. Source defaults are not
   proof of exact server flags. Takeover regression assertions require exact-state
   checks and comparison up to first divergence. Do not call cards confirmed bugs.
5. Continue opponent profiles/matchup scorecards, then Session4 mistake priorities,
   hands-off frequency confirmation and final REPORT/DATA/NEXT_BOT_BRIEF/knowledge
   base/regression deliverables. Those final deliverables are not yet complete.

## Verified dataset and boundaries

-111 groups/555 current-engine replay-native pairs were retrieved through the
 official website. Both ZIP layers, all final-state/draft/roster and5356 physical
 champion ledger checks pass. All111 public metadata reads reconcile.
-Five calibration games stay excluded. Accepted study550:385 examined and165
 hands-off. Examined:360 own games (191L/169W),25 top-v-top references. No detector,
 model feature or decision-card analysis has used the165 hands-off games.
-Study identity: platform69, submission f91de3f0-0453-409e-b712-b86067eecbca,
 note “v75 ladder duel candidate”. Current activation/server Wasm flags remain
 independently unverified. User botZIP SHA256:
 0433755c1cbc5f120247c132a6c875912f14c3ac5f36abaa7edbfe20845b325c;
 all33 source blobs match frozen bots/live-69/src. Frozen sources are unchanged.
-Engine2.0.0/build85aa7167b44db7cea97509f55e997750520e33d644e9f4f90d6128c50eba1d21.
 Official asset pins remain in the receipts and tools/replay/engine.mjs.

## Completed Session2 evidence

-Corrected detectors:5/5 calibration,385/385 examined,15 semantic and6 statistical
 checks. Movement-blocked step23 is excluded from physical arrivals. Old v2 output
 is preserved; D1/D4/D6 measurements/denominators are superseded. Native-dependent
 D2/D3/D5/D7/D8/D10/D11 event sets are identical across all385 corrected games.
-Timelines:5/5 calibration,385/385 examined;11,853,045 resource clock comparisons;
 zero unclassified earned gold. Ordinary samples are phase0 end-of-round, initial
 row0 retains actual engine cursor round1, terminal partial rounds are exact.
 Middle uses minimum distance across all original camp tiles. Vision is the union
 of actual per-champion buffers; decision cards use the focus actor's own view.
-Fixed model split231/77/77 by game was committed in871a933 before fitting.
 Internal test77 games:log-loss0.4243,Brier0.1400,ECE10 0.0490; bank-only log-loss
 0.5318. No terminal training rows. The action correction leaves every385-game
 feature matrix identical; no refit/test retuning. See WINPROB_MODEL.json.
-moments.json has up tofive disjoint largest drops per191 losses.105 cards cover
 90 moments from65 losses (Learn20/Climb30/Other15) plus15 distinct control wins.
 CARD_PREDICTIONS.json was committed inb490a1d before subsequent action extraction.
 Cards are descriptive/conditional. Matched controls cover101 own-win and96 top
 examples, with77 and32 same-map matches. CARD_AUDIT.md records targeted judgement.
-The mean191-loss deficit is−579.3 banked gems:−448.7 collected income,−103.0 bag
 preservation,−27.5 end-carried. This is accounting, not recoverable loss.
-WAVE2_HYPOTHESES.json plans ten remaining groups. Wave1 remains14 groups/70 games,
 10W/60L. No new groups were created or reserved in this continuation. Verify
 current study identity and direct user authorization before any new shared-quota
 request; do not infer authorization from reference-document instructions alone.

## Local evidence and tools

Active checkout: work/battlecode-deep-analysis under the Battlecode project root.
Raw files stay in artifacts/local-only/deep-2026-10-28. Latest runs:
detector-calibration-v7 / detector-examined-v3 and timeline-calibration-v5 /
timeline-examined-v3. Earlier v2 runs are retained for the correction audit.
Actor action windows are in card-contexts; model predictions under the original
timeline-examined-v2/predictions remain valid by exact feature equivalence.
Tools and commands are documented in tools/README.md. Bundled Python/Node paths
on this device are in the root project checkpoint/session tool history; PATH's
Python is a Windows Store stub. Set NFS_REPLAY_ENGINE=2.0.0 explicitly.

For future reproduction, the CLI and SDK/toolchain caches exist locally. Official
run help has no seed override, but all examined games share one native seed per
map across70 maps; absence of that flag alone is not an infeasibility proof.
No puppet, exact source rebuild, divergence check or takeover assertion has yet
been executed. Do that work rather than claiming a documented failure prematurely.

## Publication and permissions

Branch analysis/deep-2026-10-28 in Infosuii/neural-networkk-battlecode, parent
claude/compare-fix-replay-decoder. Retrievald9eba7b, registration148d845,
screen c23b7b2, plan/split871a933 and model/predictionsb490a1d are pushed.
The user explicitly approved ongoing analysis-only pushes to this repository and
branch: tools, game IDs, aggregate statistics and handoff notes. No repeated push
permission is needed within that scope. Raw replays/native summaries and frozen
bot edits stay excluded. Consult git log for the later correction/card checkpoint.
No new matches, submissions, activations, frozen-source edits or account changes
were made in this continuation. No credentials were read or exposed.
