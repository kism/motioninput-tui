# motioninput-tui

[![Check](https://github.com/kism/motioninput-tui/actions/workflows/check.yml/badge.svg)](https://github.com/kism/motioninput-tui/actions/workflows/check.yml)
[![CheckType](https://github.com/kism/motioninput-tui/actions/workflows/check_types.yml/badge.svg)](https://github.com/kism/motioninput-tui/actions/workflows/check_types.yml)
[![Test](https://github.com/kism/motioninput-tui/actions/workflows/test.yml/badge.svg)](https://github.com/kism/motioninput-tui/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/kism/motioninput-tui/graph/badge.svg?token=FPGDA0ODT7)](https://codecov.io/gh/kism/motioninput-tui)
[![Docs](https://readthedocs.org/projects/motioninput-tui/badge/?version=latest)](https://motioninput-tui.readthedocs.io/en/latest/?badge=latest)

A terminal trainer for fighting game motion inputs. Pick a game and a
character, press inputs, and see which move the game would have given you.
The input handling has been tuned per game: hold down and
double tap forward in 3rd Strike and you get a dragon punch; do it in Super
Turbo or Alpha 3 and you get nothing.

Ships with Hyper Street Fighter II, Street Fighter Alpha 3, 3rd Strike, The
King of Fighters '98 and 2001, and Samurai Shodown V Special.

**Full documentation: <https://motioninput-tui.readthedocs.io/>**

## Install and run

```bash
uv sync --all-extras   # omit --all-extras for a plain install
uv run motioninput-tui
```

See the docs for the full command line reference, controls, settings and move
notation.

## Technical Information and AI Disclaimr

### How it's created

This is my first AI-heavy project, the workflow is

- Get claude to add a game based on a gamefaqs guide
  - sha256 of original guide is verified to avoid possibility of claude editing the reference data
  - skill to make a briefing of each guide, each brief gets made in the game-brief skill
  - claude writes a parser for each guide
    - The moves from the guide are parsed with hard logic, not interpereted by claude
    - The game logic is interpreted by claude based on the guide

- The game engine has many control layouts and motion inputs that are applied per game

### How I ensure code quality

For each numberd release I do the following

- Manually read all the changed code from the previous release

- In this register of games/characters I personally test and re-verify
  - This is not frame perfect, I just open 3SX/Mame/whatever and see if it feels the same.
  - The tests that claude writes will reflect these, but absolutely needs to be checked by a human

- Register (this will later be a separate file)
  - SFA3
    - Ken
      - Shouryuu Ken feels too strict
    - Sakura
      - Shou'ou Ken feels too strict
      - Sakura Otoshi timing is relaxed
      - Midare-zakura is impossible? verify on mame
  - SFIII
    - Ken
    - Elana
  - USFIV
    - Ken
    - Sakura (Sakura Otoshi timing is relaxed)

## Contributing

- [Adding a game](https://motioninput-tui.readthedocs.io/en/latest/adding-a-game.html)
- [Development setup](https://motioninput-tui.readthedocs.io/en/latest/development.html)

## Credit

Move list guides by:

- [Kao Megura / Chris MacDonald](https://gamefaqs.gamespot.com/community/Kao_Megura/contributions/faqs) [Rest In Peace](https://web.archive.org/web/20040520095719/http://cgfm2.emuviews.com/).
- x_MJ_x (Hyper Street Fighter II)
