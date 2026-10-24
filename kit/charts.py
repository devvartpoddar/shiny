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
    if horizontal:
        fig.update_yaxes(autorange="reversed")
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
