<p align="center">
  <img src="docs/assets/hero.svg" alt="Team DOOMSDAY, Cambridge Battlecode 2026: #5 in the UK lobby, #41 internationally, 250+ bot builds, 2,100 commits in 24 days" width="100%">
</p>

<p align="center">
  <img alt="Bot: C++20 to WebAssembly" src="https://img.shields.io/badge/bot-C%2B%2B20%20%E2%86%92%20WebAssembly-00599C?style=for-the-badge">
  <img alt="Tooling: Python and Node" src="https://img.shields.io/badge/tooling-Python%20%C2%B7%20Node-3776AB?style=for-the-badge">
  <img alt="UK lobby peak: #5" src="https://img.shields.io/badge/UK%20lobby%20peak-%235-d95926?style=for-the-badge">
  <img alt="International peak: #41" src="https://img.shields.io/badge/international%20peak-%2341-3987e5?style=for-the-badge">
</p>

<p align="center">
  <b>A real-time strategy AI that drafts, farms, fights and banks on its own, every turn, inside a 100,000-instruction budget.</b><br>
  Built, measured and shipped in 24 days for <a href="https://2026a.battlecode.co.uk">Cambridge Battlecode 2026</a>.
</p>

<p align="center">
  <a href="#-highlights">Highlights</a> ·
  <a href="#-the-challenge">The challenge</a> ·
  <a href="#-architecture">Architecture</a> ·
  <a href="#-results">Results</a> ·
  <a href="#-how-we-engineered-it">How we engineered it</a> ·
  <a href="#-the-journey">Journey</a> ·
  <a href="#-lessons">Lessons</a> ·
  <a href="#-repository-map">Repository</a> ·
  <a href="#-team">Team</a>
</p>

---

## ✦ Highlights

<table>
<tr>
<td width="33%" valign="top">

**🏆 5th in the UK lobby**<br>
Peak rank among UK teams. Internationally the bot climbed from **#87 to #41** (rating 1834 → 2206) in two weeks.

</td>
<td width="33%" valign="top">

**⚙️ 17k lines of C++ → WebAssembly**<br>
A deterministic decision engine that runs in under 100,000 WebAssembly instructions per turn, with zero faults as a release gate.

</td>
<td width="33%" valign="top">

**🧠 Neural nets where they pay**<br>
A 16-bit camp-ranking network blended into the heuristic core: **54.6% vs our own best bot** over 1,440 games, at the real compute limit.

</td>
</tr>
<tr>
<td valign="top">

**🗺️ Per-map intelligence**<br>
The bot fingerprints each of 86+ maps on turn one and loads a tuned draft and a 48-knob strategy profile.

</td>
<td valign="top">

**📊 Statistics before ship**<br>
Paired benches across 28 maps × 2 sides × several seeds, map-clustered bootstrap intervals, held-out maps, and paired ladder duels.

</td>
<td valign="top">

**🖥️ Five machines in parallel**<br>
Campaigns on GPU and CPU boxes, coordinated through a git-based job board with leases and heartbeats.

</td>
</tr>
</table>

## ✦ The challenge

Cambridge Battlecode is a programming competition with **no humans in the loop**. Each team uploads a bot, and the
bots play each other on a public ladder around the clock.

> Two teams draft 3–5 champions from a roster of 12, then play up to 2,000 rounds on a mirrored map. Champions clear
> monster camps for gems and gold, buy items, fight, and race to **bank 1,000 gems** at an altar. A death hands the
> killer your entire bag.

What makes it hard:

| Constraint | Consequence |
|---|---|
| ⛽ **100,000 fuel per turn**, one unit per WebAssembly instruction | Run out and the turn is lost. Every loop has a price. |
| 🎲 **Fully deterministic engine** | A do-nothing code change still moves fuel use and flips 4–7 of 172 games, so every build is one draw. |
| 👁️ **No shared vision** | Each champion sees only its own raycast, 8 tiles out. |
| 📡 **8 bytes of team memory** | Coordination has to be bit-packed: camp claims, sightings and respawn timers. |

→ [Full rules primer](docs/game.md)

## ✦ Architecture

<p align="center">
  <img src="docs/assets/architecture.svg" alt="Architecture: a draft phase with map fingerprinting and per-map tables; a per-turn priority cascade of perceive, shop, fight or flee, close out, hunt, bank and farm; side modules for neural networks, the 8-byte team radio and fuel discipline; and a ship pipeline from C++ to the ladder" width="100%">
</p>

- **Priority cascade.** Each turn walks seven stages, and the first one that acts ends the turn. That keeps the
  common case cheap and the expensive analysis rare.
- **Heuristic core, neural edges.** Camp choice is scored by hand-built value, distance, danger and crew-size terms.
  A small quantised network re-ranks the result and overrides it only when it is more than 2 logits more confident.
- **Fuel as a first-class resource.** New logic runs once per turn, never per camp. Network inputs refresh in stages on
  spare fuel, and distance fields are built lazily.
- **Bit-packed coordination.** Six claim slots, sightings and respawn events fit in 8 bytes, so champions split camps
  without colliding.

→ [Architecture deep-dive](docs/architecture.md)

## ✦ Results

<p align="center">
  <img src="docs/assets/ladder.svg" alt="International ladder rank: #87 on 25 Oct, #54 on 26 Oct, #68 on 3 Nov, #63 on 4 Nov, a peak of #41 on 8 Nov, #53 on 9 Nov. Peak in the UK lobbies: #5." width="100%">
</p>

<sub>International ranks come from dated ladder snapshots (dots), with lines joining them. The UK lobby ranks UK
teams separately; our peak there was 5th.</sub>

| Milestone | Build | Measured |
|---|---|---|
| Island and stampede map fixes | v51–v52 | stampede 0/28 on the ladder → 6–0 locally |
| Economy package on the new rules | v58 | 430/672 games, +153 gems a game vs v57 |
| Per-map draft and knob tables | v74 | best of its generation in paired top-12 ladder duels |
| Neural camp blend (nnq4) | v106 | 54.6% ± 1.3 vs v92 over 1,440 games |
| Retuned network weights | v112 | **international #41**, rating 2206 |
| Home-siege and navigation fixes | v118 cycle | home capture from round 1,353 → 417; Islands 7/18 → 15/18 |
| Shop-while-waiting | v137 | +149 over 2,064 paired games vs v130 |

## ✦ How we engineered it

| Practice | What we did |
|---|---|
| **Release gates** | Candidates played the current bot on 28 development maps × both sides × several seeds. They shipped only if a map-clustered bootstrap interval cleared zero, with no regression on 12 held-out maps and zero faults. |
| **Paired ladder duels** | Local self-play turned out to be a poor predictor, so we built a pipeline that plays a candidate and the base against the *same* ladder opponents, pinned to identical bot versions. |
| **Replay intelligence** | We built an official-engine replay decoder and decoded about **245,000 ladder matches** into NumPy shards. That data fed team ratings, behaviour-cloning datasets, loss diagnoses and top-team studies. A win-probability model trained on 138k game states reached 73.6% held-out accuracy. |
| **Map atlas** | The bot computes about 25 features of each map itself (exact on 86/86 maps), sorts maps into 7 categories, and picks one of 14 strategy profiles at round 3. |
| **Distributed campaigns** | A PC, a laptop and GPU boxes (RTX 5060, RTX 5070 Ti) ran experiments in parallel, coordinated by a git message board with jobs, leases and heartbeats. |
| **Root-cause loops** | Logging builds and decision traces found map-specific bugs fast. For example, home monoliths were never attacked because `need > team_size`; a 3-champion siege crew fixed it. |

## ✦ The journey

| | Phase | Dates | What happened |
|:-:|---|---|---|
| 0 | Prototype | 19–21 Oct | First repository: parallel workstreams, bots v34–v36, tuning on engine 1.0.1 |
| 1 | Neural framework | 24 Oct | Behaviour cloning on **7.3M** top-team decisions. It learned nothing usable, so we pivoted to a heuristic core |
| 2 | Heuristic sprint | 25–26 Oct | v51 → v61 behind statistical gates. **International #87 → #54** |
| 3 | Per-map tuning | 27–28 Oct | Per-map drafts and knob tables (v65–v81), a proxy of the top teams, and DOOMSDAY Zero, a clean-slate rewrite |
| 4 | Scale-out | 29 Oct – 2 Nov | Map atlas and portfolio, gigabot and botx3 lines, multi-machine campaigns. **v92** becomes the reference |
| 5 | Neural blend | 3–5 Nov | The nnq4 camp-ranking blend (v106), a recurrent PPO learner, migration to engine 3.0.0 |
| 6 | Qualifier week | 7–11 Nov | Retuned weights take us to **international #41**. Root-cause fixes v113–v138 run up to the UK qualifier lock |

→ [Detailed timeline, with sources](docs/timeline.md)

## ✦ Lessons

1. **Compute is the opponent.** A behaviour-identical change in a hot loop lost 70–98 over 168 games.
2. **One build is one draw.** An "improved" RL checkpoint fell from 56% to 44.5% once its own scores were jittered.
3. **Self-play lies.** Local gains of +37 to +89 were about zero on the ladder. Only paired ladder duels predicted it.
4. **Losses are economic.** Production was the biggest deficit in 96 of 151 losses, and +150 gold at round 100 meant
   an 84.5% win rate.
5. **Networks belong beside heuristics, not instead of them.**

→ [All findings, with the numbers](docs/findings.md)

## ✦ Repository map

```text
bots/        250+ builds by line: mainline (v48 → v115e), x-series, gigabot, live-line, botx3, rl-env, neural, doomsday-zero
research/    Reports and measurements for every version and line (versions/, live-line/, rl-env/, x-series/, …)
tools/       Benchmarks, Bayesian and map-clustered comparison, replay decoding, ladder duels, map atlas
data/        Ladder snapshots, decoded loss samples, match manifests
maps/        The 86-map ladder pool, benchmark sets, generated and maze maps
neural/      The neural framework: Python package, schemas, models, locked evaluation protocol
tests/       Python and C++ tests, mechanic probes, loss cases
sdk/         The official C++ SDK and CMake files
docs/        Rules primer, architecture, timeline, findings, team; history/ holds the original working notes
archive/     Retired material: the v36 prototype, framework workspaces, continuation packages
```

## ✦ Team

<table>
<tr>
<td align="center" width="25%"><b>Om Dhande</b><br><sub>Team lead</sub><br><a href="https://github.com/Infosuii"><code>@Infosuii</code></a></td>
<td align="center" width="25%"><b>Rishik</b><br><sub>Campaigns · RL environment</sub><br><a href="https://github.com/R1shik123"><code>@R1shik123</code></a></td>
<td align="center" width="25%"><b>Ishan Patil</b><br><sub>Fuel merge · live analysis</sub><br><a href="https://github.com/ishanp765"><code>@ishanp765</code></a></td>
<td align="center" width="25%"><b>Iniya</b><br><sub>Neural blend research</sub></td>
</tr>
</table>

→ [Who built what, and where every old branch went](docs/workstreams.md)

---

<sub>This is a finished project: the competition has moved on to newer engines, and the repository is kept as a record
of the work. Every former branch is preserved as a tag `archive/<branch-name>`. Large raw evidence (game-dump zips,
split archives) is in git history but not in the current tree; see
<a href="archive/REMOVED_FROM_TREE.tsv"><code>archive/REMOVED_FROM_TREE.tsv</code></a>. Scripts use the paths from
before the cleanup. Build a bot with <code>cambc build bots/mainline/v92 --release --output v92.wasm</code>.</sub>
