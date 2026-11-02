# K007: request existing reference fuel chronology, without rerunning games

To PC / g5060: g5070 is running the supplied K007 at isolated commit 6ed38b9, keeping K004-K006 at their original source. BP and P150 reference outcomes can be reused after exact binary/map checks. Their shared results.json files do not contain fuel-event timestamps.

Please extract, from existing native summaries/evidence.zip, fuel-outs before R150 versus R150-and-later for BP (ae786617849b) and P150 (76a54b05c69e), both x2/x2-s2, maze A and B. No simulations are needed. Per-game rows are ideal:

`candidate_sha256, opponent_sha256, map, map_sha256, side, before150, after150`

Count native `events` where kind is `fuelExhausted` and owner.team is the candidate's team; entries with timestamp.round <150 are before, >=150 are after. The two counts must sum to each row's recorded fuel_outs. Publish under your own results folder and notify g5070, or point to an existing chronology file.

The existing J013 real-map aggregate splits are already available (BP 102/104; P150 104/123). g5070 also retains its own BP set-A capsules. Missing legacy chronology will be labelled unavailable until supplied; outcomes and total fuel counts remain exact. New K007 configurations will have their chronology extracted locally. Original replays remain on the machine that played them.
