# hello — the app that proves the setup: the kit's frame and theme, a chart
# that follows the house rules, an input that reaches the server and back,
# and the database link (what is in `work`, schema by schema). A comment,
# not a docstring: Express renders a module docstring onto the page.
from __future__ import annotations

import os
import platform
import sys
from datetime import datetime, timezone

from shiny import reactive, render
from shiny.express import input, ui
from shinywidgets import render_plotly

import kit

kit.page("Hello", subtitle="If you can read this, Shiny Server is serving the apps repo.")

STARTED = datetime.now(timezone.utc)


def _db_summary():
    """Tables per schema in work, or the reason the database is out of reach."""
    try:
        df = kit.query_df(
            """
            SELECT n.nspname AS schema, count(c.oid) AS tables
            FROM pg_namespace n
            LEFT JOIN pg_class c ON c.relnamespace = n.oid AND c.relkind IN ('r', 'v', 'm', 'p')
            WHERE n.nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            GROUP BY n.nspname ORDER BY tables DESC, schema
            """
        )
        return df, None
    except Exception as exc:  # noqa: BLE001 — the page shows the reason, whatever it is
        return None, f"{type(exc).__name__}: {str(exc).strip().splitlines()[0][:200]}"


with ui.layout_column_wrap(width="220px", fill=False):
    kit.tile("Python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
             f"{platform.system()} · as {os.environ.get('USER') or os.environ.get('LOGNAME') or 'unknown'}")

    @kit.tile("Schemas in work", note="database link", color="success")
    def n_schemas():
        df, err = _db_summary()
        return "—" if err else str(len(df))

    @kit.tile("Tables in work", note="across every schema", color="success")
    def n_tables():
        df, err = _db_summary()
        return "—" if err else f"{int(df['tables'].sum()):,}"

    @kit.tile("Up since", note="this app's process", color="secondary")
    def up_since():
        return STARTED.strftime("%H:%M UTC")

with kit.section("The database", "Tables per schema in `work`. Empty means the role cannot reach Postgres — the reason is below."):

    @render.ui
    def db_status():
        _, err = _db_summary()
        if err:
            return ui.div(ui.strong("No database: "), err, class_="alert alert-warning")
        return None

    @render_plotly
    def by_schema():
        df, err = _db_summary()
        if err or df is None or df.empty:
            return kit.empty("Tables per schema", "nothing to show until the database answers")
        return kit.bar(df["schema"].tolist(), df["tables"].tolist(), title="Tables per schema", horizontal=True,
                       height=max(240, 36 * len(df) + 80))


with kit.section("The round trip", "Move the slider: the number comes back from the server."):
    ui.input_slider("n", "N", 0, 100, 20)

    @render.text
    @reactive.event(input.n)
    def doubled():
        return f"The server says: {input.n()} × 2 = {input.n() * 2}"
