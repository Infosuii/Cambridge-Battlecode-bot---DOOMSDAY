# K014 preflight: A3_ITEMS override appears shadowed

K011 accepted per PC 0035; K014 is running on Linux x3mf with own baseline 96/115/130. No bot edits.

Source at 9c1bbde: common.h defines A3_ITEMS unconditionally to 0 at line231, then has a guarded fallback definition at line250. dz.py --set common.h support appends `#define A3_ITEMS ...` to x1_config.h, which common.h includes first. The unconditional line231 then overrides the requested value. The guarded fallback is never used.

I will run/report the supplied row26 builds exactly as instructed and report measured hash equality or changes. I will not repair the source inside K014. This note is an early source-backed heads-up for PC review, not a claim of a measured A3_ITEMS result. Avoid changing active benchmark source inputs; any later fix should be isolated and retested explicitly.
