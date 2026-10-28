# v71: the team's best bot (received 2026-10-28), frozen base for v72

Source: `bot (2).zip` from the team (SHA-256 `726d0e9223e6d7a1968bba12573cf329eceb9e7c5797dd244d0e3ee08820b6a6`),
33 files under `src/`, copied unchanged. It was developed outside this repository; v59–v70 are not in the repo.
Do not edit; copy to a new version folder.

Lineage (from its own `common.h` comments): v58 + the v65 48-knob lab vector (`A2_KNOBS`) +
- `V68_SIEGE_FIX` 1: incremental siege line-of-sight scan (00vault froze champions on fuel every turn);
- `V69_ISLAND` 1: a champion stranded on a hole island dashes back to walkable ground or recalls;
- `V69_CAPTURE_STALL` 15: after 15 rounds stalled on a reward region, fight for the capture or leave;
- `V70_DRAFT_TABLE` 1: per-map draft lineups for the pool maps (keyed by width, height, team size, camp groups);
- `V71_MAP_KNOBS` 1: per-map strategy profiles over the runtime lab knobs.

Measured vs frozen v58 on the 120-map suite (both sides, official CLI 4.0.0 / engine 2.0.0, release builds, official
fuel; `tools/mapgen/profile_maps.py`): **164/240 (68.3%), +230.3 gems (map-clustered 95% +161 to +299), 0 faults**.
Official dev 66.1% (+234), official holdout 83.3% (+272), fresh pool 78.3% (+424); generated dev 61.4% (+105),
generated holdout 58.9% (+100). The per-map tables apply only to recognised pool maps, so its edge roughly halves on
unseen maps.
