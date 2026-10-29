# DZ implementation decisions

2026-10-28: The user's current request authorizes building a pure algorithmic bot and creating a
portable repository branch. Historical planning text saying "awaiting approval" is superseded.
Commit and push checkpoints of this work to enable fresh-system continuation. Do not commit the
pre-existing `config/paths.json` edit, generated compile commands, or unrelated artifacts.

- Implement fresh C++ in `bots/dz/src`; use only the official SDK and standard library.
  Previous bots are benchmark opponents only. Evaluation tools can be reused.
- Target the current 70 maps, as confirmed by the user. Read-only top-team replay downloads are authorized.
- Start with Z1–Z4 walking skeleton and a partial Z0 suite. Models stay disabled until validated.
- All action mutations belong to Actuator. Check the captured round after expensive reads and before
  each mutation. On stale resumption restart immediately, without yielding away the new round.
- The research protocol sketches cannot detect an unchanged slot's age from its bits. Do not invent
  freshness or death timers from unchanged values. Use claims as soft hints until a tested protocol
  extension exists. Draft initializes every slot to IDLE so the zero word is never interpreted as group 0.
- Group indices >=112 publish IDLE rather than aliasing group 111. Internal indices remain unrestricted.
- Sighting parity and crew TTL alone cannot prove message age. Team messages stay disabled in v0.
- Advanced auction/ObjModel/EE/gear/opening remain future gated modules, not claimed implementations.
- v76 is the local comparator; final fallback selection remains the user's decision.
- No submit, activate, unranked match-group creation, or ladder duel without separate authorization.

Implementation results: `RESULTS.md` and `CONFORMANCE.md` distinguish observed facts,
working starter behavior, incomplete conformance and unvalidated future models.
The user explicitly approved the named GitHub push after the initial automatic
approval review requested destination/payload authorization. The branch is published.
Support evidence was added so fresh agents have raw calibration replays rather than
only reports. The one-time 04:07 London continuation fired on 2026-10-29 and its
automation was deleted after delivery. No scheduled continuation remains.

## Subsequent engine corrections

The supplied planning sketches are not executable authority. Controlled engine
checks override their hypotheses; read CONFORMANCE.md for exact scope/evidence.

- Camp attacks occur every round in the tested wolf/elk/golem/monolith fixtures.
  The proposed half-rate would substantially underpredict incoming damage.
- Hidden champion liveness can be queried, including death and respawn. Hidden
  health still rejects 97. The public bundled SDK has no champion respawn-timer
  wrapper/import. Observe liveness transitions rather than inventing one.
- Respawn occurs at the champion turn, 60 rounds after death in the controlled
  native timeline. Another champion can observe the change later in the round or
  next round; a first-observed death is not automatically an exact death timestamp.
- Uncaught exceptions restart the guest. A local static counter resets, the main
  function re-enters, and shared team memory persists; the champion remains alive.
  The permanent-inactivity hypothesis was wrong. Catching failures preserves
  local map memory and avoids repeated startup. A restarted bot clears its own old
  shared claim before rebuilding map state, and splits an ordinary-budget cold
  start across turns.
- Fatal-turn stdout can be lost. Native fault events determine fault count/time;
  diagnostic prints alone cannot establish the absence or number of faults.
- Home recall takes three ticks versus five base ticks. Health purchases on spawn
  heal by the maximum-health gain immediately; ordinary spawn healing follows.
- Multiple assertions with one name are combined with AND. A later passing result
  must never overwrite an earlier failure. Prior passing transcripts are audited.

- CT-19: both linked bodies die in the same exact native event, including when
  their partner is parked safely at full health. Respawn remains at each body's
  own turn, 60 rounds later in these fixtures.
- CT-20: a missed first/second pick stops subsequent guest drafting and the engine
  fills the remaining roster in the tested 3/4/5-pick cases. An own successful
  pick appears in the committed list on the following draft turn, not immediately.
  Preserve pick-before-optional-work ordering; do not predict autofill choices.

- CT-13 reward correction: Prospector boosts gold clusters as well as gem
  clusters. Its tested gold effect combines multiplicatively with Vesper. The
  supplied objective formula omitted this gold benefit.
- Vesper's tested gold increments require cumulative fractional-bonus carry:
  reversing wolf/gold awards moves the extra unit to the later event. Do not
  floor each event independently, or infer a hidden remainder without its prior
  reward history. Internal storage, other stacking and death behavior are open.
