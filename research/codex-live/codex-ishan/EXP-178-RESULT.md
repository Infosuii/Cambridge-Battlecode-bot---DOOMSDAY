# EXP-178 result — current111 fails the original safety baseline

MEASURED: [172-cell current111 baseline](LIVE111_POOL_SAFETY.json),86frozen official maps/both sides, engine3/CLI5/real100k/no logs, exact uploaded111 source72e9a198/local0896a189 against frozenv92/platform80/local5704d7ba. The reused v92 mirror rows have identical map and engine seeds.

Native suspensions1582versus203, round1 62versus28,146per-cell increases, zero faults/codes. Safety fails. Fixed-release score95/172versus86/172, +5.233pp with map-cluster95%[-2.907,+13.372], is context only and not a noisy strength or ladder claim. No individual pool failure is used in mechanism design.

The live platform remains111pinned; this chat does not activate an older version without the lock/release protocol. Existing111 CLFS9 enables slow-block and warm/rebuild guards but disables scoring-margin and slower-tail-memory parts. EXP179 separately tests those existing parts with current weights fixed, using development maps/fresh paired noise. No holdout or ladder operation.
