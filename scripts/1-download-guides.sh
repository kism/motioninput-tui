#!/usr/bin/env bash
uv sync --all-groups
uv run -m motioninput_tui_guides
uv run -m motioninput_tui_guides --checksum
