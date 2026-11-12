# EXP-174 result — diagnostic controls caught two instrumentation problems

The first preparation stopped at an ambiguous two-occurrence anchor; no games ran. The r2 disabled inline-call diagnostic compiled to d70d1941e133b2a03541153b12434866d375c84dec0ee0d021784a52c356e647, size600346, instead of the frozen11801 baselinec1a22367, size600357. Call-site preprocessing restored exactc1a22367 in r3 before diagnostic matches.

[R3 fine records](LIVE109_RUNTIME_FINE.json) show a real warm-feature crossing, but flushing every record with printf adds material charged work. Other cases can have a same-round native event without the intended in-buffer source crossing. Those cases do not justify source attribution. Artifacts stay local under engine3-live109-runtime-fine, -r2 and-r3, with no recorded files overwritten. EXP-175 repairs the measurement workflow and repeats the original five actor-round controls.
