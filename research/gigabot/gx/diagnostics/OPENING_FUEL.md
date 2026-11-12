# Fuel diagnostics and first repairs

The instrumented 12-game sample locates recurring suspension sites; it is separate from the release comparison. All 36 round-one suspension markers fell in field construction. The runtime also recorded nine markers at siege cache setup and two at the sight scan.

- Field guard mode 2 limits first-turn field work on larger maps and checks the cost of preparing the group order before sorting. It cut round-one exhaustions from 84 to zero and total exhaustions from 548 to 442. It scored 337/516, four wins below baseline, with no faults. Keep it as an engineering option for combinations.
- The siege variant allocates each camp mask lazily and uses precomputed integer ray offsets. The host compatibility check verifies all offsets near map edges and in the interior. The release scored 328/516 with 446 fuel-outs and zero faults. The cheaper path alone did not increase strength.
