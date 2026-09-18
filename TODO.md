# TODO

The rosters sit at 89% trainable overall, 76% (Sailor Moon S) to 95% (KoF '98).
`python -m motioninput_tui_datagen --show-skipped` lists what is left and why.

## Timings

3S is accurate, getting real numbers for any other game would require either annotated disassembly or decompiled code that doesn't currently exist. Another method would be using mame lua and memory editing to figure it out.

The same goes for `chain_window_ms` (700ms) and `sequence_window_ms` (1200ms), reckoned at one figure for every game that has them wired. Nothing has been measured. 3rd Strike carries both, which makes them the only two numbers in that game's ruleset not read off the decompilation — `docs/sfiii3-from-the-decomp.md` says so under "Still open".

## Tekken 3

No longer blocked. `MotionKind.SEQUENCE` handles a run of presses, each with whatever direction was held for it, so the combo structure this file used to call difficult is modelled: <https://gamefaqs.gamespot.com/arcade/563192-tekken-3/faqs/979>. Its panel is defined already (`buttons.TEKKEN`, square and triangle over cross and circle) and reached by no game, which is what adding it would change.

Two things a Tekken parser will want that the sequence model does not have yet. A step is a press, so a direction with no button attaches to the press after it — Tekken writes `f,f,N,2`, where the `N` is a deliberate neutral between two forwards and no press belongs to it. And Tekken tells a held press (`2*`) from a tapped one, which is the same gap `normalise` already notes for `+ hold P`.

## Chains in the remaining guides

`Move.follows` is wired for every roster whose guide names the parent — 228 links across eight games. Four shapes cover it: the SNK guides name the parent first (`neogeo.split_parent`); the Street Fighter ones name it last, spell its command out again, or trail off with `...` (all three in `common.split_follow_on`); and Martial Masters and SSV Special indent a link under its parent.

Of the links still struck through, three are guide typos where the command names a parent one letter off the move it means (Juzo Kanzaki's `Iwakudai` for `Iwakudaki`, Naoe Shigen's `Konogosai` for `Kongosai`), which want an override table or fuzzy matching — a third rung the current two-pass match deliberately stops short of. Seven name the parent by an abbreviation the roster does not carry (`after H.C.`, `during C. Shinwa`), which an alias table per guide would fix.

Three of 3rd Strike's Akuma links are in the right section but still struck, because their own input reads `press P while in air` and `while` is one of the words `normalise` rejects outright. Here it describes the state the dive already put him in rather than a condition to meet, but teaching `_UNSUPPORTED` that difference affects every guide.

## Conditions the trainer has no model of

The largest remaining block, 106 moves. `While getting up`, `Jump against a wall`, `against a back-turned opponent`, `when near a knife`, `while dashing`, `when hit`. These are game states rather than inputs, and they are right to stay struck through — but a few are close to reachable. Samurai Shodown V Special has twelve `Sankaku Tobi` (wall jump, `uf~df near a wall in air`) and six `while dashing` moves; a dash or a wall would each be a real engine concept, not a parsing fix.

Related: 57 moves have no button requirement the parser can find, most of them movement (`_move b / f`, `_press in any dir.`, `Nidan Jump`), and Shizumaru Hisame's five charge-a-button moves (`Hold any for 1.5 sec.`) want a held button the engine treats as momentary.

## Motions not in the table

Around 90 moves, and nearly all one-offs. The ones worth an entry each need a real matcher rather than a table row: `d,d` (16 moves) and `d,d,d` are double and triple taps of one direction, `d,u` is a tap rather than a charge, `f,b,f,b,f,b,d` (7) is Galford's and Hanzo's counter, and every character in Samurai Shodown II has a different long `Nuigurumi` code.

`db,qcf` (`db,d,df,f`) looks like it could just map to a quarter circle, but it must not — Ukyo and Suija have a plain `qcf` move as well, and mapping it would hand out the wrong one of the pair.

## Held buttons

Two moves are struck through because the guide says to hold the button rather than tap it, and every press is momentary to the engine. Yuri's `d, df, f + hold P` is otherwise indistinguishable from the plain fireball listed above it. Shizumaru's five, above, are the same problem at a longer timescale.
