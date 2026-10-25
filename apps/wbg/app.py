# wbg — climate resilience commitments in World Bank appraisal documents for
# the digital assets a project finances (repository devvartpoddar/wbg-digital-
# resilience). Every query and every number computed beyond the views is in
# wbg_portfolio.app; this file only lays them out. Read only: no write, no
# model call. Two views: the overall picture, and one country, project, asset
# or measure at a time. Any bar, cell, country or card opens the commitments
# behind it in the side panel. A comment, not a docstring: Express renders a
# module docstring onto the page.
from __future__ import annotations

import time

import pandas as pd
import plotly.graph_objects as go
from shiny import reactive, render
from shiny import ui as cui
from shiny.express import input, ui
from shinywidgets import render_plotly

import kit
from wbg_portfolio import app as W

kit.page("WBG Digital Resilience",
         subtitle="Climate resilience commitments in World Bank appraisal documents, for the digital assets a project finances.")

LENSES = {"country": "Country", "project": "Project", "asset": "Asset", "measure": "Measure"}
COHORTS = {"": "All projects", "digital": "Digital projects", "digital_contributor": "Projects with a digital part"}
STAGE_STYLE = {"Completed": "color:#1f8a70", "Under way": "color:#2458b3", "Coming up": "color:#c77d00",
               "Dropped": "color:#6b7280", "No package linked": "color:#6b7280"}
DRILL_MAX = 60          # commitments listed in the side panel; the count above says how many there are
CACHE_SECONDS = 600     # the data change only at a publish

_cache: dict = {}


def _cached(key, fn):
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < CACHE_SECONDS:
        return hit[1]
    value = fn()
    _cache[key] = (time.time(), value)
    return value


def short_asset(a):
    if a == W.NO_ASSET:
        return "No asset named"
    for long, s in ((" and international connectivity", ""), (" and emergency communication systems", ""),
                    (" and terrestrial wireless networks", " and wireless"), (" and sensor networks", " and sensors"),
                    (" infrastructure", ""), (" systems and applications", " systems")):
        a = a.replace(long, s)
    return a


def short_type(t):
    return "No type" if t == W.NO_TYPE else t.removeprefix("OTH. ")


def plural(n, word):
    return f"{n:,} {word}{'' if n == 1 else 's'}"


# ---------------------------------------------------------------- data

@reactive.calc
def frame():
    cohort = input.cohort() or None
    return _cached(("commitments", cohort), lambda: W.commitments(kit.query_df, cohort))


@reactive.calc
def measure_table():
    return _cached("measures", lambda: W.measures(kit.query_df))


@reactive.calc
def type_table():
    return _cached("types", lambda: W.measure_types(kit.query_df))


@reactive.calc
def asset_table():
    return _cached("assets", lambda: W.assets(kit.query_df))


def lens_frame(lens=None, value=None):
    df = frame()
    lens, value = lens or input.lens(), value if value is not None else input.pick()
    if not value:
        return df.iloc[0:0]
    col = {"country": "place", "project": "project_name", "asset": "asset_name", "measure": "measure_name"}[lens]
    return df[df[col] == value]


# ---------------------------------------------------------------- the drill

drill = reactive.value(None)        # {"title": str, "where": {column: value}}


def open_drill(title, **where):
    drill.set({"title": title, "where": where, "at": time.time()})


@reactive.effect
@reactive.event(drill)
def _show_panel():
    if drill.get():
        ui.update_sidebar("panel", show=True)


@reactive.effect
@reactive.event(input.card)
def _card_clicked():
    c = input.card()
    if c.get("go"):
        go_to(c["go"], c["value"])
    else:
        open_drill(c["title"], **c["where"])


def go_to(lens, value):
    ui.update_navs("view", selected="Explore")
    ui.update_radio_buttons("lens", selected=lens)
    pending_pick.set(value)


pending_pick = reactive.value(None)


HANDLERS: dict = {}     # chart output id -> what its click does (this session)


def clickable(name, fig, keys, on_click):
    """Chart `name` with keys[i] (or keys[i][j] for a grid) behind each point;
    a click calls on_click(key)."""
    fig.data[0].customdata = keys
    HANDLERS[name] = on_click
    return fig


CHARTS = ("ov_map", "ov_measure", "ov_asset", "ov_heat", "ov_stage", "c_heat", "c_assets", "a_measures", "a_heat",
          "a_map", "m_map", "m_heat_region", "m_heat_asset")
for _name in CHARTS:
    kit.on_click(input, _name, lambda pt, n=_name: HANDLERS[n](pt["customdata"]) if n in HANDLERS and pt.get("customdata") is not None else None)


# ---------------------------------------------------------------- layout

with ui.div(class_="d-flex flex-wrap gap-3 align-items-end mb-2"):
    ui.input_select("cohort", "Projects", COHORTS, selected="")
    ui.input_selectize("find", "Find a country, project, asset or measure", choices=[],
                       options={"placeholder": "Type a name"}, width="420px")


@reactive.effect
def _find_choices():
    df = frame()
    groups = {"Countries and regions": sorted(df["place"].dropna().unique()),
              "Projects": sorted(df["project_name"].dropna().unique()),
              "Assets": sorted(a for a in df["asset_name"].unique() if a != W.NO_ASSET),
              "Measures": sorted(df["measure_name"].unique())}
    keys = {"Countries and regions": "country", "Projects": "project", "Assets": "asset", "Measures": "measure"}
    ui.update_selectize("find", choices={g: {f"{keys[g]}|{v}": v for v in vs} for g, vs in groups.items()},
                        selected="", server=False)


@reactive.effect
@reactive.event(input.find)
def _found():
    if input.find():
        lens, value = input.find().split("|", 1)
        go_to(lens, value)


with ui.layout_sidebar(fillable=False, height="calc(100vh - 190px)", border=False):
    with ui.sidebar(id="panel", position="right", open="closed", width=480, title="The commitments behind it"):

        @render.ui
        def panel_body():
            d = drill.get()
            if not d:
                return ui.p("Click a bar, a cell, a country or a card.", class_="text-secondary")
            df = frame()
            for col, val in d["where"].items():
                df = df[df[col] == val]
            ids = df["commitment_id"].head(DRILL_MAX).tolist()
            ev = W.evidence(kit.query_df, ids).set_index("commitment_id") if ids else pd.DataFrame()
            head = [cui.h5(d["title"], class_="mb-1"),
                    cui.p(f"{plural(len(df), 'commitment')} · {plural(df['project_id'].nunique(), 'project')} · "
                          f"{plural(df['place'].nunique(), 'place')}", class_="text-secondary small")]
            if len(df) > DRILL_MAX:
                head.append(cui.p(f"The first {DRILL_MAX} are listed.", class_="text-secondary small"))
            body = []
            for (pid, pname, place), rows in df.head(DRILL_MAX).groupby(["project_id", "project_name", "place"], sort=False):
                items = []
                for _, r in rows.iterrows():
                    e = ev.loc[r["commitment_id"]] if r["commitment_id"] in ev.index else None
                    tags = [x for x in (r["measure_name"] if "measure_name" not in d["where"] else None,
                                        short_type(r["type_name"]) if "type_name" not in d["where"] else None,
                                        short_asset(r["asset_name"]) if "asset_name" not in d["where"] else None) if x]
                    items.append(cui.div(
                        cui.div(*[cui.span(t, class_="badge text-bg-light border me-1") for t in tags],
                                cui.span(r["stage"], class_="badge text-bg-light", style=STAGE_STYLE.get(r["stage"]))),
                        cui.tags.blockquote(
                            (e["text"] if e is not None else ""),
                            cui.div(cui.a(f"page {e['page_number']}", href=e["pdf_url"], target="_blank")
                                    if e is not None and e["pdf_url"] else "",
                                    f" · {plural(int(r['sentences']), 'sentence')}", class_="small text-secondary"),
                            class_="border-start border-3 ps-2 my-1 small"),
                        class_="mb-2"))
                body.append(cui.div(
                    cui.div(kit.card(pname, [place], input_id="card", payload={"go": "project", "value": pname}),
                            class_="mb-1"),
                    *items, class_="mb-3 pb-2 border-bottom"))
            return cui.div(*head, *body)

    with ui.navset_underline(id="view"):

        # ======================================================= overview
        with ui.nav_panel("Overview"):

            @render.ui
            def tiles():
                h = W.headline(frame())
                share = "—" if h["linked_share"] is None else f"{h['linked_share']:.0%}"
                return cui.layout_column_wrap(
                    kit.tile("Commitments", f"{h['commitments']:,}", "project × asset × measure × type"),
                    kit.tile("Projects", f"{h['projects']:,}"),
                    kit.tile("Countries", f"{h['countries']:,}", "plus regional projects"),
                    kit.tile("Measures", f"{h['measures']:,}"),
                    kit.tile("With a linked package", share, "read as leads, not a full account", color="secondary"),
                    width="200px", fill=False, class_="my-3")

            with ui.card():
                ui.card_header("Where · click a country to explore it")

                @render_plotly
                def ov_map():
                    c = W.count(frame()[~frame()["is_regional"].fillna(False).astype(bool)], "country_code", "place")
                    fig = kit.world(c["country_code"], c["commitments"], c["place"], height=460)
                    return clickable("ov_map", fig, list(fig.data[0].text), lambda place: go_to("country", place))

                @render.text
                def ov_regional():
                    n = int(frame()["is_regional"].fillna(False).astype(bool).sum())
                    return f"{plural(n, 'commitment')} sit in regional projects and are not on the map."

            with ui.layout_columns(col_widths=[6, 6]):
                with ui.card():
                    ui.card_header("By measure · click a bar to explore it")

                    @render_plotly
                    def ov_measure():
                        c = W.count(frame(), "measure_name")
                        fig = kit.bar(c["measure_name"].tolist(), c["commitments"].tolist(), horizontal=True,
                                      height=max(300, 34 * len(c) + 60))
                        return clickable("ov_measure", fig, c["measure_name"].tolist(), lambda m: go_to("measure", m))

                with ui.card():
                    ui.card_header("By digital asset · click a bar to explore it")

                    @render_plotly
                    def ov_asset():
                        c = W.count(frame(), "asset_name")
                        c = pd.concat([c[c["asset_name"] != W.NO_ASSET], c[c["asset_name"] == W.NO_ASSET]])
                        keys = c["asset_name"].tolist()
                        fig = kit.bar([short_asset(k) for k in keys], c["commitments"].tolist(), horizontal=True,
                                      height=max(300, 34 * len(c) + 60))
                        return clickable("ov_asset", fig, keys, lambda a: go_to("asset", a) if a != W.NO_ASSET
                                         else open_drill("No asset named", asset_name=W.NO_ASSET))

            with ui.card():
                ui.card_header("Measures by asset · click a cell for its commitments")

                @render_plotly
                def ov_heat():
                    return heat("ov_heat", frame(), "measure_name", "asset_name", xlab=short_asset, height=520)

            with ui.layout_columns(col_widths=[8, 4]):
                with ui.card():
                    ui.card_header("By approval year")

                    @render_plotly
                    def ov_fy():
                        c = W.count(frame(), "approval_fiscal_year").dropna().sort_values("approval_fiscal_year")
                        fig = kit.bar([f"FY{int(y)}" for y in c["approval_fiscal_year"]], c["commitments"].tolist(), height=280)
                        fig.update_xaxes(type="category")
                        return fig

                with ui.card():
                    ui.card_header("Linked procurement so far")

                    @render_plotly
                    def ov_stage():
                        c = W.count(frame(), "stage").set_index("stage").reindex(W.STAGES[:-1]).fillna(0).reset_index()
                        fig = kit.bar(c["stage"].tolist(), c["commitments"].astype(int).tolist(), horizontal=True, height=240)
                        return clickable("ov_stage", fig, c["stage"].tolist(), lambda s: open_drill(f"Linked procurement: {s}", stage=s))

                    ui.p("Package links are found for about a third of commitments.", class_="small text-secondary")

        # ======================================================= explore
        with ui.nav_panel("Explore"):
            with ui.div(class_="d-flex flex-wrap gap-3 align-items-end my-3"):
                ui.input_radio_buttons("lens", "Look at one", LENSES, selected="country", inline=True)
                ui.input_selectize("pick", None, choices=[], width="460px")

            @reactive.effect
            def _pick_choices():
                df, lens = frame(), input.lens()
                col = {"country": "place", "project": "project_name", "asset": "asset_name", "measure": "measure_name"}[lens]
                c = W.count(df, col)
                c = c[c[col] != W.NO_ASSET]
                with reactive.isolate():
                    want = pending_pick.get()
                choices = c[col].tolist()
                ui.update_selectize("pick", choices=choices,
                                    selected=want if want in choices else (choices[0] if choices else None))
                pending_pick.set(None)

            # ---------------------------------------------- one country
            with ui.panel_conditional("input.lens === 'country'"):

                @render.ui
                def c_head():
                    df = lens_frame()
                    if df.empty:
                        return None
                    return facts(input.pick(), "Country or region", df)

                with ui.card():
                    ui.card_header("Its projects · click one for its commitments")

                    @render.ui
                    def c_projects():
                        df = lens_frame()
                        items = []
                        for (pid, pname), rows in df.groupby(["project_id", "project_name"]):
                            ms = sorted(rows["measure_name"].unique())
                            items.append(kit.card(pname, [" · ".join(ms), f"{plural(len(rows), 'commitment')} · {plural(len(ms), 'measure')}"],
                                                  input_id="card", payload={"title": f"{pname} in {input.pick()}",
                                                                            "where": {"project_id": pid}}))
                        return kit.cards(items)

                with ui.card():
                    ui.card_header("Who commits to what · click a cell")

                    @render_plotly
                    def c_heat():
                        return heat("c_heat", lens_frame(), "measure_name", "project_name", height=440, where={"place": input.pick()})

                with ui.card():
                    ui.card_header("Where each project stands · by linked procurement")

                    @render.ui
                    def c_board():
                        return stand(lens_frame(), {"place": input.pick()})

                with ui.card():
                    ui.card_header("Digital assets · click a bar")

                    @render_plotly
                    def c_assets():
                        return bars("c_assets", lens_frame(), "asset_name", where={"place": input.pick()}, label=short_asset)

            # ---------------------------------------------- one project
            with ui.panel_conditional("input.lens === 'project'"):

                @reactive.calc
                def project_parts():
                    df = lens_frame("project", input.pick())
                    if df.empty:
                        return None
                    pid = df["project_id"].iloc[0]
                    return _cached(("project", pid), lambda: W.project(kit.query_df, pid))

                @render.ui
                def p_head():
                    parts, df = project_parts(), lens_frame()
                    if parts is None or parts["header"].empty:
                        return None
                    h = parts["header"].iloc[0]
                    bits = [h["project_id"], h["country_name"] or h["region"], h["status"],
                            f"approved FY{int(h['approval_fiscal_year'])}" if pd.notna(h["approval_fiscal_year"]) else None,
                            f"US${h['commitment_usd_m']:,.1f} million" if pd.notna(h["commitment_usd_m"]) else None,
                            f"closes {h['closing_date']:%d %b %Y}" if pd.notna(h["closing_date"]) else None,
                            plural(int(h["documents_read"]), "document") + " read"]
                    return cui.card(cui.card_body(
                        cui.h3(h["project_name"], class_="h4 mb-1"),
                        cui.p(" · ".join(str(b) for b in bits if b), class_="text-secondary mb-1"),
                        cui.p(f"{plural(len(df), 'commitment')} under {plural(df['label_set'].nunique(), 'measure')} · "
                              f"{plural(len(parts['packages']), 'linked package')}", class_="mb-0")))

                with ui.layout_columns(col_widths=[6, 6]):
                    with ui.card():
                        ui.card_header("What it commits to · with the strongest sentence")

                        @render.ui
                        def p_commits():
                            df = lens_frame()
                            if df.empty:
                                return None
                            ev = W.evidence(kit.query_df, df["commitment_id"]).merge(
                                df[["commitment_id", "measure_name"]], on="commitment_id")
                            best = ev.sort_values("posterior_probability", ascending=False).drop_duplicates("measure_name")
                            out = []
                            for m, rows in df.groupby("measure_name"):
                                b = best[best["measure_name"] == m]
                                types = sorted({short_type(t) for t in rows["type_name"]})
                                out.append(cui.div(
                                    kit.card(m, [f"{plural(len(rows), 'commitment')} · " + "; ".join(types)], input_id="card",
                                             payload={"title": f"{m} · {input.pick()}",
                                                      "where": {"project_name": input.pick(), "measure_name": m}}),
                                    cui.tags.blockquote(b["text"].iloc[0],
                                                   cui.div(cui.a(f"page {b['page_number'].iloc[0]}", href=b["pdf_url"].iloc[0], target="_blank"),
                                                           class_="small"),
                                                   class_="border-start border-3 ps-2 my-1 small") if len(b) else None,
                                    class_="mb-2"))
                            return cui.div(*out)

                    with ui.div(class_="d-flex flex-column gap-3"):
                      with ui.card():
                        ui.card_header("Digital assets its sentences name")

                        @render_plotly
                        def p_assets():
                            parts = project_parts()
                            if parts is None or parts["assets"].empty:
                                return kit.empty("Assets", "no asset named")
                            a = parts["assets"]
                            return kit.bar([short_asset(x) for x in a["asset_name"]], a["sentences_naming_it"].fillna(0).astype(int).tolist(),
                                           horizontal=True, height=max(240, 30 * len(a) + 60))

                      with ui.card():
                        ui.card_header("Components · cost from all funding sources")

                        @render.data_frame
                        def p_components():
                            parts = project_parts()
                            if parts is None:
                                return None
                            c = parts["components"]
                            return render.DataGrid(pd.DataFrame({
                                "Component": [f"{n} {name}" if n else name for n, name in zip(c["component_number"].fillna(""), c["component_name"])],
                                "US$ million": c["cost_usd_millions"].round(1)}), width="100%")

                with ui.card():
                    ui.card_header("Its linked packages · each bubble is a package, sized by estimated value")

                    @render_plotly
                    def p_packages():
                        parts = project_parts()
                        if parts is None or parts["packages"].dropna(subset=["date"]).empty:
                            return kit.empty("Packages", "no dated package linked")
                        pk = parts["packages"].dropna(subset=["date"])
                        fig = go.Figure(go.Scatter(
                            x=pk["date"], y=pk["package_status"], mode="markers",
                            text=pk["description"].str.slice(0, 90), customdata=pk["estimated_amount_usd"],
                            marker={"size": 10 + (pk["estimated_amount_usd"].fillna(0) / 1000) ** 0.5 * 1.4, "opacity": 0.8},
                            hovertemplate="%{text}<br>%{x|%d %b %Y} · about US$%{customdata:,.0f}<extra></extra>"))
                        return kit.figure(fig, height=300)

                with ui.card():
                    ui.card_header("Documents read")

                    @render.ui
                    def p_docs():
                        parts = project_parts()
                        if parts is None:
                            return None
                        return cui.tags.ul(*[cui.tags.li(cui.a(f"{r.title or r.document_kind}", href=r.pdf_url, target="_blank"),
                                                         f" · {r.document_kind} · {r.document_date:%d %b %Y}" if pd.notna(r.document_date) else "")
                                             for r in parts["documents"].itertuples()])

            # ---------------------------------------------- one asset
            with ui.panel_conditional("input.lens === 'asset'"):

                @render.ui
                def a_head():
                    df = lens_frame()
                    if df.empty:
                        return None
                    d = asset_table()
                    d = d[d["asset_name"] == input.pick()]
                    return facts(input.pick(), "Digital asset", df, d["definition"].iloc[0] if len(d) else None)

                with ui.layout_columns(col_widths=[6, 6]):
                    with ui.card():
                        ui.card_header("Measures committed for it · click a bar")

                        @render_plotly
                        def a_measures():
                            return bars("a_measures", lens_frame(), "measure_name", where={"asset_name": input.pick()})

                    with ui.card():
                        ui.card_header("Measures by region · click a cell")

                        @render_plotly
                        def a_heat():
                            return heat("a_heat", lens_frame(), "measure_name", "region", height=400, where={"asset_name": input.pick()})

                with ui.card():
                    ui.card_header("Where each project stands · by linked procurement")

                    @render.ui
                    def a_board():
                        return stand(lens_frame(), {"asset_name": input.pick()})

                with ui.card():
                    ui.card_header("Where · click a country")

                    @render_plotly
                    def a_map():
                        return lens_map("a_map", lens_frame(), {"asset_name": input.pick()})

            # ---------------------------------------------- one measure
            with ui.panel_conditional("input.lens === 'measure'"):

                @render.ui
                def m_head():
                    df = lens_frame()
                    if df.empty:
                        return None
                    m = measure_table()
                    m = m[m["measure_name"] == input.pick()]
                    acc = None
                    if len(m) and pd.notna(m["precision"].iloc[0]):
                        acc = (f"Accuracy {m['precision'].iloc[0]:.0%} on {int(m['graded_units'].iloc[0])} checked sentences"
                               + (" (training sample, provisional)" if m["graded_sheet"].iloc[0] != "evaluation" else ""))
                    return facts(input.pick(), "Measure", df, m["definition"].iloc[0] if len(m) else None, acc)

                with ui.card():
                    ui.card_header("The types · click a type for its commitments")

                    @render.ui
                    def m_types():
                        df = lens_frame()
                        if df.empty:
                            return None
                        defs = type_table()
                        defs = defs[defs["label_set"] == df["label_set"].iloc[0]].drop_duplicates("type_name").set_index("type_name")["definition"]
                        items = []
                        for t, rows in sorted(df.groupby("type_name"), key=lambda g: -len(g[1])):
                            items.append(kit.card(short_type(t), [defs.get(t, "Commitments that name no specific type." if t == W.NO_TYPE else ""),
                                                                  f"{plural(len(rows), 'commitment')} · {plural(rows['project_id'].nunique(), 'project')}"],
                                                  input_id="card", payload={"title": f"{short_type(t)} · {input.pick()}",
                                                                            "where": {"measure_name": input.pick(), "type_name": t}}))
                        return kit.cards(items)

                with ui.card():
                    ui.card_header("Where each project stands · by linked procurement")

                    @render.ui
                    def m_board():
                        return stand(lens_frame(), {"measure_name": input.pick()})

                with ui.card():
                    ui.card_header("Where · click a country")

                    @render_plotly
                    def m_map():
                        return lens_map("m_map", lens_frame(), {"measure_name": input.pick()})

                with ui.layout_columns(col_widths=[6, 6]):
                    with ui.card():
                        ui.card_header("Types by region · click a cell")

                        @render_plotly
                        def m_heat_region():
                            return heat("m_heat_region", lens_frame(), "type_name", "region", ylab=short_type, height=380,
                                        where={"measure_name": input.pick()})

                    with ui.card():
                        ui.card_header("Types by asset · click a cell")

                        @render_plotly
                        def m_heat_asset():
                            return heat("m_heat_asset", lens_frame(), "type_name", "asset_name", ylab=short_type, xlab=short_asset, height=380,
                                        where={"measure_name": input.pick()})


# ---------------------------------------------------------------- the pieces the views share

def facts(name, kind, df, definition=None, note=None):
    places = df.loc[~df["is_regional"].fillna(False).astype(bool), "country_code"].nunique()
    line = [plural(len(df), "commitment"), plural(df["project_id"].nunique(), "project"),
            f"{places} {'country' if places == 1 else 'countries'}"]
    if kind != "Measure":
        line.append(plural(df["label_set"].nunique(), "measure"))
    return cui.card(cui.card_body(
        cui.span(kind, class_="small text-secondary"), cui.h3(name, class_="h4 mb-2"),
        cui.p(definition, style="max-width: 80ch") if definition else None,
        cui.p(" · ".join(line), class_="mb-0"), cui.p(note, class_="small text-secondary mb-0") if note else None))


def heat(name, df, rows, cols, *, where=None, xlab=lambda v: v, ylab=lambda v: v, height=400):
    """A rows x cols grid of commitments; a click opens the cell's commitments."""
    if df.empty:
        return kit.empty("", "nothing under these filters")
    t = df.groupby([rows, cols]).size().unstack(fill_value=0)
    t = t.loc[t.sum(axis=1).sort_values(ascending=False).index, t.sum().sort_values(ascending=False).index]
    if W.NO_ASSET in t.columns:
        t = t[[c for c in t.columns if c != W.NO_ASSET] + [W.NO_ASSET]]
    z = [[int(v) if v else None for v in r] for r in t.values]
    fig = kit.heatmap(z, [xlab(x) for x in t.columns], [ylab(y) for y in t.index], height=height)
    keys = [[[y, x] for x in t.columns] for y in t.index]
    return clickable(name, fig, keys,
                     lambda k: open_drill(f"{ylab(k[0])} · {xlab(k[1])}", **(where or {}), **{rows: k[0], cols: k[1]}))


def bars(name, df, col, *, where=None, label=lambda v: v):
    if df.empty:
        return kit.empty("", "nothing under these filters")
    c = W.count(df, col)
    keys = c[col].tolist()
    fig = kit.bar([label(k) for k in keys], c["commitments"].tolist(), horizontal=True, height=max(260, 32 * len(c) + 60))
    return clickable(name, fig, keys, lambda k: open_drill(label(k), **(where or {}), **{col: k}))


def lens_map(name, df, where):
    c = W.count(df[~df["is_regional"].fillna(False).astype(bool)], "country_code", "place")
    fig = kit.world(c["country_code"], c["commitments"], c["place"], height=420)
    names = list(fig.data[0].text) if len(fig.data) else []
    return clickable(name, fig, names, lambda place: open_drill(place, **where, place=place))


def stand(df, where):
    """The board: a column per stage, a card per project; a click opens that
    project's commitments at that stage."""
    b = W.board(df)
    columns = []
    for s in W.STAGES:
        rows = b[b["stage"] == s]
        items = [kit.card(r.project_name, [f"{r.place} · {plural(int(r.commitments), 'commitment')}",
                                           "; ".join(short_type(t) for t in r.types[:3]) + (f" and {len(r.types) - 3} more" if len(r.types) > 3 else "")],
                          input_id="card", payload={"title": f"{r.project_name} · {s}",
                                                    "where": {**where, "project_id": r.project_id, "stage": s}})
                 for r in rows.itertuples()]
        columns.append((s, STAGE_STYLE.get(s, ""), items))
    return kit.board(columns, limit=8)
