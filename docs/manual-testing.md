# Manual testing

The engine is tuned per game, and how a motion *feels* is not something a test
suite can tell you. So before each numbered release every game and character in
the register below gets played in the real game — 3SX, MAME, whatever runs it —
and in the trainer, to check the same input does the same thing.

This is not frame perfect and does not try to be. It is one person deciding
whether the trainer feels like the game. The motion tests under
`tests/engine/test_motions/` are written to match what that finds, which is why
those tests must be checked by a human rather than trusted because they pass.

Third Strike is the exception: its figures are read out of a decompilation
rather than judged by feel — see [Third Strike, from the decompiled
game](sfiii3-from-the-decomp.md).

## What happens at a release

- Read every line of code changed since the previous release.
- Play through the register, noting anything that feels off.
- Correct the ruleset or the reference data, and add a motion test for it.

## Register

Anything noted under a character is an open discrepancy, not a fixed one.

- **SFA3**
  - Ken — Shouryuu Ken feels too strict
  - Sakura — Shou'ou Ken feels too strict; Sakura Otoshi punch timing is relaxed?
- **SFIII: 3rd Strike**
  - Ken
  - Elena
  - Hugo
- **USFIV**
  - Ken
  - Sakura — Sakura Otoshi timing is relaxed
- **KoF 2001**
  - Yuri Sakazaki
