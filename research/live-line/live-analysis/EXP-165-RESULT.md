# EXP-165 result — current-engine loss diagnosis and confirmation

MEASURED: the fresh48-hour inventory contains5195 matches and1106 distinct losses above the collector's2000rating threshold. The separate [frozen current-engine cohort](LIVE109_DISCOVERY_SPLIT.json) has359 losses to the current above-us set/three requested rivals since00:31GMT5Nov, split by whole-group SHA into223discovery/136confirmation, plus18hash-selected win controls. All377 native summaries verify engine3 build96ce858f and every terminal champion metric matches its native total. All125 selected representative replays (58discovery,56confirmation,11controls) reproduce native death counts. Exact source identity is inferred from the v108/v109 time interval, not exposed by these listings. No causal or champion claim follows from these samples.

The initial split incorrectly inferred132 ranked/unranked labels from groupId; [the separate audit](LIVE109_DISCOVERY_METADATA_AUDIT.json) uses saved explicit kind fields. Frozen membership/groups remain unchanged and these labels were not used by the metrics. [Frozen native/replay patterns and group-weighted recount](LIVE109_DISCOVERY_PATTERN_REPORT.json) preserve every result, including weak hypotheses.

| Finding | Discovery losses | Confirmation losses | Win controls |
|---|---:|---:|---:|
| R800 banked+held gem deficit, among games still running |129/171|84/106|3/18|
| R300 inferred realized camp gold below rival |38/58|40/56|4/11|
| More no-PvP-basic-or-cast deaths throughR600 than rival |25/58|32/56|1/11|
| Fewer wards throughR300 |169/223|103/136|17/18|
| First deposit later, among both depositing |112/216|68/128|8/15|

R300 median team earned gold is968versus1227 in discovery and979.5versus1200.5 in confirmation. Representative replay median inferred capture gold is712.5versus900 and860.5versus1030; win controls1055versus890. No-hit deaths are76/310 own versus31/184 rival in discovery and84/321 versus27/169 in confirmation; controls5/27versus11/49. These are preceding-five-alive-round action windows, not proof that no damage was ever returned.

The larger midgame gem deficit, lower early capture income and unproductive deaths recur in confirmation. Ward count alone, earlier first banking, early grouping and clear-to-capture delays do not cleanly separate losses from this small set of wins. The income-without-any-deathsR150 pattern also occurs in3/18wins versus30/223 and20/136losses; do not oversell it as a predictor. Do not resurrect rejected generic pack play or early banking from these descriptive differences.

[Error accounting](LIVE109_DISCOVERY_ERROR_TABLE.json) reports frequency, conditional gap and their product in gold/gems/deaths. For example the observed R800 gem deficit averages249.2 among129 affected discovery cases, corresponding187.96 per eligible case; confirmation286.83 and227.30. These overlapping observed deficits are not an attributable improvement ceiling or win-rate estimate.

[EXP-171](EXP-171-RESULT.md) traces one same-champion own-view opening per named rival. Two show rival Marcella with1700/2500maxHP versus our1200. Current source health purchases are later, but private historical targets and source paths remain unresolved. Replicate a local controlled decision before altering purchase timing. Early Greed and late Skirmish cards are deprioritized: discovery buys only20Greed and25Collectors shards throughR300 across223 games, so those planned milestones rarely address the opening gap. Prism is not justified by its buff alone. Native target-versus-executor midgame attribution remains coordinated with JOHNDOE/CLAUDE.

The new balance remains fully accounted for in runtime metadata and all tests use the new engine. The current priority is actual current-source suspension attribution (EXP-173), after three component/runtime screens were rejected. Old v92 subsystem ablations remain historical engine2 evidence; no new learner or long training run was started, no source from another worker was edited, no holdout opened and no platform action was taken.
