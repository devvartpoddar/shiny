"""Charts that follow the house rules by construction. Plotly, through
shinywidgets' render_plotly; every figure gets the brand's colours and a
plain layout, bars carry their values, and there is no pie here on purpose."""
from __future__ import annotations

import plotly.graph_objects as go

from kit.theme import brand, palette

_FONT = "Inter, system-ui, sans-serif"


def figure(fig: go.Figure, *, title: str | None = None, height: int = 360) -> go.Figure:
    """Apply the house layout to any plotly figure."""
    p = palette()
    b = brand()
    fig.update_layout(
        title={"text": title, "x": 0, "xanchor": "left", "font": {"size": 16}} if title else None,
        font={"family": _FONT, "size": 13, "color": p.get("ink", "#1b1f24")},
        paper_bgcolor=p.get("paper", "#ffffff"),
        plot_bgcolor=p.get("paper", "#ffffff"),
        margin={"l": 8, "r": 8, "t": 40 if title else 8, "b": 8},
        height=height,
        showlegend=len(fig.data) > 1,
        legend={"orientation": "h", "y": -0.15},
        colorway=[p.get(k) for k in ("blue", "teal", "amber", "red", "grey") if p.get(k)] or None,
        hoverlabel={"font": {"family": _FONT}},
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=p.get("line", "#d9dde3"))
    fig.update_yaxes(gridcolor=p.get("line", "#d9dde3"), zeroline=False)
    fig.layout.meta = {"brand": (b.get("meta") or {}).get("name")}
    return fig


def wrap(s, width: int = 30, lines: int = 3) -> str:
    """A long name broken over lines at spaces (plotly breaks on <br>), never
    cut mid-word; past `lines` lines the last one ends in an ellipsis. The
    full name belongs in the hover."""
    words, out, cur = str(s).split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        out.append(cur)
    if len(out) > lines:
        out = out[:lines]
        out[-1] = out[-1].rstrip(" ,;:·-") + "…"
    return "<br>".join(out)


def bar(x, y, *, title: str | None = None, horizontal: bool = False, label: str | None = None,
        height: int | None = None, text: list[str] | None = None, hover: list[str] | None = None,
        wrap_at: int = 34) -> go.Figure:
    """One series of bars, values shown on each bar. Horizontal when the
    categories are long names: each name is wrapped, never cut, the axis makes
    room for it, and the height follows the number of bars unless one is
    given. text: what each bar shows instead of its value (e.g. "37 · 54%");
    hover: a full line per bar."""
    text = text or [f"{v:,.0f}" if isinstance(v, (int, float)) else str(v) for v in y]
    hover = hover or [f"{k}: {t}" for k, t in zip(x, text)]
    common = {"text": text, "textposition": "outside", "name": label or "", "hovertext": hover,
              "hovertemplate": "%{hovertext}<extra></extra>"}
    if horizontal:
        names = [wrap(k, wrap_at) for k in x]
        trace = go.Bar(x=y, y=list(range(len(x))), orientation="h", **common)
    else:
        trace = go.Bar(x=x, y=y, **common)
    fig = go.Figure(trace)
    fig.update_traces(cliponaxis=False, marker_line_width=0)
    # Room past the longest bar for its value, and air between the bars.
    longest = max([len(t) for t in text] or [1])
    top = max([v for v in y if isinstance(v, (int, float))] or [0]) * (1.12 + 0.02 * longest) or 1
    if horizontal:
        rows = [n.count("<br>") + 1 for n in names]
        fig.update_yaxes(autorange="reversed", tickmode="array", tickvals=list(range(len(x))), ticktext=names,
                         automargin=True, ticklabelstandoff=6, showgrid=False)
        fig.update_xaxes(range=[0, top], showticklabels=False)
        if height is None:
            height = 30 + sum(max(34, 17 * r + 10) for r in rows)
    else:
        fig.update_yaxes(range=[0, top])
        fig.update_xaxes(automargin=True)
    fig.update_layout(bargap=0.35)
    return figure(fig, title=title, height=height or 360)


def empty(title: str, reason: str = "no data", *, height: int = 200) -> go.Figure:
    """What a chart shows when it has nothing: the title and the reason, no
    axes pretending otherwise."""
    fig = go.Figure()
    fig.add_annotation(text=reason, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
                       font={"size": 14, "color": palette().get("grey", "#6b7280")})
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return figure(fig, title=title, height=height)


def line(x, ys: dict[str, list], *, title: str | None = None, height: int = 360) -> go.Figure:
    """One or more lines over x; the dict's keys are the legend."""
    fig = go.Figure()
    for name, y in ys.items():
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", name=name))
    return figure(fig, title=title, height=height)


def heatmap(z, x, y, *, title: str | None = None, height: int | None = None, hover: str = "commitments",
            x_chars: int = 13, y_chars: int = 34, text=None, hovertext=None) -> go.Figure:
    """Counts in a grid (rows y, columns x), each cell showing its number; an
    empty cell is blank, not zero. The house's answer to a stacked bar.
    Names are wrapped on the axes, never cut or turned: column names sit
    upright over their column, row names take the room they need, and the
    height follows the rows and the tallest column name unless one is given.
    text / hovertext: grids the shape of z, to show something other than the
    number in a cell or to say more in its hover."""
    p = palette()
    xs, ys = [wrap(v, x_chars, 4) for v in x], [wrap(v, y_chars, 3) for v in y]
    if text is None:
        text = [["" if v is None else f"{v:,.0f}" for v in row] for row in z]
    if hovertext is None:
        hovertext = [[f"{yy} · {xx}: {'' if v is None else format(v, ',')} {hover}" for xx, v in zip(x, row)]
                     for yy, row in zip(y, z)]
    fig = go.Figure(go.Heatmap(
        z=z, x=list(range(len(x))), y=list(range(len(y))), xgap=2, ygap=2, hoverongaps=False, showscale=False,
        # The darkest cell stays light enough for dark numbers to read on it.
        colorscale=[[0, p.get("mist", "#f4f5f7")], [1, "#8fb0e6"]],
        text=text, texttemplate="%{text}", textfont={"size": 12, "color": p.get("ink", "#1b1f24")},
        hovertext=hovertext, hovertemplate="%{hovertext}<extra></extra>"))
    fig.update_xaxes(side="top", tickangle=0, tickmode="array", tickvals=list(range(len(x))),
                     ticktext=xs, showgrid=False, automargin=True, tickfont={"size": 11.5})
    fig.update_yaxes(autorange="reversed", tickmode="array", tickvals=list(range(len(y))),
                     ticktext=ys, showgrid=False, automargin=True, ticklabelstandoff=6)
    if height is None:
        head = max([v.count("<br>") + 1 for v in xs] or [1])
        tall = max([v.count("<br>") + 1 for v in ys] or [1])
        height = 24 + 16 * head + (38 if tall <= 2 else 54) * max(len(y), 1)
    return figure(fig, title=title, height=height)


def world(iso2, values, names, *, title: str | None = None, height: int = 420, label: str = "commitments",
          shaded: bool = False, hover: list[str] | None = None) -> go.Figure:
    """A world map of where something is. Every country with a value gets the
    same colour (hover gives the number); shaded=True grades the colour by
    value instead. Countries come as ISO 3166 alpha-2 codes; a code that is
    not a country (a region) is left off, so say beside the map what it does
    not show. hover: a full line per country, in place of "name: value label"."""
    import pycountry

    def a3(code):
        c = pycountry.countries.get(alpha_2=str(code).upper()) if code else None
        return c.alpha_3 if c else None

    hover = list(hover) if hover is not None else [f"{n}: {v:,} {label}" for v, n in zip(values, names)]
    rows = [(a3(c), v, n, h) for c, v, n, h in zip(iso2, values, names, hover) if a3(c)]
    p = palette()
    fig = go.Figure(go.Choropleth(
        locations=[r[0] for r in rows], z=[r[1] for r in rows], text=[r[2] for r in rows],
        locationmode="ISO-3",
        colorscale=[[0, p.get("mist", "#f4f5f7") if shaded else p.get("blue", "#2458b3")], [1, p.get("blue", "#2458b3")]],
        showscale=shaded, marker_line_color=p.get("paper", "#ffffff"), marker_line_width=0.5,
        colorbar={"thickness": 10, "len": 0.6, "outlinewidth": 0, "title": {"text": label, "side": "right"}},
        hovertext=[r[3] for r in rows], hovertemplate="%{hovertext}<extra></extra>"))
    fig.update_geos(projection_type="natural earth", showframe=False, showcoastlines=False,
                    showcountries=True, countrycolor=p.get("line", "#d9dde3"), showland=True,
                    landcolor=p.get("mist", "#f4f5f7"), bgcolor="rgba(0,0,0,0)", lataxis_range=[-50, 75])
    fig = figure(fig, title=title, height=height)
    fig.update_layout(margin={"l": 0, "r": 0, "t": 40 if title else 0, "b": 0})
    return fig
