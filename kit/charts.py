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


def bar(x, y, *, title: str | None = None, horizontal: bool = False, label: str | None = None,
        height: int = 360) -> go.Figure:
    """One series of bars, values shown on each bar. Horizontal when the
    categories are long names."""
    text = [f"{v:,.0f}" if isinstance(v, (int, float)) else str(v) for v in y]
    if horizontal:
        trace = go.Bar(x=y, y=x, orientation="h", text=text, textposition="outside", name=label or "")
    else:
        trace = go.Bar(x=x, y=y, text=text, textposition="outside", name=label or "")
    fig = go.Figure(trace)
    fig.update_traces(cliponaxis=False, marker_line_width=0)
    # Room past the longest bar for its value, and air between the bars.
    top = max([v for v in y if isinstance(v, (int, float))] or [0]) * 1.18 or 1
    if horizontal:
        fig.update_yaxes(autorange="reversed")
        fig.update_xaxes(range=[0, top])
    else:
        fig.update_yaxes(range=[0, top])
    fig.update_layout(bargap=0.35)
    return figure(fig, title=title, height=height)


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


def _clip(s, n):
    s = str(s)
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def heatmap(z, x, y, *, title: str | None = None, height: int | None = None, hover: str = "commitments",
            x_chars: int = 22, y_chars: int = 38) -> go.Figure:
    """Counts in a grid (rows y, columns x), each cell showing its number; an
    empty cell is blank, not zero. The house's answer to a stacked bar.
    Long names are cut on the axes (the full name is in the hover) and every
    row and column keeps its label; the height follows the number of rows
    unless one is given."""
    p = palette()
    fig = go.Figure(go.Heatmap(
        z=z, x=list(range(len(x))), y=list(range(len(y))), xgap=2, ygap=2, hoverongaps=False, showscale=False,
        colorscale=[[0, p.get("mist", "#f4f5f7")], [1, p.get("blue", "#2458b3")]],
        text=[["" if v is None else f"{v:,.0f}" for v in row] for row in z], texttemplate="%{text}",
        textfont={"size": 12},
        hovertext=[[f"{yy} · {xx}" for xx in x] for yy in y],
        hovertemplate="%{hovertext}: %{z:,} " + hover + "<extra></extra>"))
    fig.update_xaxes(side="top", tickangle=-30, tickmode="array", tickvals=list(range(len(x))),
                     ticktext=[_clip(v, x_chars) for v in x], showgrid=False)
    fig.update_yaxes(autorange="reversed", tickmode="array", tickvals=list(range(len(y))),
                     ticktext=[_clip(v, y_chars) for v in y], showgrid=False)
    longest = max([len(_clip(v, x_chars)) for v in x] or [0])
    if height is None:
        height = 40 + 6 * longest + 30 * max(len(y), 1)
    return figure(fig, title=title, height=height)


def world(iso2, values, names, *, title: str | None = None, height: int = 420, label: str = "commitments",
          shaded: bool = False) -> go.Figure:
    """A world map of where something is. Every country with a value gets the
    same colour (hover gives the number); shaded=True grades the colour by
    value instead. Countries come as ISO 3166 alpha-2 codes; a code that is
    not a country (a region) is left off, so say beside the map what it does
    not show."""
    import pycountry

    def a3(code):
        c = pycountry.countries.get(alpha_2=str(code).upper()) if code else None
        return c.alpha_3 if c else None

    rows = [(a3(c), v, n) for c, v, n in zip(iso2, values, names) if a3(c)]
    p = palette()
    fig = go.Figure(go.Choropleth(
        locations=[r[0] for r in rows], z=[r[1] for r in rows], text=[r[2] for r in rows],
        locationmode="ISO-3",
        colorscale=[[0, p.get("mist", "#f4f5f7") if shaded else p.get("blue", "#2458b3")], [1, p.get("blue", "#2458b3")]],
        showscale=shaded, marker_line_color=p.get("paper", "#ffffff"), marker_line_width=0.5,
        colorbar={"thickness": 10, "len": 0.6, "outlinewidth": 0, "title": {"text": label, "side": "right"}},
        hovertemplate="%{text}: %{z:,} " + label + "<extra></extra>"))
    fig.update_geos(projection_type="natural earth", showframe=False, showcoastlines=False,
                    showcountries=True, countrycolor=p.get("line", "#d9dde3"), showland=True,
                    landcolor=p.get("mist", "#f4f5f7"), bgcolor="rgba(0,0,0,0)", lataxis_range=[-50, 75])
    fig = figure(fig, title=title, height=height)
    fig.update_layout(margin={"l": 0, "r": 0, "t": 40 if title else 0, "b": 0})
    return fig
