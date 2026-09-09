# TODO

## KOF

Why the two KoF games are still the least trainable rosters: 71% for `kof98`,
63% for `kof2001`, against 74-89% for the others. No whole character is missing
in either — every skip is something the engine has no model for.

It is not the Neo Geo panel or the author. `ssvsp` is the same panel and the
same author and reaches 74%, because Samurai Shodown asks for plain motions and
lists few follow-ups. What is left is structural and not worth chasing:

- **Close command throws** (`b/f + C when close`, `N>4/6+C`). The engine has no
  "one direction _or_ the other, plus a single button" throw, so these produce
  no direction requirement at all. Same reason the SF games skip their
  non-two-button throws. Every character has two.
- **Follow-up chains and stances.** Both guides list each follow-up as its own
  line (`_236+P`, `from X`), and 2001 goes much further — Vanessa's Puncher
  tree alone is ~22 lines. Correctly non-trainable, and they still show in the
  move list struck through.
- **Direction ranges** (`A>1~3+D`) and stance switches (`ABC`), 2001 only.

### Compound super motions — done

`qcf~hcb`, `qcb~hcf` and `hcb,f` are now `MotionKind.QCF_HCB` / `QCB_HCF` /
`HCB_F`, worth 76 moves across the two games ('98 63% → 71%, 2001 57% → 63%).

The two halves share the direction they meet on, and the doubled direction the
'98 numbers used to show was ours, not the guide's: '98 writes `qcf,hcb` and
`normalise._SHORTHAND` used to expand each shorthand separately, giving
`d,df,f` + `f,df,d,db,b`. 2001 is numpad and writes `2363214` =
`d,df,f,df,d,db,b`, sharing the forward. `_expand_shorthand` now walks a whole
run of shorthands and drops a repeat at the join, so both guides reduce to one
tuple:

| motion  | canonical tuple    | '98       | 2001      |
| ------- | ------------------ | --------- | --------- |
| qcf~hcb | `d,df,f,df,d,db,b` | `qcf,hcb` | `2363214` |
| qcb~hcf | `d,db,b,db,d,df,f` | `qcb,hcf` | `2141236` |
| hcb,f   | `f,df,d,db,b,f`    | `hcb,f`   | `632146`  |

Only the join is collapsed, so a literal `d,d` still means two presses.
`qcf~hcb` and `qcb~hcf` take the doubled window (`_DOUBLE_MOTIONS`) and rank
just under the x2 supers; `hcb,f` follows `QCF_UF` — one window, one direction
appended — and has to outrank the plain `hcb` and `qcf` its tail contains.

Still unmodelled, and small: `d,d` (5 moves, all games), `f,f`, `db,f`,
`b,f,d,df`, and a handful of one-offs.

## Timings

Not sure when the ai got it's information from, but need to see if there is a way to get input timing into each game

## Super activation time per game

- For Mash / tap tap tap supers, the delay between activation starting and mashing needs to be entered as inputs during the cinematic are dropped. Manually measure each game. In a comment for each game state the source whether its guessed or was part of the prompt.

SFA3: TKTKTKTK
SFIII3: TKTKTKTK
USFIV: TKTKTKTK

## Tekken 3

This will be difficult, https://gamefaqs.gamespot.com/arcade/563192-tekken-3/faqs/979
