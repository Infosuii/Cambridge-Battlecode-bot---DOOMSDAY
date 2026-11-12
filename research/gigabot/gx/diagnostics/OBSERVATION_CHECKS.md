# Camp observation checks

Both catalogue builds reproduce 5704d7ba41ac with the catalogue off. The first format reconstructed the native group list, member IDs, positions, types and rewards on five layouts, and fell back on the-front (166 camp members). The second format uses two bytes for a tile and its type on maps with at most 4,096 cells. It decoded every record on the-front as well. Both teams and every initialised champion agreed on the six selected maps. These were conformance games with zero reported bot faults; their win records do not establish strength.

The hidden-camp probe deliberately called the health API when the group was visible but an individual camp tile was hidden. The omitted lookup never succeeded in the six sample games, and both sides exercised the branch on every map. The production switch skips only these calls.

The capture probe read 2,158 visible reward states, including 1,273 ally captures and 30 enemy captures. Its reported timers span the countdown observed during active capture. The release variants either hold a safe capture close to completion or use the remaining time in the camp scorer. Neither will assume a countdown for an unseen group.
