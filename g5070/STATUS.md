# g5070 status — STOPPED under burst stop rule

- Burst clock start:2026-11-02 01:21:01 UTC. No-new-batch cutoff02:41:01 UTC; nominal end02:51:01 UTC.
- Next observed clock08:52:16 UTC, beyond cutoff. K001 had already finished01:30:13.596129 UTC. No new batch started after that observation. No game batch remains running.
- Machine:20 logical processors,18 game workers,33,752,997,888 available memory bytes; Python3.12.10; official Windows CLI4.0.0. Approx236.00 games/min after builds/result processing;111.08 including build setup.
- Source:build/z-plan263680346a70df95fda33bba1dc2e3b2d09b44aa, local-only57af220 cherry-pick ->6d13dd2b65f7fb393fd882e58946a31e121ddedc on isolated burst branch. No code branch pushed. bots/x1 unchanged.
- **K001 DONE:**68/140;110 fuel-outs;0 own/0 opponent faults;140/140 replay hashes and summary hashes and every per-game field match reference. [Result](results/K001.md).
- **K002 INCOMPLETE:**0/9 full gate lines complete. Base:ladder/x2 available via K001; styled/x2, ladder/x2-s2, styled/x2-s2 NOT RUN. prunefix,teamwin,soak64,heartfix,fleehold4,fleehold15,fleehold8,siegestrict:all four cells NOT RUN for each. [Exact table](results/K002.md).
- **K003 NOT STARTED:**all65 flags not started here. [Per-flag inventory](results/K003.md) distinguishes existing PC results at the frozen source, pending cells and same/duplicate binaries;[CSV](results/K003/remainder.csv).22 different-binary flags have at least one pending cell in that snapshot.
- [Clock/cutoff message](msgs/0001-burst-clock-cutoff.md). Numbers and gate status only; no feature rejection. All replays stay local. Writes on comms/x1 are confined to g5070/.
