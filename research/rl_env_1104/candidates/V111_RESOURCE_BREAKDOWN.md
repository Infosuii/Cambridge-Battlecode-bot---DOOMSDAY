# v111 loss resource breakdown (JOHNDOE #170), from e3-v111-v109-base-02

**Source.** Official gem events of the 180 base-02 games; tool `tools/rl_env_1104/strategy/resource_breakdown.py`.

**Accounting.** banked = camp + fight_in - fight_out - camp_loss - held, which is exact and asserted per game. The final margin therefore splits exactly into four components:
- **production:** camp gems, ours - theirs.
- **fights:** net transfers.
- **camp losses.**
- **conversion:** their held minus our held at the end.

## v111 losses (38 games): production carries the deficit

| | margin | production | fights | camp losses | conversion | clears ours / theirs |
|---|---|---|---|---|---|---|
| v111 losses (38) | -468 | **-345** | -129 | -8 | +15 | 52 / 67 |
| v109 losses (41) | -443 | -266 | -155 | +3 | -26 | 60 / 67 |
| v111 losses vs nnfinal (14) | -543 | -424 | -116 | . | +2 | 60 / 61 |
| v111 losses vs v86h (12) | -415 | -346 | -70 | . | +3 | 43 / 59 |
| v111 losses vs x3inv (12) | -432 | -250 | -204 | . | +40 | 50 / 82 |

- **Main cause:** production is the most negative component in 32 of the 38 losses (fights in 4, conversion in 2).
- **Carry conversion is not the general cause.** In only 4 of 38 losses does v111 finish holding at least the margin. The recall-loop case (#171) is real but rare here.
- **vs nnfinal, a value deficit:** v111 clears as many camps as nnfinal (60 vs 61) but collects 424 fewer gems.
- **vs v86h and x3inv, a clear-rate deficit:** 43 vs 59 and 50 vs 82 clears.
- **vs x3inv, fights also matter** (-204).

## Matched cells, v111 - v109 on the same map/side/opponent

| cells | n | margin | production | fights | conversion | our clears |
|---|---|---|---|---|---|---|
| all | 90 | 0 | +1 | +25 | -14 | -1.9 |
| v111 lost, v109 won | 17 | -1011 | -804 | -172 | -9 | -14 |
| v111 won, v109 lost | 20 | +820 | +659 | +189 | -15 | +9 |

The two versions are equal on average; the flips are decided by camp production races.

**General mechanism to target:** camp production, meaning which camps v111 commits to and how fast it clears them. Carry conversion is not the target. This is outcome-conditioned and descriptive only; it does not establish cause.
