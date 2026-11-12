# Bots

More than 250 bot builds, grouped by workstream. In each folder, `src/` is exactly what `cambc submit` uploads.
Where a version has a `CHANGES.md`, it records what changed and how the change measured.

| Folder | What's inside |
|---|---|
| [`mainline/`](mainline) | The ladder lineage, **v48 → v115e**, with single-change variants such as `v62a–f`, `v66x_*`/`v66y_*` and `v92*`. Includes `live-69`, a frozen copy of platform version 69. |
| [`x-series/`](x-series) | z-plan development bots: `x1`/`x2`/`x3`, map-table bots `x3mf`/`x3mf2`, counter tables `x3ctr*`, the `x3inv*` sparring partners, and portfolio profiles `pf0`–`pf13`. The default `x3` build is byte-identical to v92. |
| [`gigabot/`](gigabot) | gigabot (gx): about 100 single-mechanism increments (`gx-bankproof01`, `gx-siege01` …), each with a matched control, plus `gx-final`. |
| [`codex/`](codex) | Candidates from the Codex agentic loop: siege, ward, bush, opening and fuel variants, and `codex-live111-frozen`. |
| [`botx3/`](botx3) | The team-economy line, `botx3` and `botx3_1`–`botx3_11`. |
| [`rl-env/`](rl-env) | Qualifier-week builds from the RL environment (`claude-rlenv-1104`, `claude-native-1104`) and johndoe's g5070 qualifier builders. |
| [`neural/`](neural) | `agent2-v61` (Agent 2's neural experiments) and `mimic`, a replay-trained policy prototype. |
| [`doomsday-zero/`](doomsday-zero) | DOOMSDAY Zero, the clean-slate C++20 rewrite started on 28 Oct. |
| [`opponents/`](opponents) | Sparring partners: `proxy` (a stand-in for the top ladder teams) and three public bots. |

## Key versions

| Version | Why it matters |
|---|---|
| `mainline/v58` | Economy package on the Sprint 3 rules: 430/672 vs v57. Submitted as platform 57. |
| `mainline/v61` | Platform 60. Rank 54 on 26 Oct. |
| `mainline/v74` | Per-map draft and knob tables. Best on the ladder in the top-12 duel; platform 68. |
| `mainline/v92` | The reference bot from 2 Nov (platform 75 / 80). The base of most later work. |
| `mainline/v113` | Om's fuel fix on top of v112, the Codex build that was live at our peak of rank 41. Base of v114–v117. |
| `mainline/v115e` | Ishan's v113 + v114 merge with extra network fixes. |

Later live builds (v117–v138) came from the Codex workstream and the rl-env patch pipeline. Their sources are in
`research/codex-live/` (release zips) and `tools/rl_env_1104/` (patch scripts on top of v130/v135). See
[docs/timeline.md](../docs/timeline.md).

## Building

```bash
cambc build bots/mainline/v92 --release --output v92.wasm
```
