# TODO

## Timings

3S is accurate, getting real numbers for any other game would require either annotated disassembly or decompiled code that doesn't currently exist. Another method would be using mame lua and memory editing to figure it out.

The same goes for `chain_window_ms`, which is reckoned at 700ms for all three games that have chains wired. Nothing has been measured; it is long enough to roll a deliberate quarter circle out of the move before and short enough that a string doesn't outlive its animation, which is a guess dressed as a number.

## Tekken 3

This will be difficult due to the combo structure instead of motion input, <https://gamefaqs.gamespot.com/arcade/563192-tekken-3/faqs/979>

## Chains in the remaining guides

`Move.follows` is wired for Martial Masters, KoF '98 and KoF 2001 — 132 links. The rest are still struck through because their guides don't say which move a link comes out of in a way the parsers can follow.

Last Blade 2 is the cheap one: its 44 follow-ups are written exactly as KoF's (`Ittou Sogetsu: Ittou Shingetsu, f, d, df + B`), so calling `neogeo.split_parent` from its parser resolves 36 of them with no new mechanism. The other 8 name a parent whose roster entry is spelled differently, which `names.py`-style overrides or a looser match would pick up.

Samurai Shodown II gets 6 of its 21 the same way. The remainder are conditions rather than parents — `unarmed, b or f + B`, `while attacked, BCD` — and are right to stay struck through.

That leaves 156 marked "conditional or follow-up move", mostly Alpha 3 (64), USFIV (43) and 3rd Strike (25). Those describe the link in prose — `b / f + P after Head Press` — so finding the parent is per-guide text mining with a lower hit rate than either case above. Worth doing one guide at a time, and only where the parent is named rather than implied.

## Sequences of presses

15 moves are struck through as "a chain of presses, which the trainer has no model for": Akuma's Raging Demon (`LP,LP,f,LK,HP`) in three games, Guy's Bushin strings, Drunk Master's target combo. These are a real input shape — buttons in order, sometimes with a direction between — and the engine has no `MotionKind` for one. Until it does they must not fall back to "press all of these at once", which is what they used to do and which is a move none of these games have.

## Motions not in the table

121 moves are skipped as an unrecognised motion. Some are genuine one-offs not worth an entry; a few are real shapes the table just lacks, such as `b,d,df` (Monkey Boy's Monkey Stomp, two moves). Each needs a `MotionKind` and a matcher, so they are worth adding only where more than one character wants one.

## Held buttons

Two moves are struck through because the guide says to hold the button rather than tap it, and every press is momentary to the engine. Yuri's `d, df, f + hold P` is otherwise indistinguishable from the plain fireball listed above it.
