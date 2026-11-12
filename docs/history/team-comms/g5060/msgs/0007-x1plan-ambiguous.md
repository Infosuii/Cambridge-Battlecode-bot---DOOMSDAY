# 0007: --set X1_PLAN=... fails on x3 (ambiguous define); fixed in my dz.py

bots/x3/src/x1_config.h defines X1_PLAN twice (line ~102 default, and `#define X1_PLAN 1` inside `#if X1_COUNTER`), so
tools/dz.py's --set found 2 matches and raised "unknown or ambiguous define: X1_PLAN": every J025 line (mfp6, mfp8,
mfp2l) failed at once (no games). Fix on build/z-plan-5060 bea45114: --set replaces the first #define only (the
default; later ones sit inside #if blocks). Suggest the same in build/z-plan's tools/dz.py, or rename the second
(e.g. `#undef X1_PLAN` + define via a different macro). J025 is re-running now with the fix.
