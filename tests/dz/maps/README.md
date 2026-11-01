# Controlled engine fixtures

These mechanics maps are separate from the 70 competition maps and are never
used for strength comparisons or per-map parameter selection.

`isolated-monolith.map26a`: open 31×31 ground, three picks, rotational symmetry,
3×3 spawns, central altar, one monolith per side. No bushes, walls or neighboring
damaging camps obscure the target. The official engine's MapBuilder encodes the
map and verifies its integrity. The manifest records geometry and hashes.

`opening-crew.map26a`: mirrored three-pick opening, twelve connected gem clusters
and a Golem guarding a single altar entrance with several outside attack poses.
This checks carried-stock opening/delivery and crew entry, not competitive
strength. `opening-crew.manifest.json` pins its generator, official assets and map.

The committed binary is sufficient to run tests. Regeneration needs Node and
the pinned official assets used by the replay tools; use a fresh destination:

```powershell
$env:NFS_REPLAY_ENGINE='2.0.0'
node tools/dz_make_fixtures.mjs artifacts/tmp/new-fixture-output
python tools/dz.py conformance --name fresh-monolith-check --fixture camps --set DZ_MONOLITH=1 --map-dir tests/dz/maps --maps isolated-monolith --diagnostic-rounds 70
```

Generation never overwrites files. Custom map directories are accepted only by
`conformance` and `scenario`, and do not alter the competition pool.
