# EXP-013 implementation freeze — One-turn banking before an ordinary hunt

In v92, `bot.cpp:7614` invokes `hunt()` before `tribute_if_needed()`. Farming is already after tribute. On an ordinary hunt the bot walks toward a recent enemy sighting at `:4492`. Keep rescue, snipe, direct combat and home priority intact.

Measure the intersection, through round 300, of an executed ordinary hunt and an otherwise eligible one-round small-bag deposit. At hunt entry require 1–10 gems, no visible enemy, no awake camp threatening the position, no prior movement, an already-ready altar field at zero distance, the existing banking guards clear, and an altar in submission range without an enemy lock. Exclude enemy sightings within four tiles over the past three rounds. SDK guards and a probe of observations do not prove that the channel would succeed.

Use the frozen 16-map conformance set, both sides vs v92 and x3inv. A charged diagnostic calls the original hunt once and logs a qualifying intersection only when its resulting mode is `hunt`. Report affected cells and bag size. A clean candidate requires recurring opportunities in at least two independent map cells. Preserve its priorities and banking guards, freeze the implementation before the pool, and stop on any local veto.
