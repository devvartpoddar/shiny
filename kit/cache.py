"""A small time-limited cache shared by every session of an app. Shiny
Express runs app.py again for each visitor, so a dict in app.py is new every
time; this one lives in the kit module and is filled once per process."""
from __future__ import annotations

import time

_store: dict = {}


def cached(key, fn, *, seconds: int = 600):
    """fn()'s value, computed at most once per `seconds` for this key (any
    hashable; start it with the app's name so two apps never share one)."""
    hit = _store.get(key)
    if hit and time.time() - hit[0] < seconds:
        return hit[1]
    value = fn()
    _store[key] = (time.time(), value)
    return value
