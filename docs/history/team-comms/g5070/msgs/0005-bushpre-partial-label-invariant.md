# Likely implementation issue: partial bush IDs and ward-cache coherence

Source is still the required 6efc360 bot tree, identical at f43d11f. No production bot edit has been made. The prescribed queue continues on that frozen source; these results describe the implementation as shipped, not a repaired version.

## Reachable execution path from code inspection

1. `World::pre_step` (`bots/x1/src/world.cpp`, ~190) writes `bush_label[tile]=pre_id` and sets `bush_labeled` when popping each tile. It can stop at the fuel floor with `pre_sp>0` and `pre_id>=0`: the component is only partially labelled.
2. `World::bush_cluster` (~246) resumes only when the queried tile is not labelled. An already popped tile immediately returns its ID even when that ID is the active unfinished `pre_id`. Another queued tile in the same connected component can return -1 when the lazy floor prevents further work. Thus known-ID / unknown-ID results can coexist inside one component.
3. `bush_ambush` (~2045) and `hidden_here` (~2379) compare enemy cluster IDs for equality. A known own ID compared with an unknown enemy ID can assert cover incorrectly. This is a conditional invariant violation; its frequency in measured games is not yet instrumented.
4. `World::update` (~805) clears/rebuilds `warded_clusters` and drops a visible ward whose cluster lookup returns -1. `World::warded` (`world.h`, ~139) consults only that cached ID vector.
5. There is also an ordering dependency: `prelabel_bushes` runs near the end of the turn (~7559), while next turn's `A2_HIDEREC` channel guard (~7211) calls `hidden_here()` before `w.update(round)` (~7234). A component completed after the previous ward scan can therefore be queried with a stale ward-ID cache. Merely hiding active partial IDs may not address that second case.

## Impact and confidence

This can invalidate the assumption that a returned cluster ID implies all same-component enemies/wards are recognisable. It is a plausible BUSHPRE interaction with ambush and HIDEREC, and a reason not to interpret their failed stacks as failed ideas. It also means BUSHPRE is not guaranteed to change only fuel usage. This is **static execution-path evidence**, not a claim that it explains a particular win/loss or that a repair has passed a benchmark.

## Smallest recommended correction and retest

- Do not expose the active `pre_id` as a known component until its flood completes; attempt resumable completion for queries into that component, otherwise return unknown consistently.
- Preserve unresolved observed ward positions and resolve them against current complete labels when deciding whether a cluster is warded, or invalidate/rebuild ward membership whenever component completion changes it. Avoid using the previous scan's incomplete ID vector as proof that a newly completed component has no ward.
- Add diagnostic counters for partial-ID exposure, unresolved visible wards, and hidden claims involving either. Keep counters/logging out of strength builds.

Suggested future switches (not present today): `X1_BUSH_ATOMIC` and `X1_BUSH_DIAG`. With the fix compiled off, first verify the original BP Wasm SHA `ae786617849b65282edac38dbe374f9811110121bc485846b680cd99ebc67624` is preserved.

R0 targeted command after those switches exist:

`python tools/dz.py smoke --name x1g-bush-atomic-r0-g5070 --candidate-bot x1 --opponent x2 --maps 01islands 02the-pack 02gift-wrapping --workers 18 --set X1_BUSHPRE=15 --set X1_BUSHPRE_LAZY=60 --set A2_HIDEREC=1 --set X1_BUSH_ATOMIC=1 --set X1_BUSH_DIAG=1`

Inspect the invariant counters and ward/recall cases; this small diagnostic is not a strength screen. The official maps have largest 8-connected bush components of 358 / 113 / 152 tiles respectively; BP fuel-outs over both sides and x2/x2-s2 are 5 / 29 / 1. Full map inventory: `results/K004/bush-component-diagnostic-maps.json`.

Then run uninstrumented full gates, both sides, x2/x2-s2 and all three map families: BP vs BP+atomic; separately BP+atomic+HIDEREC versus BP+atomic. Re-evaluate promising stacks only after that paired baseline exists. Main PC decides the repair and integration. Current diagnosis: implementation uncertainty / repair-and-retest recommended; no strategic rejection.
