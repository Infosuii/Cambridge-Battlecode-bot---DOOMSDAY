# EXP-016 result

MEASURED. The charged v92 diagnostic `73adac9670ec42051209caee412c9f757b595b3c65a611bc3f0fb19e73840b08` finished 16 games on four dev maps, both sides versus v92 and x3inv. The [replay-log recount](WARD_COOLDOWN_PROBE.json) had zero reactive calls reaching the late positive-cooldown check with a nonempty candidate list. The engine reports a ten-round ward cooldown in the earlier [SDK probe](EXP-005.md). These games do not establish how often the costly bush code suspends before the check or how often this would happen on the ladder.

Verdict: the preregistered opportunity check failed. No candidate, release gate or ladder action.
