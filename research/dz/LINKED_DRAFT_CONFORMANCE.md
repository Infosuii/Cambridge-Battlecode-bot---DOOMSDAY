# Linked bodies and missed draft picks — 2026-10-29

Production source is unchanged from the low-fuel checkpoint. These are isolated
correctness probes, not strategy or strength experiments.

## CT-19

`dz-ct19-linked-cassi-02` and `dz-ct19-linked-issac-02` pass four full native
games on the separate isolated-monolith map, both sides. One linked body stands
adjacent to the monolith and attacks; the other parks outside every damaging
camp's range at full health before combat begins. All unrelated bodies park.

Both linked bodies die in the **same exact native timeline event**. The reader
compares event indices, not just round/phase labels. Both return 60 rounds later,
each at its own champion turn; simultaneous death does not imply the same respawn
turn. Cassi-initiated death is R33→93, Issac-initiated death R35→95. Every recorded
observer liveness view matches native state (93/95 views per cell, no mismatches).
The full summaries report zero native faults/fuel-outs.

The initial 01 runs also pass but only compare round, phase and turn for linked
death. The 02 reader adds exact event identity. The reader and official loader are
frozen and hashed in each capsule. LIFECYCLE_READER_REGRESSION.json separately
checks that the new reader preserves all four earlier hidden-death results using
their existing native replays, without rerunning engine games.

## CT-20

The following final runs pass 12 complete native cells with zero faults/fuel-outs:

- `dz-ct20-draft-miss-02`: first pick omitted, 3/5-pick maps, both sides.
- `dz-ct20-draft-miss-second-02`: second pick omitted, same maps/sides.
- `dz-ct20-draft-miss-four-02`: first pick omitted, 4-pick fixture, both sides.
- `dz-ct20-draft-miss-four-second-02`: second pick omitted, 4-pick fixture/sides.

In these cases, after a missing pick the draft guest is not resumed for later
draft rounds. The engine completes the remaining roster. Existing selected picks
are retained. The probe authenticates the saved draft prefix against every
spawned body's type, team size and shared marker. It does not assume particular
autofill choices or their distribution. Linked picks still create two bodies.

A successful `draft::pick()` does **not** immediately appear in a same-turn
`current_draft(ally)` read. The list commits by the next draft turn. The second-
skip tests establish this with a known first C&I pick, its delayed list entry,
saved shared prefix and both resulting bodies. Production's rule remains: pick
before optional work, and read the committed prefix on the next draft turn.

Retained failures: first 01 wrongly expected to resume drafting after one
autopick; second-01 wrongly expected immediate list visibility after pick.
Both failed their assertions and were preserved. Later tests explicitly assert
the observed timing and complete roster rather than labeling quiet output a pass.

Remaining CT-19/20 scope includes explicit priority-change timing and omissions
at later draft positions; these results do not establish those cases. No draft
strategy change or map-specific plan was introduced.
