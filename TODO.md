# TODO

## KOF

Why only 63% trainable
No whole character is missing. The skipped moves are: command throws (b/f + C when close — the engine has no "direction + single button" throw, same as the SF games' non-2-button throws), KoF compound super motions (qcf,hcb, qcb,hcf, f,hcf, qcb,db,f — not in the engine's motion table), and genuine follow-ups/stances. Adding those two super motions to the engine would recover ~12 moves but is a shared-engine change with its own test surface — happy to do it as a follow-up if you want it.

## Datagen

- Should it be a separate helper module?
- Separate game files into a folder

## Timings

Not sure when the ai got it's information from, but need to see if there is a way to get input timing into each game
