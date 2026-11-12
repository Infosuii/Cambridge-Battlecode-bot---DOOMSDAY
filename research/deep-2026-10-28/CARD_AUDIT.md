# Targeted card audit

The105 generated cards and their event-label table were checked for cohort,
window, actor, outcome and prediction provenance. This is a descriptive screen;
every card is not an exact source trace. Each card has at most25 lines. Expectations
were frozen before subsequent actions; adding previously omitted action kinds
did not change those expectations or the model windows.

The nine cards with the public V75_LONE prerequisites were read alongside the
source guard and recorded follow-up. They illustrate different situations:

| Card | Observed focus behaviour | Interpretation still requiring a trace |
|---|---|---|
| C004 |736-gem carrier, visible threats, moves and attacks, then dies|Trace whether escape was already forced, one-turn-kill exception, kStand2/tactical search and bank route. No nearest-state control passed the caliper.|
| C017 |97-gem carrier moves, recalls and survives with the bag|A losing-game model drop can coexist with sensible focus behaviour; opponent economy dominates this window.|
| C018 |46-gem carrier moves and attacks amid visible enemies, then dies|Sustained fight versus attack weaving while fleeing is unresolved.|
| C030 |43-gem carrier starts at330/1100 HP with visible threats, then dies|The window also includes shopping and another ally's death; do not assign the whole drop to the focus.|
| C034 |343-gem carrier on00vault moves/attacks, then dies|A same-map winning control banks343 gems later in a similar aggregate state, but this is neither an exact same position nor a feasible-action proof.|
| C048 |56-gem carrier on00galaxy repeatedly attacks/moves, then dies|Effective retreat and path constraints need reproduction; source defaults alone are insufficient.|
| C069 |Low-HP focus moves without a visible-enemy-target attack, then dies|The same visible danger can be fatal even when the focus attempts escape. Suppressing attacks cannot explain every case.|
| C070 |Low-HP focus casts/attacks/moves, then dies in a repeated-death window|Native repetition is measured; route/memory/configuration and actual escape feasibility remain unknown.|
| C099 |Control win: focus moves away and survives the window|A visible local health disadvantage is not itself a loss prediction or a bug.|

C082 is the other repeated-death-labelled selected loss window. Its focus carrier
is healthy and travelling; a **different** own champion dies. Its team-level D3
label must not be attributed to the chosen carrier's decision. Session3 should
reconstruct the victim's own turn history when investigating that death.

All six cards with a guard prerequisite and later visible-enemy-target action
are losses (C004/C018/C030/C034/C048/C070). This selected, tiny comparison cannot
show that the source guard failed: attacks may be legal while fleeing, spell
targets can differ from target intention, and the one-turn-kill exception is
not evaluated by the card tool. No confirmed error or counterfactual gain is
claimed. None of the source changes previously rejected in the repository is
revived by these cards.

The79/90 selected loss windows with an opponent purchase and63/90 with an enemy
camp receipt are event associations, not79 shopping bugs or63 capture mistakes.
Nearest winner controls are broad aggregate matches; only32/105 top-winner
controls share the map. Those limitations materially constrain transfer claims.
