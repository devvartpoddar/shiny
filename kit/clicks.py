"""Clicks on any plotly chart, as a Shiny input: a click on the chart whose
output id is `name` sets input[f"{name}_click"] to the clicked point
({x, y, customdata, text, location, point}). Works for bars, heatmaps, maps
and scatters alike; put what the server needs to know in customdata."""
from __future__ import annotations

JS = """
(function () {
  function attach(gd) {
    // Plotly replaces a chart's event emitter (gd._ev) when it redraws it,
    // which drops listeners: attach again whenever the emitter is new.
    if (!gd.on || !gd._ev || gd.__kitEv === gd._ev) return;
    var out = gd.closest('.shiny-ipywidget-output, .shiny-bound-output');
    if (!out || !out.id) return;
    gd.__kitEv = gd._ev;
    gd.on('plotly_click', function (ev) {
      var p = ev.points && ev.points[0]; if (!p) return;
      Shiny.setInputValue(out.id + '_click', {x: p.x, y: p.y, customdata: p.customdata, text: p.text,
        location: p.location, point: p.pointNumber}, {priority: 'event'});
    });
  }
  function scan() { document.querySelectorAll('.js-plotly-plot').forEach(attach); }
  new MutationObserver(scan).observe(document.documentElement, {childList: true, subtree: true});
  setInterval(scan, 1000);
})();
"""


def on_click(input, name: str, fn):
    """Call fn(point) when the chart `name` is clicked (Express: call at the
    top level of app.py; it returns nothing, so Express shows nothing)."""
    from shiny import reactive

    @reactive.effect
    @reactive.event(input[f"{name}_click"])
    def _clicked():
        fn(input[f"{name}_click"]())
