"""Parsers that turn the reference FAQs into packaged roster data.

This lives outside the ``motioninput_tui`` package on purpose, so ``uv_build``
leaves it out of the wheel. It is a development tool: run
``python -m motioninput_tui_datagen`` from the repository root to rebuild
``motioninput_tui/games/data/*.json`` after fetching the guides with
``python -m motioninput_tui_guides``.
"""
