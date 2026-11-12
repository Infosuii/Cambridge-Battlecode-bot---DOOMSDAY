# EXP-116 bounded greedy fallback result

Two clean releases matched at `bcd627768482a0bc2cc73fb5e71ad39cb351b55dde53d8480555f29b563372ac`. With switches off the source reproduced v92. The native SDK selected the same nearest tile in all 384 checks, including 128 compacted cases across 16 maps and both sides. [Builds](CPG_GREEDY_NEAR_BUILDS.json), [SDK check](CPG_GREEDY_NEAR_PROOF.json).

The 160 ordinary-budget development pairs reduced suspensions from six to zero and reproduced Vendetta's R1077 observation and original action prefix. The separate 160 reduced-budget diagnostic pairs had 61 suspensions in each arm. No pair increased at either budget. Both arms had identical drafts and no faults or diagnostic codes. [Paired native results](CPG_GREEDY_NEAR_EXACT.json).

On all 86 official maps in both sides, the unsubmitted candidate won 101/172 versus 86/172 for v92. Candidate-only wins were 47 and baseline-only wins were 32. Total suspensions fell from 160 to 31, including round-one suspensions from 28 to 12. Both teams had zero faults and diagnostic codes. Two previously clean games still suspended. L0 failed and L1, L2 and ladder testing did not start. [Pool results](CPG-GREEDY-NEAR_POOL_SAFETY.json).
