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

## Timings

Not sure when the ai got it's information from, but need to see if there is a way to get input timing into each game

## Super activation time per game

- For Mash / tap tap tap supers, the delay between activation starting and mashing needs to be entered as inputs during the cinematic are dropped. Manually measure each game. In a comment for each game state the source whether its guessed or was part of the prompt.

SFA3: TKTKTKTK
SFIII3: TKTKTKTK
USFIV: TKTKTKTK

## Tekken 3

This will be difficult, <https://gamefaqs.gamespot.com/arcade/563192-tekken-3/faqs/979>
