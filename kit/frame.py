"""The page frame and the number tile — the two things every app starts
with, so they look the same everywhere.

Express shows an expression statement in app.py by handing it to the
display hook; code in this module is not transformed that way, so what it
wants on the page it hands to `sys.displayhook` itself.
"""
from __future__ import annotations

import sys
from contextlib import contextmanager

from shiny import render
from shiny import ui as cui
from shiny.express import ui as xui

from kit.theme import theme


def _show(tag) -> None:
    sys.displayhook(tag)


def page(title: str, *, subtitle: str | None = None, fillable: bool = False) -> None:
    """Call once at the top of an Express app: title, theme, the dashboard
    background. Everything after it is the page."""
    xui.page_opts(title=title, theme=theme(), fillable=fillable)
    with xui.div(class_="kit-header"):
        _show(cui.h2(title, class_="mt-3 mb-0"))
        if subtitle:
            _show(cui.p(subtitle, class_="text-secondary mb-3"))


@contextmanager
def section(title: str, note: str | None = None):
    """A titled block of the page. Use as `with kit.section("Projects"):`."""
    with xui.div(class_="kit-section mb-4"):
        _show(cui.h4(title, class_="mb-1"))
        if note:
            _show(cui.p(note, class_="text-secondary small mb-2"))
        yield


def tile(label: str, value=None, note: str | None = None, *, color: str = "primary"):
    """One number, labelled so it needs no hover.

    Two spellings, both in Express pages:
        kit.tile("Python", "3.12.3", "on the box")       # a plain value
        @kit.tile("Rows", note="in work")                 # a function returning the text
        def rows(): return f"{n:,}"
    """
    if value is not None:
        return cui.value_box(label, value, note or "", theme=color, class_="kit-tile")

    def wrap(fn):
        # A decorator's result is bound, not shown; the renderer tagifies
        # to its output slot inside the box.
        _show(cui.value_box(label, render.text(fn), note or "", theme=color, class_="kit-tile"))
        return fn

    return wrap
