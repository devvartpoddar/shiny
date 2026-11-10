# wbg — climate resilience commitments in World Bank appraisal documents for
# the digital assets a project finances (repository devvartpoddar/wbg-digital-
# resilience). Every query and every number computed beyond the views is in
# wbg_portfolio.app; this file only lays them out. Read only: no write, no
# model call. Two views: the overall picture, and one country, project, asset
# or measure at a time. Every chart counts commitments or projects, as the
# "Count" switch says; any bar, cell, country or card opens the projects and
# sentences behind it in the side panel. A comment, not a docstring: Express
# renders a module docstring onto the page.
from __future__ import annotations

import json
import time

import pandas as pd
import plotly.graph_objects as go
from shiny import reactive, render, req
from shiny import ui as cui
from shiny.express import input, ui
from shinywidgets import render_plotly

import kit
from wbg_portfolio import app as W

kit.page("WBG Digital Resilience", navbar="view")

LENSES = {"country": "Country", "project": "Project", "asset": "Asset", "measure": "Measure"}
LENS_COLUMN = {"country": "place", "project": "project_name", "asset": "asset_name", "measure": "measure_name"}
COHORTS = {"": "All projects", "digital": "Digital projects", "digital_contributor": "Projects with a digital part"}
COHORT_NOUN = {"": "projects", "digital": "digital projects", "digital_contributor": "projects with a digital part"}
UNITS = {"commitments": "Count: commitments", "projects": "Count: projects"}
STAGE_COLOR = {"Completed": "#1f8a70", "Under way": "#2458b3", "Coming up": "#c77d00",
               "Dropped": "#6b7280", "No package linked": "#6b7280"}
STAGE_STYLE = {s: f"color:{c}" for s, c in STAGE_COLOR.items()}
SENTENCES_SHOWN = 3     # per project in the side panel before "show more"
SENTENCES_MAX = 40      # per project, opened
OPEN_UP_TO = 4          # a side panel of this many projects or fewer shows them all open


def short_asset(a):
    if a == W.NO_ASSET:
        return "No asset named"
    for long, s in ((" and international connectivity", ""), (" and emergency communication systems", ""),
                    (" and terrestrial wireless networks", " and wireless"), (" and sensor networks", " and sensors"),
                    (" infrastructure", ""), (" systems and applications", " systems")):
        a = a.replace(long, s)
    return a


# The World Bank's own codes for its regions; the full name is in the hover.
REGION_SHORT = {"Eastern and Southern Africa": "AFE", "Western and Central Africa": "AFW",
                "East Asia and Pacific": "EAP", "Europe and Central Asia": "ECA",
                "Latin America and Caribbean": "LAC", "South Asia": "SAR",
                "Middle East, North Africa, Afghanistan, and Pakistan": "MENAAP",
                "Middle East and North Africa": "MENA"}


def short_region(r):
    return REGION_SHORT.get(r, r)


def short_type(t):
    return "No type" if t == W.NO_TYPE else t.removeprefix("OTH. ")


def plural(n, word):
    return f"{n:,} {word}{'' if n == 1 else 's'}"


def share_text(n, of):
    """'37 of 68 (54%)', or just the number when there is no base."""
    if of is None or pd.isna(of) or not of:
        return f"{int(n):,}"
    return f"{int(n):,} of {int(of):,} ({n / of:.0%})"


# ---------------------------------------------------------------- data

@reactive.calc
def frame():
    cohort = input.cohort() or None
    return kit.cached(("wbg", "commitments", cohort), lambda: W.commitments(kit.query_df, cohort))


@reactive.calc
def base():
    """The projects a share is taken of: every project of the cohort with a
    document read, with or without a commitment."""
    cohort = input.cohort() or None
    return kit.cached(("wbg", "projects", cohort), lambda: W.projects(kit.query_df, cohort))


@reactive.calc
def measure_table():
    return kit.cached(("wbg", "measures"), lambda: W.measures(kit.query_df))


@reactive.calc
def type_table():
    return kit.cached(("wbg", "types"), lambda: W.measure_types(kit.query_df))


@reactive.calc
def asset_table():
    return kit.cached(("wbg", "assets"), lambda: W.assets(kit.query_df))


def by_projects():
    return input.unit() == "projects"


def unit_word(n=2):
    return ("project" if by_projects() else "commitment") + ("" if n == 1 else "s")


def cohort_noun():
    return COHORT_NOUN.get(input.cohort() or "", "projects")


def lens_frame(lens=None, value=None):
    """The commitments of what is picked. While the picker still holds the
    last lens's value (the moment after the lens changes) this waits, so no
    output draws an empty state and then its real one a moment later: a
    chart replaced while it is still being set up never appears."""
    df = frame()
    lens, value = lens or input.lens(), value if value is not None else input.pick()
    out = df[df[LENS_COLUMN[lens]] == value] if value else df.iloc[0:0]
    req(len(out) > 0)
    return out


def lens_base(lens=None, value=None):
    """The projects a share inside a lens is taken of: a country's projects
    (with or without a commitment); for an asset or a measure, the projects
    that have it, so a type's share is of the measure's projects."""
    b = base()
    lens, value = lens or input.lens(), value if value is not None else input.pick()
    if lens in ("country", "project"):
        return b[b[LENS_COLUMN[lens]] == value]
    return b[b["project_id"].isin(lens_frame(lens, value)["project_id"])]


def tally(df, *by, of=None):
    """W.tally in the unit the switch says; of: the projects a share is taken
    of (default: every project of the cohort)."""
    return W.tally(df, *by, unit=input.unit(), base=base() if of is None else of)


def cell_text(r, one_base=False):
    """What a bar shows: the count; in the project view also its share, and
    its base ("6 of 10") unless every bar of the chart has the same base,
    which the chart then says once (base_note)."""
    if by_projects() and pd.notna(r["share"]):
        if one_base:
            return f"{int(r['n']):,} ({r['share']:.0%})"
        return f"{int(r['n']):,} of {int(r['of']):,} ({r['share']:.0%})"
    return f"{int(r['n']):,}"


def one_base(c):
    """Whether every row of a tally is a share of the same number of projects."""
    return by_projects() and c["of"].notna().all() and c["of"].nunique() == 1


def base_what(of):
    """In words, the projects a share is taken of (of as given to tally)."""
    if of is None:
        return f"{cohort_noun()} read"
    return {"country": f"{cohort_noun()} read here", "project": "projects",
            "asset": "projects with this asset", "measure": "projects with this measure"}[input.lens()]


def base_note(fig, c, of, *, below=False):
    """One line on a chart whose bars or cells all share a base: 'Projects, of
    68 digital projects read'. Over a bar chart; under a grid, whose column
    names sit along its top."""
    if not one_base(c):
        return fig
    fig.add_annotation(text=f"Projects, of {int(c['of'].iloc[0]):,} {base_what(of)}", xref="paper", yref="paper",
                       x=1, y=0 if below else 1, xanchor="right", yanchor="top" if below else "bottom",
                       yshift=-8 if below else 6, showarrow=False, font={"size": 12.5, "color": "#4b5563"})
    if below:
        fig.update_layout(margin_b=34, height=(fig.layout.height or 360) + 26)
    else:
        fig.update_layout(margin_t=30)
    return fig


def cell_hover(name, r):
    if by_projects():
        return f"{name}: {share_text(r['n'], r['of'])} projects"
    return f"{name}: {int(r['n']):,} commitments"


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
    if len(fig.data):
        fig.data[0].customdata = keys
    HANDLERS[name] = on_click
    return fig


CHARTS = ("ov_map", "ov_measure", "ov_asset", "ov_heat", "ov_stage", "ov_fy", "c_heat", "c_assets", "a_measures",
          "a_heat", "a_map", "m_map", "m_heat_region", "m_heat_asset")
for _name in CHARTS:
    kit.on_click(input, _name, lambda pt, n=_name: HANDLERS[n](pt["customdata"]) if n in HANDLERS and pt.get("customdata") is not None else None)


# ---------------------------------------------------------------- layout


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


def sentence_item(s, where):
    """One sentence of a project in the side panel: what it commits to
    (measure, solid), how (type, outline) and for what (asset, tint), where
    its procurement stands, then the words and their page."""
    measures = [] if "measure_name" in where else s["measures"]
    types = [] if "type_name" in where else [t for t in s["types"] if t != W.NO_TYPE]
    assets = [] if "asset_name" in where else [a for a in s["assets"] if a != W.NO_ASSET]
    stage = s["stage"]
    return cui.div(
        cui.div(cui.div(*[kit.tag(m, "solid", title="Measure") for m in measures],
                        *[kit.tag(short_type(t), "outline", title="Type") for t in types],
                        *[kit.tag(short_asset(a), "tint", title="Digital asset") for a in assets]),
                kit.dot(stage, STAGE_COLOR.get(stage), hollow=stage == "No package linked"),
                class_="d-flex justify-content-between align-items-start gap-2"),
        kit.quote(s["text"],
                  cui.a(f"page {int(s['page_number'])}", href=s["pdf_url"], target="_blank")
                  if s["pdf_url"] and pd.notna(s["page_number"]) else None),
        class_="mb-2")


with ui.sidebar(id="panel", position="right", open="closed", width=520, title="What is behind it"):

    @render.ui
    def panel_body():
        d = drill.get()
        if not d:
            return ui.p("Click a bar, a cell, a country or a card.")
        df = frame()
        for col, val in d["where"].items():
            df = df[df[col] == val]
        if df.empty:
            return cui.div(cui.h5(d["title"]), cui.p("Nothing under the filters set now."))
        sent = W.sentences(kit.query_df, df["commitment_id"]).merge(
            df[["commitment_id", "project_id", "measure_name", "type_name", "asset_name", "stage"]], on="commitment_id")
        order = {s: i for i, s in enumerate(W.STAGES)}
        # One row per project and sentence: a sentence behind several commitments (two
        # assets, two types) is shown once, with every tag it carries.
        per = (sent.sort_values("posterior_probability", ascending=False)
                   .groupby(["project_id", "text"], sort=False)
                   .agg(measures=("measure_name", lambda v: sorted(set(v))),
                        types=("type_name", lambda v: sorted(set(v))),
                        assets=("asset_name", lambda v: sorted(set(v))),
                        stage=("stage", lambda v: min(v, key=lambda s: order.get(s, 99))),
                        p=("posterior_probability", "max"), page_number=("page_number", "first"),
                        pdf_url=("pdf_url", "first"))
                   .reset_index().sort_values("p", ascending=False))
        projects = (df.groupby(["project_id", "project_name", "place"], dropna=False)
                      .agg(commitments=("commitment_id", "size"),
                           measures=("measure_name", lambda v: sorted(set(v))))
                      .reset_index().sort_values(["commitments", "project_name"], ascending=[False, True]))
        head = [cui.h5(d["title"], class_="mb-1"),
                cui.p(f"{plural(len(projects), 'project')} · {plural(len(df), 'commitment')} · "
                      f"{plural(len(per), 'sentence')} · {plural(df['place'].nunique(), 'place')}", class_="small mb-1"),
                cui.p(kit.tag("Measure", "solid"), kit.tag("Type", "outline"), kit.tag("Digital asset", "tint"),
                      class_="mb-2")]
        if len(projects) > OPEN_UP_TO:
            head.append(cui.p("Open a project for its sentences.", class_="small mb-2"))
        body = []
        for p in projects.itertuples():
            mine = per[per["project_id"] == p.project_id]
            rows = [sentence_item(s, d["where"]) for _, s in mine.head(SENTENCES_MAX).iterrows()]
            shown, more = rows[:SENTENCES_SHOWN], rows[SENTENCES_SHOWN:]
            lines = [p.place, f"{plural(int(p.commitments), 'commitment')} · {plural(len(mine), 'sentence')}"
                     + ("" if "measure_name" in d["where"] else f" · {plural(len(p.measures), 'measure')}")]
            body.append(kit.fold(
                p.project_name, lines, *shown,
                cui.tags.details(cui.tags.summary(f"Show {plural(len(more), 'more sentence')}",
                                                  class_="small fw-semibold text-primary mb-2", style="cursor:pointer"),
                                 *more) if more else None,
                cui.p(f"{len(mine) - SENTENCES_MAX:,} more are on the project's page.", class_="small")
                if len(mine) > SENTENCES_MAX else None,
                cui.tags.button("Open the project's page", type="button", class_="btn btn-sm btn-outline-primary",
                                onclick="Shiny.setInputValue('card', "
                                + json.dumps({"go": "project", "value": p.project_name}) + ", {priority: 'event'})"),
                open=len(projects) <= OPEN_UP_TO))
        return cui.div(*head, *body)


# ======================================================= overview
with ui.nav_panel("Overview"):
    ui.p("Climate resilience commitments in World Bank appraisal documents, for the digital assets a project "
         "finances. A commitment is one project, asset, measure and type. Click any bar, cell, country or card "
         "for the projects and sentences behind it.", class_="mt-3 mb-0", style="max-width: 110ch")

    @render.ui
    def tiles():
        df, b = frame(), base()
        h = W.headline(df)
        n, of = h["projects"], len(b)
        if by_projects():
            linked = df.loc[df["stage"] != "No package linked", "project_id"].nunique()
            share = "—" if not n else f"{linked / n:.0%}"
            linked_note = "of projects with a commitment · leads, not a full account"
        else:
            share = "—" if h["linked_share"] is None else f"{h['linked_share']:.0%}"
            linked_note = "of commitments · leads, not a full account"
        return cui.layout_column_wrap(
            kit.tile("Projects with a commitment", f"{n:,}",
                     f"of {of:,} {cohort_noun()} read ({n / of:.0%})" if of else None),
            kit.tile("Commitments", f"{h['commitments']:,}", "project × asset × measure × type"),
            kit.tile("Countries", f"{h['countries']:,}", "plus regional projects"),
            kit.tile("Measures", f"{h['measures']:,}"),
            kit.tile("With a linked package", share, linked_note, color="secondary"),
            width="200px", fill=False, class_="my-3")

    @render.ui
    def ov_note():
        if not by_projects():
            return None
        return cui.div(f"Counting projects: a project counts once in each bar or cell it has a commitment in, so the "
                       f"bars do not add up to the number of projects. A chart names its base once when every bar "
                       f"shares it (of the {len(base()):,} {cohort_noun()} with a document read); where the base "
                       f"differs by country, region or year, each bar or cell says \"6 of 10\".",
                       class_="alert alert-light border py-2 small mb-3")

    with ui.card():
        ui.card_header("Where")

        @render_plotly
        def ov_map():
            return lens_map("ov_map", frame(), None, height=460, click=lambda place: go_to("country", place))

        @render.text
        def ov_regional():
            reg = frame()[frame()["is_regional"].fillna(False).astype(bool)]
            n = reg["project_id"].nunique() if by_projects() else len(reg)
            return (f"{plural(n, unit_word(1))} {'are' if n != 1 else 'is'} regional and not on the map."
                    if by_projects() else
                    f"{plural(n, 'commitment')} sit in regional projects and are not on the map.")

    with ui.layout_columns(col_widths=[6, 6]):
        with ui.card():
            ui.card_header("By measure")

            @render_plotly
            def ov_measure():
                return bars("ov_measure", frame(), "measure_name", click=lambda m: go_to("measure", m))

        with ui.card():
            ui.card_header("By digital asset")

            @render_plotly
            def ov_asset():
                return bars("ov_asset", frame(), "asset_name", label=short_asset,
                            click=lambda a: go_to("asset", a) if a != W.NO_ASSET
                            else open_drill("No asset named", asset_name=W.NO_ASSET))

    with ui.card():
        ui.card_header("Measures by asset")

        @render_plotly
        def ov_heat():
            return heat("ov_heat", frame(), "measure_name", "asset_name", xlab=short_asset)

    with ui.layout_columns(col_widths=[7, 5]):
        with ui.card():
            ui.card_header("By approval year")

            @render_plotly
            def ov_fy():
                c = tally(frame(), "approval_fiscal_year").dropna(subset=["approval_fiscal_year"]) \
                    .sort_values("approval_fiscal_year")
                if c.empty:
                    return kit.empty("", "nothing under these filters")
                names = [f"FY{int(y)}" for y in c["approval_fiscal_year"]]
                fig = kit.bar(names, c["n"].tolist(), height=300, text=[cell_text(r) for _, r in c.iterrows()],
                              hover=[cell_hover(k, r) for k, (_, r) in zip(names, c.iterrows())])
                fig.update_xaxes(type="category")
                return clickable("ov_fy", fig, c["approval_fiscal_year"].tolist(),
                                 lambda y: open_drill(f"Approved in FY{int(y)}", approval_fiscal_year=y))

        with ui.card():
            ui.card_header("Linked procurement so far")

            @render_plotly
            def ov_stage():
                c = tally(frame(), "stage").set_index("stage").reindex(W.STAGES[:-1]).reset_index()
                c["n"] = c["n"].fillna(0)
                same = one_base(c.dropna(subset=["of"])) if by_projects() else False
                fig = kit.bar(c["stage"].tolist(), c["n"].astype(int).tolist(), horizontal=True,
                              text=[cell_text(r, same) for _, r in c.iterrows()],
                              hover=[cell_hover(r["stage"], r) for _, r in c.iterrows()])
                if same:
                    base_note(fig, c.dropna(subset=["of"]), None)
                return clickable("ov_stage", fig, c["stage"].tolist(), lambda s: open_drill(f"Linked procurement: {s}", stage=s))

            ui.p("Package links are found for about a third of commitments.", class_="small")

# ======================================================= explore
with ui.nav_panel("Explore"):
    with ui.div(class_="d-flex flex-wrap gap-3 align-items-end my-3"):
        ui.input_radio_buttons("lens", "Look at one", LENSES, selected="country", inline=True)
        ui.input_selectize("pick", None, choices=[], width="460px")

    @reactive.effect
    def _pick_choices():
        df, lens = frame(), input.lens()
        col = LENS_COLUMN[lens]
        c = W.count(df, col)
        c = c[c[col] != W.NO_ASSET]
        with reactive.isolate():
            # Keep what was picked when only the cohort changed.
            want = pending_pick.get() or input.pick()
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
            return facts(input.pick(), "Country or region", df, of=lens_base(), of_what=f"{cohort_noun()} read here")

        with ui.card():
            ui.card_header("Its projects")

            @render.ui
            def c_projects():
                df = lens_frame()
                items = []
                for (pid, pname), rows in df.groupby(["project_id", "project_name"]):
                    ms = sorted(rows["measure_name"].unique())
                    items.append(kit.card(pname, [f"{plural(len(rows), 'commitment')} · {plural(len(ms), 'measure')}",
                                                  " · ".join(ms)],
                                          input_id="card", payload={"title": f"{pname} in {input.pick()}",
                                                                    "where": {"project_id": pid}}))
                return kit.cards(items)

        with ui.card():
            ui.card_header("Who commits to what")

            @render_plotly
            def c_heat():
                return heat("c_heat", lens_frame(), "measure_name", "project_name", where={"place": input.pick()},
                            of=lens_base(), x_chars=18)

        with ui.card():
            ui.card_header("Where each project stands, by linked procurement")

            @render.ui
            def c_board():
                return stand(lens_frame(), {"place": input.pick()})

        with ui.card():
            ui.card_header("Digital assets")

            @render_plotly
            def c_assets():
                return bars("c_assets", lens_frame(), "asset_name", where={"place": input.pick()}, label=short_asset,
                            of=lens_base())

    # ---------------------------------------------- one project
    with ui.panel_conditional("input.lens === 'project'"):

        @reactive.calc
        def project_parts():
            df = lens_frame("project", input.pick())
            if df.empty:
                return None
            pid = df["project_id"].iloc[0]
            return kit.cached(("wbg", "project", pid), lambda: W.project(kit.query_df, pid))

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
                cui.p(" · ".join(str(b) for b in bits if b), class_="mb-1", style="color:#4b5563"),
                cui.p(f"{plural(len(df), 'commitment')} under {plural(df['label_set'].nunique(), 'measure')} · "
                      f"{plural(len(parts['packages']), 'linked package')}", class_="mb-0 fw-semibold")))

        with ui.layout_columns(col_widths=[6, 6]):
            with ui.card():
                ui.card_header("What it commits to, with the strongest sentence")

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
                        types = sorted({short_type(t) for t in rows["type_name"] if t != W.NO_TYPE})
                        assets = sorted({short_asset(a) for a in rows["asset_name"] if a != W.NO_ASSET})
                        out.append(cui.div(
                            kit.card(m, [plural(len(rows), "commitment")], input_id="card",
                                     payload={"title": f"{m} · {input.pick()}",
                                              "where": {"project_name": input.pick(), "measure_name": m}}),
                            cui.div(*[kit.tag(t, "outline", title="Type") for t in types],
                                    *[kit.tag(a, "tint", title="Digital asset") for a in assets], class_="mt-1"),
                            kit.quote(b["text"].iloc[0],
                                      cui.a(f"page {int(b['page_number'].iloc[0])}", href=b["pdf_url"].iloc[0], target="_blank")
                                      if pd.notna(b["page_number"].iloc[0]) else None) if len(b) else None,
                            class_="mb-3"))
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
                                   horizontal=True)

              with ui.card():
                ui.card_header("Components, with cost from all funding sources")

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
            ui.card_header("Its linked packages: each bubble is a package, sized by estimated value")

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
                fig.update_yaxes(automargin=True)
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
                ui.card_header("Measures committed for it")

                @render_plotly
                def a_measures():
                    return bars("a_measures", lens_frame(), "measure_name", where={"asset_name": input.pick()},
                                of=lens_base(), wrap_at=28)

            with ui.card():
                ui.card_header("Measures by region")

                @render_plotly
                def a_heat():
                    return heat("a_heat", lens_frame(), "measure_name", "region", where={"asset_name": input.pick()},
                                of=lens_base(), xlab=short_region, y_chars=24, x_chars=9)

        with ui.card():
            ui.card_header("Where each project stands, by linked procurement")

            @render.ui
            def a_board():
                return stand(lens_frame(), {"asset_name": input.pick()})

        with ui.card():
            ui.card_header("Where")

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
            ui.card_header("The types")

            @render.ui
            def m_types():
                df = lens_frame()
                if df.empty:
                    return None
                defs = type_table()
                defs = defs[defs["label_set"] == df["label_set"].iloc[0]].drop_duplicates("type_name").set_index("type_name")["definition"]
                of = df["project_id"].nunique()
                c = W.tally(df, "type_name", unit=input.unit())
                counts = df.groupby("type_name").agg(commitments=("commitment_id", "size"),
                                                     projects=("project_id", "nunique"))
                items = []
                for t in c["type_name"]:
                    k = counts.loc[t]
                    items.append(kit.card(short_type(t), [f"{share_text(k['projects'], of)} projects · "
                                                          f"{plural(int(k['commitments']), 'commitment')}",
                                                          defs.get(t, "Commitments that name no specific type." if t == W.NO_TYPE else "")],
                                          input_id="card", payload={"title": f"{short_type(t)} · {input.pick()}",
                                                                    "where": {"measure_name": input.pick(), "type_name": t}}))
                return kit.cards(items)

        with ui.card():
            ui.card_header("Where each project stands, by linked procurement")

            @render.ui
            def m_board():
                return stand(lens_frame(), {"measure_name": input.pick()})

        with ui.card():
            ui.card_header("Where")

            @render_plotly
            def m_map():
                return lens_map("m_map", lens_frame(), {"measure_name": input.pick()})

        with ui.layout_columns(col_widths=[6, 6]):
            with ui.card():
                ui.card_header("Types by region")

                @render_plotly
                def m_heat_region():
                    return heat("m_heat_region", lens_frame(), "type_name", "region", ylab=short_type,
                                xlab=short_region, where={"measure_name": input.pick()}, of=lens_base(),
                                y_chars=24, x_chars=9)

            with ui.card():
                ui.card_header("Types by asset")

                @render_plotly
                def m_heat_asset():
                    return heat("m_heat_asset", lens_frame(), "type_name", "asset_name", ylab=short_type, xlab=short_asset,
                                where={"measure_name": input.pick()}, of=lens_base(), y_chars=24, x_chars=10)


ui.nav_spacer()

with ui.nav_control():
    with ui.div(class_="d-flex gap-2 align-items-center"):
        ui.input_select("unit", None, UNITS, selected="commitments", width="200px")
        ui.input_select("cohort", None, COHORTS, selected="", width="210px")
        ui.input_selectize("find", None, choices=[], width="350px",
                           options={"placeholder": "Find a country, project, asset or measure"})


# ---------------------------------------------------------------- the pieces the views share

def facts(name, kind, df, definition=None, note=None, *, of=None, of_what=None):
    """The head of a lens: what it is, and how many projects of how many have
    it (of: the projects it could be; default every project of the cohort)."""
    b = base() if of is None else of
    places = df.loc[~df["is_regional"].fillna(False).astype(bool), "country_code"].nunique()
    n = df["project_id"].nunique()
    line = [f"{share_text(n, len(b))} {of_what or cohort_noun() + ' read'}", plural(len(df), "commitment")]
    if places and kind != "Country or region":
        line.append(f"{places} {'country' if places == 1 else 'countries'}")
    if kind != "Measure":
        line.append(plural(df["label_set"].nunique(), "measure"))
    return cui.card(cui.card_body(
        cui.span(kind, class_="small", style="color:#4b5563"), cui.h3(name, class_="h4 mb-2"),
        cui.p(definition, style="max-width: 80ch") if definition else None,
        cui.p(" · ".join(line), class_="mb-0 fw-semibold"),
        cui.p(note, class_="small mb-0", style="color:#4b5563") if note else None))


def heat(name, df, rows, cols, *, where=None, of=None, xlab=lambda v: v, ylab=lambda v: v, height=None,
         x_chars=13, y_chars=34):
    """A rows x cols grid of commitments or projects; a click opens the
    cell. In the project view a cell's hover gives its share."""
    if df.empty:
        return kit.empty("", "nothing under these filters")
    c = tally(df, rows, cols, of=of)
    t = c.pivot(index=rows, columns=cols, values="n")
    r_order, c_order = tally(df, rows, of=of)[rows].tolist(), tally(df, cols, of=of)[cols].tolist()
    if W.NO_ASSET in c_order:
        c_order = [x for x in c_order if x != W.NO_ASSET] + [W.NO_ASSET]
    t = t.reindex(index=r_order, columns=c_order)
    z = [[int(v) if pd.notna(v) and v else None for v in r] for r in t.values]
    look = {(r[rows], r[cols]): r for _, r in c.iterrows()}
    # The hover names the row and column in full, whatever the axis shortens them to.
    full = (lambda v: v) if cols == "region" else xlab
    hover = [[cell_hover(f"{ylab(y)} · {full(x)}", look[(y, x)]) if (y, x) in look else "" for x in t.columns]
             for y in t.index]
    text = None
    if by_projects() and not one_base(c):
        # A cell says how many projects of how many: the count, and its base under it.
        text = [[f"<b>{int(look[(y, x)]['n']):,}</b><br>of {int(look[(y, x)]['of']):,}"
                 if (y, x) in look and pd.notna(look[(y, x)]["of"]) else ("" if (y, x) not in look else f"{int(look[(y, x)]['n']):,}")
                 for x in t.columns] for y in t.index]
    fig = kit.heatmap(z, [xlab(x) for x in t.columns], [ylab(y) for y in t.index], height=height,
                      hovertext=hover, text=text, x_chars=x_chars, y_chars=y_chars)
    if text is not None:
        fig.update_traces(textfont={"size": 11})
    base_note(fig, c, of, below=True)
    keys = [[[y, x] for x in t.columns] for y in t.index]
    return clickable(name, fig, keys,
                     lambda k: open_drill(f"{ylab(k[0])} · {xlab(k[1])}", **(where or {}), **{rows: k[0], cols: k[1]}))


def bars(name, df, col, *, where=None, of=None, label=lambda v: v, click=None, wrap_at=34):
    """Horizontal bars of commitments or projects per value of col; a click
    opens the bar (or calls click)."""
    if df.empty:
        return kit.empty("", "nothing under these filters")
    c = tally(df, col, of=of)
    if col == "asset_name":
        c = pd.concat([c[c[col] != W.NO_ASSET], c[c[col] == W.NO_ASSET]])
    keys = c[col].tolist()
    same = one_base(c)
    fig = kit.bar([label(k) for k in keys], c["n"].tolist(), horizontal=True, wrap_at=wrap_at,
                  text=[cell_text(r, same) for _, r in c.iterrows()],
                  hover=[cell_hover(label(r[col]), r) for _, r in c.iterrows()])
    base_note(fig, c, of)
    return clickable(name, fig, keys, click or (lambda k: open_drill(label(k), **(where or {}), **{col: k})))


def lens_map(name, df, where, *, height=420, click=None):
    """Countries with a commitment. In the project view a country's hover
    says how many of its projects (of the cohort) are in the frame."""
    c = tally(df[~df["is_regional"].fillna(False).astype(bool)], "country_code", "place")
    if c.empty:
        return kit.empty("", "nothing on the map under these filters")
    fig = kit.world(c["country_code"], c["n"], c["place"], height=height, label=unit_word(),
                    hover=[cell_hover(r["place"], r) for _, r in c.iterrows()])
    names = list(fig.data[0].text) if len(fig.data) else []
    return clickable(name, fig, names, click or (lambda place: open_drill(place, **where, place=place)))


def stand(df, where):
    """The board: a column per stage, a card per project; a click opens that
    project's commitments at that stage. A project with commitments at
    several stages has a card in each."""
    b = W.board(df)
    columns = []
    for s in W.STAGES:
        rows = b[b["stage"] == s]
        items = [kit.card(r.project_name, [f"{r.place} · {plural(int(r.commitments), 'commitment')}",
                                           "; ".join(short_type(t) for t in r.types[:2]) + (f" and {len(r.types) - 2} more" if len(r.types) > 2 else "")],
                          input_id="card", payload={"title": f"{r.project_name} · {s}",
                                                    "where": {**where, "project_id": r.project_id, "stage": s}})
                 for r in rows.itertuples()]
        columns.append((s, STAGE_STYLE.get(s, ""), items))
    return kit.board(columns, limit=8)
