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

from kit.theme import brand, theme


def _show(tag) -> None:
    sys.displayhook(tag)


def page(title: str, *, subtitle: str | None = None, fillable: bool = False, navbar: str | None = None) -> None:
    """Call once at the top of an Express app: title, theme, the dashboard
    background. Everything after it is the page.

    navbar="<id>": an app of several views gets a dark bar across the top
    with the title and its tabs (top-level `with ui.nav_panel(...)` blocks;
    the id is the one ui.update_navs names), and a top-level right-hand
    `ui.sidebar` beside every view. The subtitle then belongs on the first
    view, not in the bar."""
    from kit.cards import CSS
    from kit.clicks import JS
    if navbar:
        ink = (brand().get("color") or {}).get("palette", {}).get("ink", "#1b1f24")
        # A navbar page takes only tabs at its top level: the style and the
        # click script go in its header.
        xui.page_opts(title=title, window_title=title, theme=theme(), fillable=fillable, id=navbar,
                      navbar_options=cui.navbar_options(bg=ink, theme="dark"),
                      header=cui.TagList(cui.tags.style(CSS), cui.tags.script(JS)))
        return
    xui.page_opts(window_title=title, theme=theme(), fillable=fillable)
    _show(cui.tags.style(CSS))
    _show(cui.tags.script(JS))
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
    # A small white card with the number in the colour: a row of these reads
    # as a strip, not a wall of colour. Plain HTML, so it lays out the same
    # in every container.
    def card(val):
        return cui.div(cui.div(label, class_="kit-tile-label"),
                       cui.div(val, class_=f"kit-tile-value text-{color}"),
                       cui.div(note, class_="kit-tile-note") if note else None,
                       class_="kit-tile")

    if value is not None:
        return card(value)

    def wrap(fn):
        # A decorator's result is bound, not shown; the renderer tagifies
        # to its output slot inside the card.
        _show(card(render.text(fn, inline=True)))
        return fn

    return wrap
