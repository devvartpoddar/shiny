"""Cards that are buttons: a board of columns (where each item stands) and a
grid of labelled cards. A click sends the card's payload to the server as
one input, so a page can open what lies behind it. Plain HTML and a few
lines of CSS; the only script is Shiny.setInputValue on click."""
from __future__ import annotations

import json

from shiny import ui

CSS = """
.kit-tile { background: var(--bs-body-bg, #fff); border: 1px solid var(--bs-border-color, #d9dde3); border-radius: 6px;
  padding: 10px 14px; display: flex; flex-direction: column; gap: 2px; min-width: 0; height: 100%; }
.kit-tile-label { font-size: 0.82rem; color: var(--bs-secondary-color, #6b7280); }
.kit-tile-value { font-size: 1.6rem; font-weight: 600; line-height: 1.2; font-variant-numeric: tabular-nums; }
.kit-tile-note { font-size: 0.75rem; color: var(--bs-secondary-color, #6b7280); }
.kit-board { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px; align-items: start; }
.kit-col { background: var(--bs-light, #f4f5f7); border-radius: 6px; padding: 8px; display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.kit-col > header { display: flex; justify-content: space-between; align-items: center; gap: 6px; font-size: 12.5px; }
.kit-col .count { color: var(--bs-body-color, #1b1f24); font-weight: 600; }
.kit-pill { display: inline-block; font-size: 13px; font-weight: 500; padding: 1px 8px; border-radius: 99px; background: var(--bs-body-bg, #fff); }
.kit-card { text-align: left; width: 100%; background: var(--bs-body-bg, #fff); border: 1px solid var(--bs-border-color, #d9dde3); border-radius: 6px;
  padding: 6px 9px; display: flex; flex-direction: column; gap: 2px; font-size: 13px; cursor: pointer; color: inherit; }
.kit-card:hover { border-color: var(--bs-primary, #2458b3); }
.kit-card .t { font-weight: 600; color: var(--bs-primary, #2458b3); }
.kit-card .s { font-size: 13px; line-height: 1.35; color: #4b5563; }
.kit-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 8px; }
.kit-more { font-size: 13px; color: var(--bs-secondary, #6b7280); padding: 2px; }
/* Tags: one look per kind of thing, told apart by form (solid, tint, outline), not by a colour each. */
.kit-tag { display: inline-block; font-size: 12.5px; line-height: 1.3; padding: 2px 8px; border-radius: 4px; margin: 0 4px 4px 0;
  border: 1px solid transparent; vertical-align: top; }
.kit-tag-solid { background: var(--bs-dark, #1b1f24); color: #fff; font-weight: 600; }
.kit-tag-tint { background: #e3ebf8; color: #1a4287; border-color: #c5d5f0; }
.kit-tag-outline { background: var(--bs-body-bg, #fff); color: var(--bs-body-color, #1b1f24); border-color: #9aa3af; }
.kit-tag-plain { background: var(--bs-light, #f4f5f7); color: #4b5563; }
.kit-dot { display: inline-flex; align-items: center; gap: 5px; font-size: 12.5px; font-weight: 600; white-space: nowrap; }
.kit-dot::before { content: ""; width: 8px; height: 8px; border-radius: 50%; background: currentColor; flex: none; }
.kit-dot.hollow::before { background: transparent; border: 1.5px dashed currentColor; }
.kit-quote { border-left: 3px solid var(--bs-border-color, #d9dde3); padding: 2px 0 2px 10px; margin: 4px 0 6px; font-size: 13.5px;
  line-height: 1.45; color: var(--bs-body-color, #1b1f24); }
.kit-quote details { display: inline; }
.kit-quote details > summary { display: inline; cursor: pointer; color: var(--bs-primary, #2458b3); list-style: none; font-weight: 500; }
.kit-quote details > summary::-webkit-details-marker { display: none; }
.kit-quote details[open] > summary { display: none; }
.kit-quote .foot { display: block; margin-top: 2px; font-size: 12.5px; color: #4b5563; }
.kit-fold { border: 1px solid var(--bs-border-color, #d9dde3); border-radius: 6px; margin-bottom: 8px; background: var(--bs-body-bg, #fff); }
.kit-fold > summary { cursor: pointer; padding: 8px 10px; list-style: none; display: flex; gap: 8px; align-items: baseline; }
.kit-fold > summary::-webkit-details-marker { display: none; }
.kit-fold > summary::before { content: "▸"; color: #4b5563; flex: none; }
.kit-fold[open] > summary::before { content: "▾"; }
.kit-fold[open] > summary { border-bottom: 1px solid var(--bs-border-color, #d9dde3); }
.kit-fold > .body { padding: 10px; }
.kit-fold .t { font-weight: 600; color: var(--bs-primary, #2458b3); }
.kit-fold .s { font-size: 13px; color: #4b5563; }
"""

TAG_KINDS = ("solid", "tint", "outline", "plain")


def tag(text: str, kind: str = "plain", *, title: str | None = None):
    """A small label. kind is its form: 'solid' (dark, the headline thing),
    'tint' (blue wash), 'outline' (white with a border) or 'plain' (grey).
    Give each kind of thing on a page one form, so they can be told apart
    without reading."""
    return ui.span(text, class_=f"kit-tag kit-tag-{kind if kind in TAG_KINDS else 'plain'}", title=title)


def dot(text: str, color: str | None = None, *, hollow: bool = False):
    """A status: a coloured dot and the word in that colour. hollow=True for
    a status that means nothing is there yet."""
    return ui.span(text, class_="kit-dot" + (" hollow" if hollow else ""), style=f"color:{color}" if color else None)


def quote(text: str, *foot, limit: int = 280):
    """Quoted text with a rule down its left. Past `limit` characters it is
    cut at the end of a word and "show more" opens the rest in place (no
    script). foot: what goes under it, small (a page link, a count)."""
    text = (text or "").strip()
    body: list = [text]
    if len(text) > limit + 60:
        cut = text.rfind(" ", 0, limit)
        cut = cut if cut > limit // 2 else limit
        body = [text[:cut], ui.tags.details(ui.tags.summary(" … show more"), text[cut:])]
    foot = [f for f in foot if f]
    return ui.tags.blockquote(*body, ui.span(*foot, class_="foot") if foot else None, class_="kit-quote")


def fold(title, lines: list, *body, open: bool = False):
    """A block that opens on a click: a title and grey lines on its bar,
    anything inside. For a long list whose items each hold more."""
    return ui.tags.details(
        ui.tags.summary(ui.div(ui.div(title, class_="t"), *[ui.div(x, class_="s") for x in lines if x])),
        ui.div(*body, class_="body"), class_="kit-fold", open="" if open else None)


def card(title: str, lines: list[str], *, input_id: str, payload: dict):
    """One clickable card: a title and grey lines under it. A click sets
    input[input_id] to payload (a new value every click)."""
    js = f"Shiny.setInputValue({json.dumps(input_id)}, {json.dumps(payload)}, {{priority: 'event'}})"
    return ui.tags.button({"type": "button", "class": "kit-card", "onclick": js},
                          ui.span(title, class_="t"), *[ui.span(x, class_="s") for x in lines if x])


def cards(items):
    """A grid of cards (each from card())."""
    return ui.div(*items, class_="kit-cards")


def board(columns, *, limit: int = 12):
    """Columns of cards: [(title, pill_style, [card, ...]), ...]. A column
    shows its first `limit` cards and says how many more there are."""
    cols = []
    for title, style, items in columns:
        shown = items[:limit]
        cols.append(ui.div(
            ui.tags.header(ui.span(title, class_="kit-pill", style=style),
                           ui.span(f"{len(items)}", class_="count")),
            *shown,
            ui.span(f"and {len(items) - len(shown)} more", class_="kit-more") if len(items) > len(shown) else None,
            class_="kit-col"))
    return ui.div(*cols, class_="kit-board")
