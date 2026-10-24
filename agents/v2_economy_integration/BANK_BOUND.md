# Bank resource bound amendment

Root explicitly accepted cap64 plus whole-decision refusal when a destination remains unresolved. The existing
action schema is unchanged because no potentially reachable destination is silently removed. Expansion cap64
limits the host search before it starts, rather than checking fuel after an uncapped search.

`nnp::bank_candidate_fuel(const Bot&)` reads cached map metadata, container counts and the already refreshed Bot
position only. It performs no live SDK feature query or candidate traversal. The return type is `uint64_t`;
`UINT64_MAX` means unsupported metadata/radius and must be rejected before adding reserves. The current formula:

```
field_cold = chunks * (64 + 24) + 2*field_bytes + 4*board_bytes + 3000
candidate = field_cold + 12000 + altars*(1200 + (2*submit_radius+1)^2*96) + enemies*250
```

For a matching owner/round/dimensions/Bot-position field cache, only `field_cold` becomes0. A builder rechecks
the SDK self position against that refreshed Bot snapshot and refuses before searching on disagreement.
The travel executor reuses that admitted cache or refuses; it never starts an unadmitted cold field search.

The field estimate uses the legacy measured `(levels+16)*chunks` model with24 instead of16 and explicit extra
buffer and fixed overhead. Per-altar/candidate margins remain provisional conservative allowances. The lead must
measure the capped real bank path and configure head-specific admission before claiming calibration or safe
full gameplay. This change alone does not establish80% ownership or coverage on long maze maps.

The synthetic SDK now models expansion counts and the cap. Its serpentine32x32 corridor extends beyond64steps.
With a far unresolved altar, builder returns false/K0; with all altar rings already reached it succeeds even
though unused corridor tiles reach the cap. Existing disconnected-map coverage verifies exhaustion before64
accepts proven-unreachable omissions. No new engine matches or jobs were started by this worker.
