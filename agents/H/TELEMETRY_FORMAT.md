# Telemetry and fuel formats consumed by Agent H

## 1. `NFT1` lines (Agent B dev telemetry, only when `kTelemetry`; never in release)

`python/nfs/evaluate/fuel.py: parse_nft1_line / parse_telemetry` parses tolerantly. The engine pads per-turn stdout
with NUL bytes; `engine.team_stdout` and the parser strip them. Accepted payloads after the `NFT1 ` tag, tried in this
order:

1. A JSON object: `NFT1 {"head":"move","calls":3,"fallback":1}`
2. Base64 JSON: `NFT1 b64:eyJoZWFkIjoibW92ZSJ9`
3. An optional bare kind token followed by `key=value` pairs: `NFT1 head head=bank calls=4 fallback=1 reason=budget fuel=812`
4. `key=value` pairs only: `NFT1 head=bank calls=4`

Values are int if integral, float if decimal, true/false as bool, `"quoted"` as string, and anything else (including
`nan`/`inf`) as string. Unparseable lines are counted as `malformed`, not dropped silently.

**Expected keys (request to Agent B).** One summary line per head per reporting window (bounded, for example every
250 rounds plus the last turn):

| key | meaning |
|---|---|
| `head` | head name as in `schemas/heads.json` (`_turn` for per-turn/encoder lines) |
| `calls` | decide() calls |
| `admitted` | budget-admitted calls |
| `neural` | calls whose executed choice came from the network (active mode) |
| `fallback` | calls that returned the teacher choice for a non-shadow reason |
| `refused` / `budget_refused` | budget refusals before feature work |
| `invalid` | network chose an illegal candidate. **Must be 0**; fails the plumbing check |
| `nan` | NaN/Inf detected (fallback taken). **Must be 0** |
| `skipped` / `errors` | encoder skipped / schema or model errors |
| `reason` (+ `count`) | fallback reason histogram entries |
| `fuel` / `spent` / `fuel_spent` | measured fuel for the window or call (Meter) |

Aggregation sums the counters per head and in total, keeps a histogram of reasons, and records the mean and max of
the fuel values. If B chooses different key names, B should document them in `agents/B/`. H will then add aliases in
`parse_telemetry` without changing the line grammar.

## 2. Replay-bundle `team-a.fuel` / `team-b.fuel` (engine 1.0.3; format inferred by H, not documented by the CLI)

```
bytes 0..7   b'a62leuf\0'                       tag
bytes 8..12  00 00 01 00 00                      opaque header (constant in all observed files)
then int64 little-endian:
  [0..7]     budgets: 1000000 (draft), 100000 (turn), 200000 (first turn), 100000, then the same 4 again
  [8..]      fuel USED by each turn of this team, in engine order:
             n draft picks (n = champions per team), then one value per champion per round
             (the first champion turn has a 200k budget; the last round may be partial)
```

Evidence (`agents/H/REPORT.md` section 3):

- Exhausted turns read exactly 100000. The count of regular turns at the cap equals the summary's `fuelExhausted`
  entries for that team on every reference cell checked (52 matches, plus older diagnosis runs such as
  01yellow-brick-road with 26 and 13 entries).
- A build that burns about 13.5k fuel after its decisions shifts exactly those turns by +13,523, and the replay is
  unchanged.
- The layout is consistent: draft count plus champions x (rounds - 1) < values <= draft count plus champions x
  rounds.

Use: per-turn tail statistics (p99, p99.9, max, turns >= 90/95% of budget, last-quarter tail) and per-turn overhead
between two action-identical runs. Gate decisions use only the official `fuelExhausted` events. The `.fuel` tail is
report-only.
