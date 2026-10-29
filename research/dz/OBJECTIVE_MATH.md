# Objective arithmetic foundation

`bots/dz/src/objective_math.h` adds three SDK-free primitives for the later
objective model. None is called by production decisions. Full routes, movement
overlap, spells, survival, crews and contest probability are still unmodeled;
this does not close V-M1.

- Solo capture distinguishes new physical eligibility from an initialized
  countdown. A new arrival uses configured duration +1; an active allied timer
  uses that timer alone. The caller must establish the same sole capturer stays
  on-site. Contested, enemy-owned, unavailable and uncertain ownership inputs
  decline a quote. Invalid timers decline it too.
- Tribute rounds the base timer first, then applies the effective reduction and
  rounds again. Multiplication deliberately retains engine float arithmetic.
  Widening the float 0.1 before multiplying a decade bag can predict an extra
  round. Zero bags and invalid/unbounded settings decline a quote.
- Solo gem/gold-cluster and wolf rewards support one Prospector emblem and
  Vesper's passive. Gem bonuses floor per award; gold retains an explicitly
  supplied fractional history in units of 1/400. Unknown history returns a
  lower/upper award interval of width at most one. It never invents a remainder.
  Integer purchases preserve a known remainder; death, unknown gold events and
  untested passives must invalidate it. Mixed groups, splits, Treasure, other
  heroes and duplicate-family effects remain unsupported caller contexts.

The fractions reproduce the tested reward phenotype; they do not assert the
engine's internal number representation. Inputs use the pinned 2.0.0 settings
and modifiers. The engine fingerprint must pass before these rules are used.

Host checks cover timer/state boundaries, invalid inputs, every bag 1..2000
against the independently known integer decade rule, ordered reward examples
and all 400 possible remainders for 24 modifier/award combinations. Reward
arithmetic widens before multiplication, including maximum uint32 gold input.
Native diagnostics execute the exact header copied into their frozen source,
compare predictions with actual receipts and countdown samples, and retain
both exact-history and unknown-history reward checks. The audit script reads
native summaries directly to verify both teams' faults and fuel-outs.

The planned `OBJECTIVE_MATH_VALIDATION.json` will record accepted current-header
campaigns and content hashes. Validation is paused and incomplete; read
`../../CLAUDE_HANDOFF.md` and `PAUSED_WORK.json`. Earlier 01 tests precede an additional active-timer input
guard. The initial 02 Prospector probes passed an already filtered applicability
flag; 03 passes actual item ownership even for the wolf, exercising the
primitive's responsibility to exclude a non-cluster bonus. All are retained.

The default release was rebuilt and remains byte-identical to the 069dfb0
behavior checkpoint. No pool games are repeated for unused arithmetic. The
existing full-pool reliability evidence remains applicable to that binary;
it still loses all contested v65 games and is not a competitive-strength gate.
