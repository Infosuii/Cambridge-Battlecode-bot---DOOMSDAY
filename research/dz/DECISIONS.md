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
