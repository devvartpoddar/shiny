"""Cards that are buttons: a board of columns (where each item stands) and a
grid of labelled cards. A click sends the card's payload to the server as
one input, so a page can open what lies behind it. Plain HTML and a few
lines of CSS; the only script is Shiny.setInputValue on click."""
from __future__ import annotations

import json

from shiny import ui

CSS = """
.kit-board { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px; align-items: start; }
.kit-col { background: var(--bs-light, #f4f5f7); border-radius: 6px; padding: 8px; display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.kit-col > header { display: flex; justify-content: space-between; align-items: center; gap: 6px; font-size: 12.5px; }
.kit-col .count { color: var(--bs-secondary, #6b7280); }
.kit-pill { display: inline-block; font-size: 12px; font-weight: 500; padding: 1px 8px; border-radius: 99px; background: var(--bs-body-bg, #fff); }
.kit-card { text-align: left; width: 100%; background: var(--bs-body-bg, #fff); border: 1px solid var(--bs-border-color, #d9dde3); border-radius: 6px;
  padding: 6px 9px; display: flex; flex-direction: column; gap: 2px; font-size: 13px; cursor: pointer; color: inherit; }
.kit-card:hover { border-color: var(--bs-primary, #2458b3); }
.kit-card .t { font-weight: 600; color: var(--bs-primary, #2458b3); }
.kit-card .s { font-size: 12px; color: var(--bs-secondary, #6b7280); }
.kit-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 8px; }
.kit-more { font-size: 12px; color: var(--bs-secondary, #6b7280); padding: 2px; }
"""


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
