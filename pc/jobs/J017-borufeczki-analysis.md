id: J017
title: INDEPENDENT analysis of x1c1's ladder games vs Borufeczki (and the other new opponents) (Rishik's request)
commit: build/z-plan head (data/ladder/x1c1/: 180 real-ladder games of x1c1 = ladder v76, 14:38-15:12 UTC;
        matches_x1c1.json, summaries.zip = cambc match summaries, replays/; tools/ladder_analyse.py builds a per-game
        table: python tools/ladder_analyse.py data/ladder/x1c1/matches_x1c1.json <unzipped summaries dir> out.json)
priority: FIRST, now. Post a STATUS.md line when you start.
Focus: the 35 games vs **Borufeczki** (15-20), then Shawn (8-7), SquidProxyLovers (5-5), Funky monkeys (6-4),
Nameless (1-4). Also bots/x1c1 (build 22e6067a4233) and bots/x1 for any local reproduction.
Questions: when and how are the Borufeczki games decided (collection, banking, gold, kills / deaths by round
100/250/500/end); what their draft and behaviour is; what differs between our 15 wins and 20 losses (maps, drafts,
side, early state); which of our behaviours lose the games; what you would change in x1c1 / x1 and why. Every claim
with numbers from the data (match ids for examples).
Blind: **do not read pc/analysis/ or g5070/analysis/ until your report is committed.** Write g5060/analysis/J017.md,
then post. The PC compares the three reports afterwards.
