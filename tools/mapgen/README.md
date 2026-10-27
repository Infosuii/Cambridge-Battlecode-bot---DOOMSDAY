# Map generation: a 120-map test suite (70 official + 50 generated)

Sprints introduce maps nobody has seen. The 70 published maps are too few to measure small changes and give no
unseen maps for development. These tools add **50 generated maps that are statistically indistinguishable from the
official ones**, in layout and in how games play out, so testing covers more of the space that new maps come from.

| Folder | Maps | Use |
|---|---|---|
| `maps/local-benchmarks` | 70 official | unchanged (28 development, 12 `final` holdout, 30 fresh) |
| `maps/generated/dev` | 22 generated | development, like the 28 development maps |
| `maps/generated/holdout` | 28 generated | frozen candidates only, once each, like the official holdouts |

Suite record: `evaluation/schedules/map_suite_120.json` (per map: split, template, size, symmetry, team size, group
sources; the screening envelope; every rejected map with its reason). Evidence: `research/maps/`.

## Running them

```bash
# development: the 22 generated dev maps (allowed without HOLDOUT=1)
MAP_DIR="$PWD/maps/generated/dev" bash tools/bench3.sh "$PWD/bots/v59" "$PWD/bots/v58" "$PWD/artifacts/evaluations/v59-gendev" 1 2 3
# frozen candidates only: the 28 generated holdout maps
HOLDOUT=1 MAP_DIR="$PWD/maps/generated/holdout" bash tools/bench3.sh "$PWD/bots/v59" "$PWD/bots/v58" "$PWD/artifacts/evaluations/v59-genhold" 1 2 3
```

Combine with the official development bench through `tools/bench_pool.py` and decide with `bench_compare.py` /
`bench_bayes.py` as usual. Generated maps are related to their template map: a generated dev map never copies a
holdout map's style, and every generated holdout map copies a holdout or fresh map's style.

## Method

Not a plain bootstrap: resampling whole official maps adds no new test conditions. Instead, a **structured
resampling of official map components**, done through the engine's own MapBuilder (engine 2.0.0 map-editor wasm):

1. **Read** every official map exactly through the engine (`mapio.py`, `extract_official.py`): size, symmetry, team
   size, spawn rectangle, every wall/bush/hole/altar tile, every camp and camp group (types, gems, gold, respawn).
   Terrain is stored for the whole map (100% mirror-closed); camps/groups for the authored half.
2. **Style:** draw an official template map; scale its size by 0.85–1.15; keep its team size and symmetry (swapped to
   another valid kind 25% of the time); scale its group and altar counts to the new area; keep its spawn size and
   relative position (moved into the authored half when it would cross the mirror line).
3. **Terrain:** tile the authored half with square patches (6–14 wide, random flip/rotation) cut from the template
   and its two official maps nearest in wall/bush/hole density. Local structure is real; the arrangement is new.
4. **Camps:** 70% of groups are the template's own official groups and 30% come from the pool of all official groups,
   with exact member types and relative layout (Golem and monolith groups appear as they do officially).
5. **Checks:** engine integrity, the game loads the map, every altar and camp is reachable on foot from spawn.
   A failed attempt retries the same template, so no map style is under-represented.
6. **Gameplay screen:** v58 plays itself on both sides of every map (`profile_maps.py`; same bot on both sides, so it
   reveals nothing about any candidate). A map is rejected for any fault, or if rounds, winner's gems, total banked
   gems, deaths or fuel-outs fall outside the range seen on the official maps (`screen_maps.py`).
7. **Selection:** 50 maps are drawn from the accepted ones by importance resampling on gameplay (a logistic
   regression's density ratio official/generated), correcting the generator's residual tilt toward shorter games.

`adgato-gemcombat1`–`5` are kept in the 70-map suite but are not used as generator sources: they have no gold and no
monsters (gem clusters only), a mini-format unlike the sprint maps.

## Validation (`realism.py`)

Official 65 (generator sources) vs the selected 50, v58 mirror games:

| Check | Result |
|---|---|
| Classifier separating official from generated layouts (cross-validated AUC; 0.5 = cannot tell) | **0.51** |
| Gameplay two-sample KS (rounds, winner gems, total banked, deaths, fuel-outs); 5% critical value 0.255 | all below (max 0.208) |
| Layout KS (area, terrain densities, groups, camps, gems, gold, camp-type shares, symmetry, team) | all below except gems per area 0.258 |
| Median game length, official vs generated | 1,181 vs 1,146 rounds |
| Faults | 0 in 140 official and 100 selected generated games |

Calibration history: batch 1 (uniform group pool) AUC 0.61, 20% fewer camps; batch 2 still gem-poor and biased to
large maps; batch 3 (template groups, template retries, spawn relocation) layout AUC 0.49 with games about 15% shorter
than official; importance-resampled selection fixed the game-length shift. Reports: `research/maps/realism_*.json`.

Limits: realism is measured with our own bot (v58 mirror); maps designed by people may contain set pieces (boss gates,
single sole-gem camps) that patch-and-group resampling reproduces only when a template's groups carry them. The
generated maps reuse official components, so they are related to the official set, not independent of it.

## Regenerating

```bash
python tools/mapgen/extract_official.py                                   # official layouts -> research/maps
python tools/mapgen/gen_maps.py --out artifacts/local-only/maps-new --count 150 --seed 5 --exclude adgato-gemcombat1 ...
python tools/mapgen/profile_maps.py --a artifacts/tmp/v58.wasm --maps artifacts/local-only/maps-new --out artifacts/evaluations/mapprofile-new
python tools/mapgen/screen_maps.py --official-profile research/maps/profile_official_v58mirror.json --gen-dirs artifacts/local-only/maps-new \
    --gen-profiles artifacts/evaluations/mapprofile-new/profile.json --out-dir <dir> --partitions <suite.json> --target 50 --exclude adgato-gemcombat1 ...
```

The map tools need the `wasmtime` Python package and the engine 2.0.0 map-editor wasm, which any cambc 4.0.0 build
unpacks into `%LOCALAPPDATA%/cambc/assets/*/mapeditor/assets/`. `realism.py` and `screen_maps.py` need scikit-learn.
The suite in this commit came from seed 4 (batch 3) and selection seed 120.
