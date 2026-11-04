# EXP-115 matched greedy fallback

The diagnostic reproduced Vendetta's original draft, visible input, actions and all six native suspensions. The greedy fallback began enumerating 7,796 goal tiles with 13,080 fuel, reached the end in R1083, and found its nearest goal at distance three. The pinned SDK implements `positions()` by allocating and filling a vector of all set tiles. [Exact samples](CPG_CONTINUATION_GREEDY.json).
