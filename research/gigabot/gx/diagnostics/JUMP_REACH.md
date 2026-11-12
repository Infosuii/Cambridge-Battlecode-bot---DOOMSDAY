# How much terrain access can jumps add?

Compared walking, the stock single-hole overlay, and geometric two- and three-tile jumps using actual camp groups on all 86 layouts and both sides. The jump graph ignores sight, occupied landings, cooldowns and hostile units, so its reach is an optimistic geometry measurement.

Only 11 layouts have any additional gem access under repeated three-tile jumps versus walking. Eight are already covered by the stock one-hole overlay in this model. The extra gem access is 35 on 00quadrants and 14 on 02guardians for two-tile jumps, and 62 on 03membrane for three-tile jumps. Islands itself needs repeated jumps: a single jump reaches 340 of 608 gems while both the stock overlay and repeated two-tile jumps reach all 608 geometrically.

A large replacement of the ordinary pathfinder targets little added coverage. Try a bounded fallback when a goal really is unreachable and an immediate or nearby usable jump connects the regions. Treat the launch search, visibility, channel risk and the engine's move result separately. See [gateway-geometry.json](gateway-geometry.json).
