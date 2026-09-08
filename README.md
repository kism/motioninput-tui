# motioninput-tui

[![Check](https://github.com/kism/motioninput-tui/actions/workflows/check.yml/badge.svg)](https://github.com/kism/motioninput-tui/actions/workflows/check.yml)
[![CheckType](https://github.com/kism/motioninput-tui/actions/workflows/check_types.yml/badge.svg)](https://github.com/kism/motioninput-tui/actions/workflows/check_types.yml)
[![Test](https://github.com/kism/motioninput-tui/actions/workflows/test.yml/badge.svg)](https://github.com/kism/motioninput-tui/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/kism/motioninput-tui/graph/badge.svg?token=FPGDA0ODT7)](https://codecov.io/gh/kism/motioninput-tui)
[![Docs](https://readthedocs.org/projects/motioninput-tui/badge/?version=latest)](https://motioninput-tui.readthedocs.io/en/latest/?badge=latest)

A terminal trainer for fighting game motion inputs. Pick a game and a
character, press inputs, and see which move the game would have given you.
The same input does different things in different games: hold down and
double tap forward in 3rd Strike and you get a dragon punch; do it in Super
Turbo or Alpha 3 and you get nothing.

Ships with Hyper Street Fighter II, Street Fighter Alpha 3 and 3rd Strike.

**Full documentation: <https://motioninput-tui.readthedocs.io/>**

## Install and run

```bash
uv sync --all-extras   # omit --all-extras for a plain install
uv run motioninput-tui
```

See the docs for the full command line reference, controls, settings and move
notation.

## Contributing

- [Adding a game](https://motioninput-tui.readthedocs.io/en/latest/adding-a-game/)
- [Development setup](https://motioninput-tui.readthedocs.io/en/latest/development/)

## Credit

Move list guides by Kao Megura / Chris MacDonald [Rest In Peace](https://web.archive.org/web/20040520095719/http://cgfm2.emuviews.com/).
