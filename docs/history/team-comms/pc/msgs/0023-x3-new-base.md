# 0023: new base x3 (= v92)

To: g5060

Your K010 A showed v92 beats x1 / x1c1 locally; its real-ladder record (751-539 while live, 0xDEADBEEF 17-63 vs
x1c1 0-25, Borufeczki 19-11, Shawn 68-42) confirms it is our best ladder bot. bots/x3 = v92 patched onto x1 (default
build byte-identical to v92, 5704d7ba41ac), so all x1 switches work on top of it. The ship base is x3 from now on.
New gate set `pool` in tools/x1_gate.sh = maps/ladder-pool (the current 86-map competition pool incl. the 03 maps;
v92's per-map fit only covers the older 70). Run pc/jobs/J018-x3-addons.md next; rebase I-60-04 onto x3.
