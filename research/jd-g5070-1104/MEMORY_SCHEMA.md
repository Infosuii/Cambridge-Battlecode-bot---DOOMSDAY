# Memory schema: 8-byte shared word and 1,024-byte draft buffer (candidate bots/jd-g5070-1104 = v92 by default)

Run g5070-1104, FEAT-002. Mission section 5. The codec for this schema is `bots/jd-g5070-1104/src/jd_mem.h` (pure, no
`cambc.h`). The executable fixtures are `tools/jd_g5070-1104/tests/mem_test.cpp`, run by
`py tools/jd_g5070-1104/host_tests.py` (32,253 checks, 0 failures). The schema is unchanged from v92. No protocol
redesign was made, because no fixture showed that the current layout loses information worth the bits. The fixes
below only correct how readers interpret the current layout.

"Compiled in" below comes from preprocessing the default build (`g++ -std=c++20 -dM -E -I sdk/cpp -I
bots/jd-g5070-1104/src bot.cpp`). The relevant macros are APEX_EVENTS 2, V54_ONSITE 1, APEX_BRAIN 1, A2_MLDRAFT 1,
A2_HOR 2, A2_MLPLAN 0, A2_DPLAN 0, V58_DIRECTOR 0, APEX_INCUMBENT 0, APEX_DISTRESS 0, APEX_TFC 0 and NOVA_NO_SIGHT 0.
No bot config macro depends on `__wasm__`/`NDEBUG`.

## Shared word (team-wide, 8 bytes, offset 0)

| bits | sighting form (bit 63 = 0) | event form (bit 63 = 1) |
|---|---|---|
| 0-41 | six 7-bit claim slots, slot s = index of the body in `bc::champions(ally)` | same |
| 42-48 | sighting x (7 bits) | camp group id (7 bits, < 127) |
| 49-55 | sighting y | respawn-ready round mod 256 (bits 49-56) |
| 56-61 | sighting round mod 64 | (bit 56 = ready bit 7) |
| 62 | distress (fleeing, call for help) | 0 |
| 63 | 0 | 1 |

Claim codes (7 bits): `127` idle, `126` dead, `64+g` = claims group g and is on site (V54_ONSITE, only when the map
has <= 48 groups), `112+k` = fight order (engage enemy k, k < 6; 118 = retreat; written and read only when the map
has < 112 groups), otherwise the raw group id. The comment in bot.cpp `write_claim` says "8 bits per slot, 255/254".
That comment is stale: the compiled constants are 7 bits, 127 and 126.

### Readers and writers (default build)

| function (bot.cpp) | reads | writes | compiled |
|---|---|---|---|
| `Bot::init` | `read_shared` + `decode_claims` | `write_claim(-1)` (first writer on an all-zero word sets all six slots idle) | yes |
| `play_turn` start | `read_shared`, `decode_claims` each live and dead turn | `unmark_onsite` when we left the group | yes |
| `write_claim(g, onsite)` | latest host word | our slot only | yes (farm, rush, dead) |
| `write_order(code)` | latest host word | our slot only | yes; called only with `kTfc` or `packOn` |
| `share_sighting(distress)` | latest host word | bits 42-62, clears bit 63 | yes, every live turn with an enemy in view; distress off (APEX_DISTRESS 0) |
| APEX_EVENTS writer (`play_turn`) | latest host word | event form bits 42-63, only with no enemy in view and no sighting younger than 12 rounds | yes (APEX_EVENTS 2) |
| `read_sighting` | `shared` (this turn's word) | - | yes, every live turn |
| `track_claims` | claim cache | - | no (APEX_INCUMBENT 0) |
| economy (V58) word writer | latest host word | - | no (V58_DIRECTOR 0) |

Every compiled writer does a read-modify-write from the latest host word, and every write preserves unrelated fields
(`test_rmw_turn_order`, `test_claim_roundtrip`). Nothing clears the whole word to send one message. Dead champions
read claims but skip `read_sighting` (the dead branch returns first).

### What a claim promises (answered against the code)

- **Heading there / working it:** `farm()` writes the claim when it picks a group. Teammates then count it in
  `claim_count`, `claims_split` and `senior_claims`.
- **On site:** `64+g` is written by `mark_onsite` at the staging ring or when standing on the group. It is cleared
  by `unmark_onsite` once we are more than 5 tiles from all of its camps, checked at the next turn start.
- **Fighting, fleeing, banking, recalling:** the claim is NOT rewritten. A champion that flees or walks home to bank
  keeps claiming its last group, so teammates keep treating that group as taken. This is the H02 observation that
  X1_FLEEFIX targets (default off). This is a stale promise, not a codec defect. Fixing it changes behaviour, so it
  belongs to FEAT-004 (JD_PROGRESS releases the claim).
- **Dead:** `126` is written once on the first dead turn. After the respawn the slot stays dead until the next
  `farm()` claim.
- **Reassigned / displaced:** the next `write_claim` overwrites the slot. There is no lease or TTL, so an unchanged
  claim stays valid for as long as its writer lives.
- **Off-screen intentions do not mean presence.** Only the onsite code (`64+g`) states presence, and only on maps
  with <= 48 groups.

### Measured properties (mem_test FINDING lines)

| question | answer | fixture |
|---|---|---|
| Do group ids collide with reserved codes on the largest maps? | No aliasing for 1-255 groups: no group decodes as another group or as an order. Groups >= 126 are published as idle, so their claim is lost (129 ids on a 255-group map). Onsite marks exist only with <= 48 groups, and orders only with < 112 groups. | `test_reserved_collisions` |
| Is mod-64 sighting age ever mistaken? | Yes. An unchanged sighting reads as fresh (age <= 10) again 64 rounds later, 44 times in 300 rounds. The word stays unchanged whenever nobody sees an enemy and no event is published. **Fix JD_SIGHTAGE.** | `test_sighting_age_wrap` |
| Can mod-256 events become phantom future respawns? | Yes. An unchanged event word (group 5 ready at 130, published at 100) decodes as a future respawn on 341 of the next 500 turns, from +95 rounds and up to 191 rounds ahead. Readers re-apply it every turn, so `apply_event` marks a live group as respawning. A 160-round bound alone (X1_RESPAWNFIX-style) still lets 279 of those through. **Fix JD_EVTONCE.** | `test_event_phantom` |
| Are RMWs based on the latest host word? | Yes for every compiled writer. The fixture shows that a writer using its turn-start copy would erase a teammate's claim. | `test_rmw_turn_order` |
| Does turn order invalidate slot coordination? | Slots are indexed by `bc::champions(ally)` order, which is fixed for the game. Lower slots act earlier in a round (`claims_split`), and a later body sees an earlier body's claim within the same round because each write goes to the host at once. | `test_rmw_turn_order` |
| Spare slots for multiplexing? | None in general: 5 picks including Cassi+Issac give 6 bodies and use all 6 slots. | `test_team_sizes_and_recovery` |

## Draft buffer (team-wide, 1,024 bytes)

`bc::draft_memory` is a startup snapshot. A submit writes a prefix to the host and leaves later host bytes unchanged.
Measured with JD_FUELPROBE (fuel_contract.json): one draft VM serves all of our draft turns, so its globals live
across picks. Gameplay VMs see the 1,024 bytes but none of the draft VM's globals.

| bytes | owner (writer) | content | validity check | compiled |
|---|---|---|---|---|
| 0-5 | `brain::record_draft` (strategy.h), called on every draft turn except the A2_HOR pick turn and the TOP_PICKS/A2_MLDRAFT early returns *after* the write | 0xA5, team size, enemy caster picks, map class, max group gems, flags (bit0 race, bit1 monolith) | magic and >= 4 bytes; the reader trusts team size and class (jd_mem `read_brain` adds range checks) | yes |
| 6 | - | unused | - | - |
| 7 | A2_MLPLAN (draft.cpp `ml_draft_pick`, last pick) | 0x80 \| plan | flag bit | no |
| 8.. | A2_DPLAN (`team_plan_bytes`) | 'P', slot count, per-slot (n, then n x (group, round/2)) | 'P' magic | no |
| 1008-1015 | `economy_record_roster` (V58_DIRECTOR) | 0x58, body count, up to 6 body types (Cassi+Issac expanded to two bodies) | magic and count == bodies | no |

The A2_HOR pick (our 2nd pick when Heart of Ruin is still free) returns before `record_draft`. The header is still
correct after the draft, because every other draft turn rewrites the full 6-byte header and the host keeps it. A
header written on an earlier turn can miss enemy casters picked later, but only if the HoR pick is our last turn.

### Defects found by the fixtures

- **Latent ML-plan erase:** with A2_MLPLAN and A2_DPLAN both on, the DPLAN write (8 zero bytes, then the plan)
  erases byte 7 written earlier in the same turn (`test_draft_regions`). Both are off by default.
- **Stale-snapshot overwrite pattern:** a writer that builds its submit from its VM's startup snapshot erases what an
  earlier draft turn wrote in the same game (`test_draft_regions`). `economy_record_roster` already avoids this by
  reading the current host bytes. No compiled writer uses the stale pattern today.
- **Map mismatch:** the reader accepts the header's map class without recomputing it. A 4-body header with class 3
  read on a 40x40 map (class 2) is detectable with `jdmem::map_class`. The engine scopes draft memory to one game,
  so the mismatch cannot occur in a real game. No fix.
- Absent, corrupt and truncated payloads (lengths 0, 3-6, 1015, 1016; bad magic; impossible team size, class or
  body count) all fall back cleanly (`test_payload_validation`).

### JD_MEM owner/merge

`jd_draft_submit(region, bytes, n)` (jd_mem_bc.h) reads the current host bytes with `sdk_read_draft_memory`, writes
only its region (`jdmem::merge` rejects oversized payloads) and submits the prefix up to that region's end. Under
JD_MEM 1 all four writers use it: brain (prefix 6, the same bytes as today), ML byte 7 alone, DPLAN from byte 8
alone, and the roster. The shared-word writers use `jdmem::set_code`, `set_sighting` and `set_event` (bit-identical
words). In the default compiled configuration JD_MEM changes no published byte. It costs one 1,024-byte host read
per draft turn.

## Role/intent recovery

`test_team_sizes_and_recovery` covers team sizes 3-5, with and without Cassi+Issac at every pick position (6 bodies
at most), and with a header written on the first and the last pick. Each body slot rebuilds its role and intent from
the draft bytes plus the shared word alone: team size, map class, body type (from the roster), claim kind/group,
onsite, dead and idle. Unused slots of smaller teams stay idle. Without the V58 roster (default off), an ally's body
type is unknown until it is seen (`init` falls back to `vesper_vale`). The roster region is the existing remedy, and
the fixture proves it maps picks to slots in pick order.

Engine check (JD_FUELPROBE `JDFP P/S` lines, `diag-fprobe-03`, 16 games, 92 gameplay VMs; fuel_contract.json
`slot_mapping`):
- `bc::champions(ally)` order equals our pick order with Cassi+Issac expanded to two bodies. This holds for every
  pick the draft VM could see, in 92 of 92 VMs.
- Every ally's `champion_name()` was readable on the first play turn (0 unseen in 92 VMs), so init's `vesper_vale`
  fallback did not fire in these games.
- **The draft VM's last turn does not see its own pick** in `current_draft(ally)`: 112 bodies were missing over 92
  VMs, which is the last pick, or 2 bodies when it is Cassi+Issac. Two consequences:
  - Anything written on the last draft turn misses that pick. This includes `economy_record_roster` (V58, default
    off): its body count is then short by the last pick, so `init`'s `count == bodies` check always rejects it.
  - The brain header's enemy-caster count misses enemy picks made after our last turn.

  A roster for gameplay must therefore be completed in gameplay from `champions(ally)`, or written with the last
  pick appended by the draft code that chose it.

## Fixes (each its own switch, default 0)

- **JD_EVTONCE = 160:** each reader applies a distinct event word once (`jdmem::EventOnce`) and rejects decodes more
  than 160 rounds ahead (the monolith's 150-round respawn plus a margin). Known limit: a reader that was dead when
  the event was published and first sees it after it wrapped can still decode a phantom within the horizon.
- **JD_SIGHTAGE = 1:** `jdmem::SightClock` ages an unchanged sighting on the reader's own clock. The same age is used
  by the event writer's "fresh sighting" check, so a wrapped old sighting no longer blocks event publication.
- **JD_MEMLOG = 1** (diagnostic): prints cumulative trigger counters (`JDMEM ... evt_phantom evt_horizon
  sight_phantom`) every 50 rounds.

## Experimental proposals (not implemented)

- A 1-bit sighting/event epoch (bit 57 of the event form is free) would let readers tell a republished event from a
  stale one without per-reader state. It is not needed while EventOnce works.
- Releasing claims on flee/bank/recall (claim = "heading there or working it") changes behaviour and is left to
  FEAT-004's JD_PROGRESS.
