# The game: Cambridge Battlecode 2026 (CAMBC)

CAMBC is a programming competition. Each team writes a bot that controls a small team of champions, compiles it to
WebAssembly, and uploads it to a ladder where it plays other teams' bots unattended. Nobody plays by hand: the bot
decides everything, every turn, under a hard compute budget.

This page summarises the rules as they mattered to us. The full rule text we worked from is in the official SDK
(`sdk/cpp/cambc.h`); our detailed notes are in [`history/handoffs/HANDOVER_LEAD.md`](history/handoffs/HANDOVER_LEAD.md) §1–2.

## Objective

- Two teams of **3–5 champions** play on a mirrored map, 30×30 up to 100×100. The ladder used a pool of 86 maps, which
  later grew to 128.
- The first team to **tribute (bank) 1,000 gems** at an altar wins. At round 2,000 the team with more banked gems wins,
  with lifetime gold and then kills as tie-breaks.
- Games between strong teams usually end between rounds 1,200 and 1,700.

## The draft

Before play, the teams take turns picking champions from a roster of 12. Each pick is visible to the other side.
The roster: Ryth, Vesper Vale, Vendetta, Cassi + Issac (one pick, two bodies), Stellar, Prism, Marcella, Willow,
Ren, Varg, Tavi and Heart of Ruin. They differ in strength, focus, growth and abilities. For example, Vesper earns +33%
gold, Marcella cannot be stunned, and Vendetta resets cooldowns on a kill.

## Economy

| Camp | Health | Hits for | Gems | Gold | Respawn (rounds) |
|---|---:|---:|---:|---:|---:|
| Gem cluster | 120 | 0 | 7 | 0 | 50 |
| Gold cluster | 120 | 0 | 0 | 20 | 50 |
| Wolf | 1,350 | 20 | 4 | 40 | 40 |
| Elk | 2,400 | 60 | 15 | 90 | 60 |
| Golem | 5,000 | 120 | 36 | 160 | 80 |
| Monolith | 20,000 | 200 | 200 | 300 | 150 |

- **Camps** come in groups. Kill every monster in a group, then hold its region for 5 rounds without enemies, and the
  reward is split among the allies standing there.
- **Banking:** gems are carried until tributed at an altar. A bag of *g* gems takes ⌈g/10⌉ turns to bank. A stun,
  a death or an *altar lock* cancels the banking.
- **Death** takes a champion out for 60 rounds, and the killer takes **every carried gem plus 100 gold**. Carrying a
  big bag is a real risk.
- **Gold** buys items at your own spawn. *Shards* add stats, and five shards combine into an *emblem* with a passive
  (monster, power, durability, treasure, jungle, bruiser, greed, collectors, and others). Consumables include teleport
  crystals and altar locks.

## Combat, vision and communication

- Melee range is 1 (walk *and* attack). Ranged is 3 (walk *or* attack). Each champion casts one spell per turn, on
  cooldowns.
- Fights roughly follow **Lanchester's square law**: numbers matter quadratically, so being outnumbered is lethal.
- Vision is 8 tiles, raycast, and bushes block it. There is **no shared vision**: each champion sees only what it sees.
  Wards extend vision.
- Teammates share only **8 bytes of memory** during play, plus 1,024 bytes written during the draft. Coordination has to
  be encoded very compactly. We used claim slots, sightings and respawn events.

## The constraint that shaped everything: fuel

Every WebAssembly instruction costs **fuel**. A turn gets **100,000 fuel**, with 10× on the first draft turn and
2× on the first play turn. If a turn runs out, it is suspended (a "fuel-out") and the champion loses that turn's decision.

The engine is **fully deterministic**: a game is fixed by the map, the side and the two binaries. As a result:

- Even a do-nothing code change shifts fuel use, and with it later decisions. It flipped 4–7 of 172 local games.
- Adding a few instructions inside a hot loop, with identical behaviour, lost **70–98 over 168 games** (−85 gems a game).

Fuel shaped every design decision in the bot. See [architecture.md](architecture.md) and [findings.md](findings.md).

## Engine versions over the project

| Period | Engine / CLI | Notes |
|---|---|---|
| to 25 Oct | engine 1.0.x | Original rules |
| 26 Oct – 4 Nov | engine 2.0.0, CLI/SDK 4.0.0 ("Sprint 3") | Balance changes: Vesper, Marcella, Heart of Ruin and Ryth nerfed; Varg, Issac, Cassi, Ren, Tavi, Willow, Stellar and Prism buffed |
| from 5 Nov | engine 3.0.0, CLI 5.0.0 | Used for the qualifier week |

Results from different engines are **never** compared directly. `tools/bench_provenance.py` enforces this.
