# Farming as production, ownership and delivery

The relevant cycle is travel → kill every group member → occupy the reward region uncontested → receive a share → survive and convert. A fast clear without capture is unfinished work. A collected bag without a viable altar route is an uncertain asset. All direct opening targets and capture receipts by body are in FARMING_ROUTES.csv; they must be joined by match/group ID, not compared as if group 7 on two maps were the same camp.

Current camp definitions range from harmless 120-HP clusters to 20000-HP monolith bodies. Group HP/rewards are summed over all members; boss_battle group 16 has two monoliths and 40000 HP, 600 gold, 400 gems. Neutral rewards and terrain must therefore be read from the actual group definition rather than a single monster prototype.

Captures start a five-round timer, with Capture capping remaining time at three. Extra allies without the emblem do not accelerate it. Empty or contested regions reset progress. The finishing allies share the rewards, with a deterministic lowest-ID remainder. After claim, the group respawns using the longest member cooldown, and an occupied spawn tile delays the entire group. These mechanics support separate clearers and receivers, but travel and lost attacks can erase a funnel's advantage.

## Observed mechanisms

On swirl, Trzy Kwaterki's Vesper becomes the dominant receiver/output source:13455 gold and 820 score. On eight, a Marcella rather than Vesper carries the scoring engine. On boss_battle, a different division is necessary: a scaling Prism helps secure access while Varg and Vendetta convert. A single fixed definition of the carry would misassign at least one of these cases.

On elk_arena, all five procless bodies open Prospector. Vesper completes it at R61, but the entire plan takes many cycles to convert: both teams have 72 score at R500, before procless finishes 1046–144. On expanse the winner has less R500 gold/equipment yet wins the race. On rows it wins with less total gold and fewer gems. These counterexamples make gross gold rate an incomplete optimisation target.

Native monster damage and direct camp basic attacks are measured separately from income. Earned gold includes kills and Marcella bank income; it is not labelled capture income. Moved boundaries include all observed displacement and are not exact travel cost. Channel presence overlaps useful movement because several elite controllers cancel/restart recall around actions. Stationary boundaries include attacks, captures and productive waiting. None of these proxies should be called avoidable idle time.

## A useful objective value

For a candidate group and coalition, estimate feasible travel time, damage-limited clear time, expected HP expenditure, capture delay and delivery time. Value delivered gems and strategic access, plus the marginal future output of gold, then subtract death/bag risk and opportunity cost. Compare rates only over a consistent horizon. An objective with lower nominal reward may win if its region connects to the next camp or altar without another return trip.

Split jobs when two safe groups can be completed concurrently with less total delay. Group when extra damage meaningfully reduces clear time or makes a dangerous camp survivable. Leave only the required receiver(s) when extra allies neither accelerate capture nor improve reward value enough to repay their lost activity. A Capture holder can join to shorten the timer and then leave while another ally maintains the region; whether a particular elite action deliberately does this remains unproved.

Measure actual gem conversion, claim delay, camp/cluster income separately, useful shopping spikes, death downtime, and how often a completed clear is captured by another team. Route policies should be tested against unseen geometry, not tuned to the 30 maps in this descriptive study. Historical held-out pools have prior exposure and cannot be silently reused as fresh confirmation.
