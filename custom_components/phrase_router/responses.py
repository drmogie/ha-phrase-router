"""Shared helper for picking one candidate reply out of a possibly
multi-line custom response field.

Each of a rule's four response fields (see const.py) can hold more than
one line - every non-blank line is a candidate reply, and one is chosen
at random each time the rule fires, so a frequently-triggered rule
doesn't always say the exact same sentence back. A field with only one
line (including every rule's existing single-line value, untouched)
behaves exactly as before - there's always exactly one line to "pick".
"""
from __future__ import annotations

import random


def pick_response(raw: str | None) -> str | None:
    """Split `raw` into non-blank lines and return one at random, or
    None if there's nothing to pick from."""
    if not raw:
        return None
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if not lines:
        return None
    return random.choice(lines)
