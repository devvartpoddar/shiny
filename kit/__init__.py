"""kit — what every app on the box shares: the page frame and theme, number
tiles, charts that follow the house rules, and the database.

The rules are Dev's, set while Metabase was still the tool, and they live
in code here so no app has to remember them:
- every tile and chart says what it shows without hovering;
- a bar chart always shows its values;
- titles are short;
- no pies or donuts for counts, no stacked bars.
"""
from kit.cards import board, card, cards
from kit.clicks import on_click
from kit.charts import bar, empty, figure, heatmap, line, world
from kit.db import query, query_df
from kit.frame import page, section, tile
from kit.theme import brand, theme

__all__ = ["bar", "board", "brand", "card", "cards", "empty", "figure", "heatmap", "line", "on_click", "page", "query", "query_df",
           "section", "theme", "tile", "world"]
