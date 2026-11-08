# Agentic Battlecode improvement: evidence and delivery

Research from 5–8 November 2026, Cambridge Battlecode engine 3.0.0, normal fuel.
This branch preserves successes, failed confirmations, repairs, teammate evidence,
training checkpoints, source snapshots and exact local evaluation records.

**Delivery status: v112 active on DOOMSDAY. Experimental release; a strength upgrade and ELO gain are unproven.**

The selected corrected bot scored 166/328 against v111 across 164 final maps,
with +1.26 reference percentage points. Its matched live unranked check scored
4/5 versus 3/5 for v111, with zero faults. That small check is not ELO proof.
The full experiment and parent comparison played 151,272 local games.

## Read first

- `followups/contested-capture-20261108/`: 5,886 further local games, a verified
  contested-objective stall, repaired handoff, matched on/off confirmation and
  defensive regressions. This repair was not promoted; v112 remains active.
- `findings/strategy-review.md`: why the experimental approach changed and what
  the measurements support.
- `findings/final-report.md`: complete selection rationale, four-candidate
  comparison and limits on the strength claim.
- `findings/ladder-review-20261108.json`: current replay-selection checks and
  accumulated score accounting, with policy-provenance limitations.
- `findings/historical-notes/`: readable session notes. These are dated evidence;
  old operational instructions and status paragraphs are not current authority.
- `index/experiments.json`: complete durable experiment records, including
  negative results and follow-up classifications.
- `index/artifacts.json`: each exported original path, byte count and SHA-256,
  plus its content-addressed archive location and explicit local-only artifacts.
- `release/`: the selected source ZIP, exact tested Wasm, hashes, selection
  rationale and confirmed submission/activation and matched-game receipts.
- `tools/`: archive restoration, export, packaging and guarded deployment tools.

## Reproduce and inspect

`archives/objects-*.zip` contain deduplicated exact file bytes. Each ZIP is kept
below GitHub's per-file limit; the index maps original paths to objects. They
are data archives, not executable installers. From the repository root:

```powershell
python research/agentic-improvement-20261107/tools/restore_findings.py `
  research/agentic-improvement-20261107 C:\battlecode-research --verify-only
python research/agentic-improvement-20261107/tools/restore_findings.py `
  research/agentic-improvement-20261107 C:\battlecode-research
```

The restored tree contains the experiment scripts, candidate sources, candidate
recipes, map bytes, SDK source, checkpoint weights, aggregate result tables,
frozen manifests and audit receipts. Runtime/compiler executables and installed
Python dependencies are excluded; use the pinned identities and requirements
in the restored tree. Historical receipt paths point to the original cache;
rebase paths deliberately when reproducing in a new directory. The old stop
markers and action database are not a deployment authorization.

Raw per-game captures, complete local replay caches, full decoded round streams,
credentials and session state remain local. The compact incident findings,
selected comparisons, full aggregate score rows and audit hash receipts are
included. The index explicitly identifies excluded classes and selected raw
artifact hashes; it is not a claim to have uploaded every replay.

## Reading the strength claims

Development, selection, fresh testing and published-map replication are labelled
separately. Historically reused published maps are never called team-unseen.
Generated maps are a synthetic stress distribution, not a measured sample of
the ladder's map or opponent frequencies. Match-level win counts share maps;
the final uncertainty checks resample map clusters.

Mechanic correctness, a changed native trace, lower fuel usage and competitive
strength are separate observations. A failed first strength gate does not erase
a correct feature. Learned weights are alternative policies, not additive code
patches. The ambitious +8 percentage point / 60% direct-score target must be
reported separately from the pragmatic choice of a delivery bot.
