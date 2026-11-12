# EXP-031 release result

The two releases reproduce c092fa438affdab4598aa3373799ac77cafde59382d9e0bcaee4cfde505687e6, and all switches off reproduce v92. The [180-game diagnostic](FIELD_ORDER_PROBE.json) found repeated deferred work on 15 development maps and measured a maximum order build cost of 20,844 fuel.

On the [172 official pool cells](FIELD-ORDER_POOL_SAFETY.json), round-one suspensions fell from 28 to zero. Both arms had 160 total suspensions, zero faults and zero diagnostic codes. Fifteen cells increased, including six previously clean cells. Wins were 80 versus 86, with b/c 7/13. The round-one change is real, but the full release fails the original fuel gate. Stop before L1/L2, live pairing or holdouts.
