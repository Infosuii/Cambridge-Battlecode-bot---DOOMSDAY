# Fourth Discovery confirmation criteria

Keep the seven [Discovery 2 predicates](../discovery2/CONFIRMATION.md). Preserve the five-of-eight directional threshold. The selected groups and split are frozen before the replay profiles.

The following additional checks distinguish a failure to clear from a failure to collect an already cleared reward. Use engine 2.0.0 replay snapshots through round 300 and report all four even if they fail.

1. Winner has more gold inferred from completed camp captures with positive configured gold reward.
2. DOOMSDAY has a longer median gap from observed group death to capture among completed positive-gold captures with at least one attributed basic attack and all attributed attackers on the capturing team. Require at least two eligible captures for each team in a game. Report how many games meet that support rule.
3. DOOMSDAY has more interruptions of single-team occupation of a cleared positive-gold group with an enemy within six tiles of the prior occupants.
4. Winner has more inferred captures with at least one attributed basic attack and every attributed attacker on the other team. Report the observed gold from those captures and the number of captures with no attacker attribution.

Use the unchanged native capture-pressure profiler. It infers collection from gold and snapshots. It misses zero-gold captures, instant clears that never show a damaged live group, and attacks it cannot attribute. Its interruption count describes occupation changes, with no engine capture-progress or causality claim. The historical match API does not identify the actual submissions. Report earlier deposits and group counts descriptively. Confirmation games cannot set bot thresholds.
