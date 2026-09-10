# motioninput-tui

[![Check](https://github.com/kism/motioninput-tui/actions/workflows/check.yml/badge.svg)](https://github.com/kism/motioninput-tui/actions/workflows/check.yml)
[![CheckType](https://github.com/kism/motioninput-tui/actions/workflows/check_types.yml/badge.svg)](https://github.com/kism/motioninput-tui/actions/workflows/check_types.yml)
[![Test](https://github.com/kism/motioninput-tui/actions/workflows/test.yml/badge.svg)](https://github.com/kism/motioninput-tui/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/kism/motioninput-tui/graph/badge.svg?token=FPGDA0ODT7)](https://codecov.io/gh/kism/motioninput-tui)
[![Docs](https://readthedocs.org/projects/motioninput-tui/badge/?version=latest)](https://motioninput-tui.readthedocs.io/en/latest/?badge=latest)
![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fkism%2Fmotioninput-tui%2Frefs%2Fheads%2Fmain%2Fpyproject.toml)
![PyPI Version](https://img.shields.io/pypi/v/motioninput-tui)

A terminal trainer for fighting game motion inputs. Pick a game and a
character, press inputs, and see which move the game would have given you.
The input handling has been tuned per game: hold down and
double tap forward in 3rd Strike and you get a dragon punch; do it in Super
Turbo or Alpha 3 and you get nothing.

Ships with Hyper Street Fighter II, Street Fighter Alpha 3, 3rd Strike, Ultra
Street Fighter IV, The King of Fighters '98 and 2001, Samurai Shodown II and V
Special, and The Last Blade 2.

**Full documentation: <https://motioninput-tui.readthedocs.io/>**

## Install and run

`uv tool install motioninput-tui`

or

`pipx install --python 3.14 motioninput-tui` (Specify any version of python 3.14 or newer that you have installed)

Either one puts `motioninput-tui` on your PATH.

See the docs for the full command line reference, controls, settings and move
notation.

## Technical information and AI disclaimer

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

Every numbered release, I read all the code changed since the last one, and
play a register of games and characters in the real game and in the trainer to
check they still feel the same. See
[Manual testing](https://motioninput-tui.readthedocs.io/en/latest/manual-testing.html)
for the register and what the check involves.

## Contributing

- [Adding a game](https://motioninput-tui.readthedocs.io/en/latest/adding-a-game.html)
- [Development setup](https://motioninput-tui.readthedocs.io/en/latest/development.html)

## Credit

Move list guides by:

- [Kao Megura / Chris MacDonald](https://gamefaqs.gamespot.com/community/Kao_Megura/contributions/faqs) [Rest In Peace](https://web.archive.org/web/20040520095719/http://cgfm2.emuviews.com/).
- x_MJ_x (Hyper Street Fighter II)
- THEMCD / Damon M. McDaniel (Ultimate Street Fighter IV)
