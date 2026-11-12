# EXP-173 result — five matched current-source phase crossings

MEASURED: [12-game charged stage profile](LIVE109_RUNTIME_PROFILE.json), the first frozen dev map by SHA in eachC4/C5/C7, both sides, x3inv/public-khiri, paired11801 noise and engine3/100k. Off profiler build exactly reproduces the recordedc1a22367 baseline. Diagnostic7d006163 has113 native suspensions versus87 in the corresponding frozen uninstrumented cells; instrumentation is a material perturbation, and these are not candidate strength/safety results.

Raw phase logs show45 crossings from lazy-score entry to exit,43 from its exit to the end of play,7 through warm-up,2 through periodic rebuild, plus a few late transitions. A phase log records the first detected round change of a call and can cover several native fuel events; do not equate the two counts.

[Matched own views/actions](LIVE109_RUNTIME_MATCHED_TURNS.json) verify all five selected earliest shared actor-round cases:

| Stage | Development cell | Actor/round |
|---|---|---|
|3to4, lazy scoring|pf_pool_77035,A,public-khiri|VendettaR46|
|4to5, following farm execution|pf_pool_77038,A,public-khiri|IssacR66|
|61to62, one-time warm features/embeddings|pf_pool_77035,A,public-khiri|CassiR17|
|63to6, spare slow-block work|pf_pool_77038,A,x3inv|HeartR179|
|6to7, tail after turn work|pf_pool_77038,A,x3inv|HeartR285|

Each has the same native actor/round crossing, the same observed own input after removing the timeline index, the same action prefix before fuel exhaustion, and an explicit replay fuel step. Four trace files are byte-identical to baseline; HeartR285 differs in timeline index only. These establish observed matches, not private whole-history identity.

The tail label alone cannot establish a costly `clna_turn_end`: exact deployed source immediately returns there under JD_NATIVE_ACTOR1/JD_NATIVE_LOG0, while the profiler adds its own tail calls. Treat it as a tail-reserve question. EXP-174 buffers narrower charged method markers and repeats the matches. No production code, weights, draft or CLFS/route setting changed; no platform action.
