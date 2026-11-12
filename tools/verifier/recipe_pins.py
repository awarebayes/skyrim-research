#!/usr/bin/env python3
"""The pins of the verifier toolchain recipe, read from the one script that installs it.

Every reader of the pins (the contributor helper among them) goes through `read_pins`, so the
recipe script can be renamed or moved by changing `RECIPE_SCRIPT` here; tests/test_recipe_pins.py
fails if that path or any pin goes missing, before a contributor's `setup` would.
"""
from pathlib import Path
import re

RECIPE_SCRIPT = 'tools/verifier/setup_boat_machine.sh'
PIN_KEYS = ('MSVC_WINE_URL', 'MSVC_WINE_COMMIT', 'VSMAN_URL', 'VSMAN_SHA256', 'SDK_VERSION')


class MissingPin(ValueError):
    """The recipe script is absent or lacks one of PIN_KEYS."""


def read_pins(repo):
    """{key: value} for every key of PIN_KEYS, from `KEY=value` lines of the recipe script."""
    path = Path(repo) / RECIPE_SCRIPT
    try:
        text = path.read_text()
    except OSError as exc:
        raise MissingPin(f'{RECIPE_SCRIPT} cannot be read: {exc}') from exc
    out = {}
    for key in PIN_KEYS:
        m = re.search(rf'^{key}=(\S+)$', text, re.M)
        if not m:
            raise MissingPin(f'{RECIPE_SCRIPT} lacks {key}')
        out[key] = m.group(1)
    return out
