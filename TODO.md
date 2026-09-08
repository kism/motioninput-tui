# TODO

## KOF

Why the two KoF games are the least trainable rosters: 63% for `kof98`, 57% for
`kof2001`, against 78-89% for the Street Fighter games. No whole character is
missing in either — every skip is something the engine has no model for.

Most of it is structural and not worth chasing — it outnumbers the motion gap
below better than two to one in '98 and nearly three to one in 2001:

- **Close command throws** (`b/f + C when close`, `N>4/6+C`). The engine has no
  "one direction *or* the other, plus a single button" throw, so these produce
  no direction requirement at all. Same reason the SF games skip their
  non-two-button throws. Every character has two.
- **Follow-up chains and stances.** Both guides list each follow-up as its own
  line (`_236+P`, `from X`), and 2001 goes much further — Vanessa's Puncher
  tree alone is ~22 lines. Correctly non-trainable, and they still show in the
  move list struck through.
- **Direction ranges** (`A>1~3+D`) and stance switches (`ABC`), 2001 only.

The one worth doing is **KoF's compound super motions**, which are absent from
`normalise._MOTION_TABLE` and the engine's `_SEQUENCE_BUILDERS`. Between the two
games they cost **131 moves**:

| motion | kof98 | kof2001 |
| ------ | ----- | ------- |
| qcf~hcb | 18 | 16 |
| qcb~hcf | 12 | 12 |
| hcb,f | 9 | 9 |
| d,d | 6 | 6 |
| others | 13 | 30 |

Note the two guides spell the same motion differently — '98 writes qcf~hcb as
`d,df,f,f,df,d,db,b` (the forward repeated at the join), 2001 as
`d,df,f,df,d,db,b` (shared) — so the table needs both forms, or the matcher
needs to tolerate the doubled direction.

Adding just the top three families would take `kof98` to ~71% and `kof2001` to
~63%. It is a shared-engine change with its own test surface, hence still here
rather than done.

## Timings

Not sure when the ai got it's information from, but need to see if there is a way to get input timing into each game
