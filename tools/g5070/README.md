# g5070 verification and archived prework

These files do not participate in any bot build. No `bots/`, SDK or engine source is changed by this contribution.

## Exact pool-record comparison

`compare_results.py` validates 172 unique map/side records, checks aggregate wins against individual outcomes, compares gameplay/provenance fields, and computes paired gained/lost games and the unadjusted sign statistic. Its JSON keeps gameplay equality separate from binary equality. A matching win count cannot hide different banked totals or duplicate identities.

```bash
"$PY" tools/g5070/compare_results.py reference.json candidate.json --output comparison.json
```

The g5070 campaign's K011 reference matched172/172 records,108/172 wins,0 faults and186 fuel-outs. PC message0035 explicitly accepted native Linux x3 hash `bf3f65d009c0` in place of the Windows `5704d7ba41ac` reference. Future paired comparisons use the machine's own exact baseline, not cross-platform binary equality. Reports and evidence live only under `g5070/` on `comms/x1`.

## Archived I-70-02 arrival prototype

`prototype/g70_arrival.h` is isolated prework created before PC message0036 cancelled K013 on g5070. It is **not integrated in a bot**, has no match-strength evidence and is not a merge candidate. It is retained to avoid losing the handoff. The `X1_G70_COORD` switch defaults to0, and the header contributes no definitions when disabled.

The helper counts basic attacks during at most two turns under explicit path and action-availability assumptions. Ranged movement consumes that turn's basic attack; melee may attack after its final approach step. Unknown paths and channeling receive no support credit. It does not invent spells/resets/dashes or predict an escaping target's future position. A future caller must verify those assumptions before treating the budget as usable support.

Fifteen native host correctness cases passed before cancellation. To reproduce them:

```bash
g++ -std=c++20 -O2 -Wall -Wextra -Werror -DX1_G70_COORD=1 \
  tools/g5070/prototype/arrival_test.cpp -o /tmp/g5070-arrival-test
/tmp/g5070-arrival-test
```

Remaining work belongs to the team queue, not this archived prototype: integrate behind a default-off switch only when reassigned; verify the Linux default build hash; establish action/path/target-motion observability; profile real fuel; then screen on x3mf and complete required gates. The current bot uses8 shared team bytes, so a static per-guest cache must not be advertised as a shared team-turn cache.
