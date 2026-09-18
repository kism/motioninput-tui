# TODO

## Timings

3S is accurate, getting real numbers for any other game would require either annotated disassembly or decompiled code that doesn't currently exist. Another method would be using mame lua and memory editing to figure it out.

The same goes for `chain_window_ms`, which is reckoned at 700ms for every game that has chains wired. Nothing has been measured; it is long enough to roll a deliberate quarter circle out of the move before and short enough that a string doesn't outlive its animation, which is a guess dressed as a number.

## Tekken 3

This will be difficult due to the combo structure instead of motion input, <https://gamefaqs.gamespot.com/arcade/563192-tekken-3/faqs/979>

## Chains in the remaining guides

`Move.follows` is wired for every roster whose guide names the parent — 221 links across eight games, 194 of them runnable. Two shapes cover it: the SNK guides name the parent first (`neogeo.split_parent`), the Street Fighter ones put it last (`common.split_trailing_parent`), and Martial Masters indents a link under its parent.

What is left is 49 moves, and each needs something other than a better splitter:

Three are guide typos, where the command names a parent that is one letter off the move it means — Juzo Kanzaki's `Iwakudai` for `Iwakudaki`, Naoe Shigen's `Konogosai` for `Kongosai`. These want an override table keyed the way `commands.py` is, or fuzzy matching, which is a third rung the current two-pass match deliberately stops short of.

Seven name the parent by an abbreviation the roster does not carry — Cammy's `after H.C.`, R. Mika's `after S.B.S.`, Dan's `during C. Shinwa`. An alias table per guide would do it.

The rest genuinely describe a condition rather than a parent: `While getting up`, `Jump against a wall`, `against a back-turned opponent`, `Hold and release PPP`, `when near a knife`. Those are mechanics the trainer has no model of and are right to stay struck through. Sailor Moon S, Samurai Shodown V Special and Hyper SF2 have no chains at all, which is correct for those three.

The `then` shape is handled: a command written as another move's command again with what to do next on the end (`qcf,uf + P, then press P`) is matched on the command text rather than a name. That turned out to be only four moves — Akuma's three off his Hyakki Shuu dive, and Bison's Somersault Skull Diver off his Head Press — not the 43 an earlier count suggested.

The other 24 commands carrying `then` are not chains at all: they are one move plus an extra press the engine has no model for (Rufus's `qcf + K, then K`, Rolento's Mekong Deltas). The head is the move's own input, so parsing it and dropping the tail would make 11 of them trainable. That is a separate decision, because it means calling a move trainable on a deliberately partial reading of its command — the thing `commands.py`'s docstring warns about — and two of the 11 would then share an input with a move the character already has. The rest of the 24 open with `Hold P`, `Block b / db` or `Jump u or uf`, which the trainer cannot read either way.

## Sequences of presses

15 moves are struck through as "a chain of presses, which the trainer has no model for": Akuma's Raging Demon (`LP,LP,f,LK,HP`) in three games, Guy's Bushin strings, Drunk Master's target combo. These are a real input shape — buttons in order, sometimes with a direction between — and the engine has no `MotionKind` for one. Until it does they must not fall back to "press all of these at once", which is what they used to do and which is a move none of these games have.

## Motions not in the table

121 moves are skipped as an unrecognised motion. Some are genuine one-offs not worth an entry; a few are real shapes the table just lacks, such as `b,d,df` (Monkey Boy's Monkey Stomp, two moves). Each needs a `MotionKind` and a matcher, so they are worth adding only where more than one character wants one.

## Held buttons

Two moves are struck through because the guide says to hold the button rather than tap it, and every press is momentary to the engine. Yuri's `d, df, f + hold P` is otherwise indistinguishable from the plain fireball listed above it.
