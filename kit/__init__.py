"""kit — what every app on the box shares: the page frame and theme, number
tiles, charts that follow the house rules, and the database.

The rules are Dev's, set while Metabase was still the tool, and they live
in code here so no app has to remember them:
- every tile and chart says what it shows without hovering;
- a bar chart always shows its values;
- titles are short;
- no pies or donuts for counts, no stacked bars.
"""
from kit.cache import cached
from kit.cards import board, card, cards, dot, fold, quote, tag
from kit.clicks import on_click
from kit.charts import bar, empty, figure, heatmap, line, world, wrap
from kit.db import query, query_df
from kit.frame import page, section, tile
from kit.theme import brand, theme

__all__ = ["bar", "board", "brand", "cached", "card", "cards", "dot", "empty", "figure", "fold", "heatmap", "line", "on_click",
           "page", "query", "query_df", "quote", "section", "tag", "theme", "tile", "world", "wrap"]
