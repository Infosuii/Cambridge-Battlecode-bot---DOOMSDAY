# Map features from live camp groups

The map editor provides terrain, spawn and altar geometry. Some groups cross the symmetry boundary or are assembled differently when the match loads. Expanding authored groups by mirroring each shape gives the wrong count or gem total on 35 of the 86 pool maps.

The diagnostic draft bot reads the public camp groups on both sides. Both sides agree on every layout, and all 86 group counts and gem totals match the recorded runtime fingerprints. `map_geometry.json` uses those live groups with terrain distances, altar access, spawn distances, centre share, jackpot share, disconnected gem share, narrow tiles and bush cover. Distances are static estimates; enemy control and live camp occupation are separate.

Notable cases: 01islands has 61% of its gem value inaccessible from spawn by ordinary walking, 02the-pond has 47%, and 03ultrastarvation has 39%. 01boss-battle and 02guardians have no reachable ordinary altar access in the static estimate after camp tiles are removed from the altar ring. These are possible regime boundaries, not evidence that a selected strategy wins.
