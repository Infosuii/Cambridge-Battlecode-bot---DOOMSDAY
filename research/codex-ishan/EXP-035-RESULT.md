# EXP-035 combined release result

The two exact releases reproduce 36854b76366f762f65853b3b66819e9c2d4742982ef7fcd69294931daf977e75. Turning the switches off reproduces v92. The no-logging native development check reduced suspensions from 45 to one versus original PG across 64 matched cells, with zero faults and diagnostic codes. [Exact development rows](PG_BUDGET_EXACT_DEV.json)

Across 172 matched official-pool cells the combined release won 91 versus 86 for v92, b/c 38/33. Fuel suspensions fell from 160 to 71. Round-one suspensions fell from 28 to 16, without an individual round-one increase. There were zero faults and diagnostic codes. Eleven full-game cells increased, including eight previously clean. The original L0 safety gate therefore rejects it. L1, L2 and ladder arms stayed unopened. [Safety rows](PG-BUDGET_POOL_SAFETY.json)

Use a larger fixed development cohort to find any further budget violation. The official-pool cell identities and outcomes are not inputs to that work.
