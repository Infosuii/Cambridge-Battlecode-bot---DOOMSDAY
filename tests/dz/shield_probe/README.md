# Stationary shield conformance probe

This tests the real DZ shield_clear.h on existing isolated native-engine maps.
The runner copies the current header into each frozen probe build. It never
changes the production controller or trains a map policy.

```
python tools/dz.py conformance --name FRESH --fixture shield --map-dir tests/dz/maps --maps isolated-wolf isolated-elk isolated-golem isolated-monolith --diagnostic-rounds 160 --set DZ_SHIELD_HEART=1
```

Omit the override for Varg. The subject uses a fixed adjacent tile and basic/
reset/shield priority; other bodies remain at their actual spawn positions.
Initial and existing-shield quotes must match outcome, elapsed rounds, HP loss,
attack and cast counts, with isolation enforced throughout. Duplicate assertion
names combine with AND. Missing or unmatched quotes/results fail the parser.

These are truncated primitive conformance tests. Native fault totals are not
measured, and mirrored/overlapping windows are not independent. See
research/dz/heart-mechanics-2026-10-30 for preserved failures and field limits.
