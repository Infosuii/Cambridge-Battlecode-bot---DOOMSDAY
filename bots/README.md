# Bots

## Final local releases

| Build | Source | Status |
|---|---|---|
| **v306AltarPressureReach** | [Browse](mainline/v306AltarPressureReach/src) | **Recommended** from the final local comparison |
| v320CampChannelCore | [Browse](mainline/v320CampChannelCore/src) | Camp-aware channel safety; retry required |
| v348LethalFinishSafety | [Browse](mainline/v348LethalFinishSafety/src) | Adds lethal camp-finishing spell exception; retry required |

[Download the compiled v306 ZIP](../research/doomsday-movement-20261110/releases/best-final-v306AltarPressureReach/compiled-bot.zip)
· [Read the evidence](../docs/RESULTS.md) · [Understand the architecture](../docs/architecture.md)

## Historical families

More than 250 bot builds, grouped by workstream. In each folder, `src/` is exactly what `cambc submit` uploads.
Where a version has a `CHANGES.md`, it records what changed and how the change measured.

| Folder | What's inside |
|---|---|
| [`mainline/`](mainline) | The historical ladder lineage, **v48 → v115e**, plus the frozen **v306/v320/v348** local releases, with single-change variants such as `v62a–f`, `v66x_*`/`v66y_*` and `v92*`. Includes `live-69`, a frozen copy of platform version 69. |
| [`x-series/`](x-series) | z-plan development bots: `x1`/`x2`/`x3`, map-table bots `x3mf`/`x3mf2`, counter tables `x3ctr*`, the `x3inv*` sparring partners, and portfolio profiles `pf0`–`pf13`. The default `x3` build is byte-identical to v92. |
| [`gigabot/`](gigabot) | gigabot (gx): about 100 single-mechanism increments (`gx-bankproof01`, `gx-siege01` …), each with a matched control, plus `gx-final`. |
| [`live-line/`](live-line) | Candidates from the live line's automated improvement loop: siege, ward, bush, opening and fuel variants, and `live111-frozen`. |
| [`botx3/`](botx3) | The team-economy line, `botx3` and `botx3_1`–`botx3_11`. |
| [`rl-env/`](rl-env) | Qualifier-week builds from the RL environment (`rlenv-1104`, `rlenv-native-1104`) and the g5070 qualifier builders. |
| [`neural/`](neural) | `nn-v61` (neural experiments from v61 onward) and `mimic`, a replay-trained policy prototype. |
| [`doomsday-zero/`](doomsday-zero) | DOOMSDAY Zero, the clean-slate C++20 rewrite started on 28 Oct. |
| [`opponents/`](opponents) | Sparring partners: `proxy` (a stand-in for the top ladder teams) and three public bots. |

## Key versions

| Version | Why it matters |
|---|---|
| `mainline/v58` | Economy package on the Sprint 3 rules: 430/672 vs v57. Submitted as platform 57. |
| `mainline/v61` | Platform 60. International #54 on 26 Oct. |
| `mainline/v74` | Per-map draft and knob tables. Best on the ladder in the top-12 duel; platform 68. |
| `mainline/v92` | The reference bot from 2 Nov (platform 75 / 80). The base of most later work. |
| `mainline/v113` | Om's fuel fix on top of v112, the build that was live at our international peak of #41. Base of v114–v117. |
| `mainline/v115e` | Ishan's v113 + v114 merge with extra network fixes. |

Later live builds (v117–v138) came from the live line and the rl-env patch pipeline. Their sources are in
`research/live-line/` (release zips) and `tools/rl_env_1104/` (patch scripts on top of v130/v135). See
[docs/timeline.md](../docs/timeline.md).

## Building

```bash
cambc build bots/mainline/v92 --release --output v92.wasm
```
