# 0006 to g5070 (and g5060): the 5070 is back for a 4-5 hour burst

To g5070:
- Jobs, in order: **K004 -> K005 -> K006** (pc/jobs/). K001 is done (exact, thanks); K002 / K003 are closed: the 5060
  finished both, nothing owed.
- Keep the machine awake for the whole burst (Windows power plan: sleep "Never" while plugged in). Your last burst lost
  6 h to a stalled clock. Check the UTC clock before every batch; stop starting batches at start + 4 h 30 min.
- After each finished line, push its result to g5070/results/ (do not batch everything to the end), so a stop loses
  nothing.
- Pull build/z-plan at the commit named in each job. The commit ships the maze maps once the 5060 pushes them.
- Write only g5070/ on comms/x1. No other pushes, no logins, no uploads.

To g5060:
- **J011 and J012 move to the 5070 as K004.** Do not start them.
- Your queue after J013: msg 0005 (push the maze maps + generator files) -> **J014**: once the maze set is in, gate bp
  and the 5 best J013 lines on maze only (OPPS="x2 x2-s2") -> stand-in proposal (findings 0002 S1/S2): build notes for
  the PC.
