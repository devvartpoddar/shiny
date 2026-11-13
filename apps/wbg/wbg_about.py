# The About view of the wbg app: definitions, scope, the pipeline as one
# figure with the count each step passes on, the models and the limitations.
# page(n) takes wbg_portfolio.app.about()'s counts and returns the HTML; a
# count that is missing is left off the figure. Nothing here queries anything.
from __future__ import annotations

import html
import textwrap

CSS = """
.wbg-about{--paper:var(--bs-body-bg,#fff);--ink:var(--bs-body-color,#1b1f24);--mist:var(--bs-light,#f4f5f7);
  --line:var(--bs-border-color,#d9dde3);--soft:#4b5563;--faint:#6b7280;--blue:var(--bs-primary,#2458b3);
  --wash:#e8eefa;--grey:#9aa1ac;max-width:1350px;padding-bottom:40px}
.wbg-about h2{font-size:1.75rem;font-weight:600;margin:1.25rem 0 .4rem}
.wbg-about h3{font-size:1.2rem;font-weight:600;margin:0 0 .25rem}
.wbg-about section{margin-top:2.6rem}
.wbg-about .lede,.wbg-about .sub{color:var(--soft);max-width:72ch}
.wbg-about .sub{margin-bottom:1rem}
.wbg-about .asof{font-size:.8rem;color:var(--faint);margin-top:.5rem}
.wbg-about dl.words{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:0 32px;margin:0}
.wbg-about dl.words div{padding:11px 0;border-top:1px solid var(--line);min-width:0}
.wbg-about dt{font-weight:600}
.wbg-about dd{margin:2px 0 0;color:var(--soft);font-size:.93rem}
.wbg-about figure{margin:0}
.wbg-about .scroll{overflow-x:auto;border:1px solid var(--line);border-radius:12px;padding:10px;background:var(--paper)}
.wbg-about .scroll svg{display:block;width:100%;min-width:1040px;height:auto}
.wbg-about svg .band{fill:var(--mist)}
.wbg-about svg .bl{font-size:10.5px;letter-spacing:.12em;font-weight:600;fill:var(--faint)}
.wbg-about svg .n{fill:var(--paper);stroke:var(--grey);stroke-width:1.2}
.wbg-about svg .n.src{stroke:var(--ink);stroke-width:1.4}
.wbg-about svg .n.mod{fill:var(--wash);stroke:var(--blue)}
.wbg-about svg .n.man{stroke:var(--grey);stroke-dasharray:5 4}
.wbg-about svg .n.st{stroke:var(--ink);stroke-width:1.6}
.wbg-about svg .n.out{fill:var(--ink);stroke:var(--ink)}
.wbg-about svg .t{font-size:13.5px;font-weight:600;fill:var(--ink)}
.wbg-about svg .d{font-size:11.5px;fill:var(--soft)}
.wbg-about svg .tag{font-size:9.5px;font-weight:600;letter-spacing:.08em;fill:var(--blue)}
.wbg-about svg .id{fill:var(--ink)}
.wbg-about svg .id.mod{fill:var(--blue)}
.wbg-about svg .id.out{fill:var(--paper)}
.wbg-about svg .idt{font-size:10px;font-weight:600;font-family:var(--bs-font-monospace,monospace);fill:var(--paper)}
.wbg-about svg .idt.out{fill:var(--ink)}
.wbg-about svg .h{font-size:10.5px;font-weight:600;letter-spacing:.08em;fill:var(--soft)}
.wbg-about svg .pill{fill:var(--paper);stroke:var(--line)}
.wbg-about svg .pt{font-size:11px;font-family:var(--bs-font-monospace,monospace);fill:var(--ink)}
.wbg-about svg .e{fill:none;stroke:var(--ink);stroke-width:1.4}
.wbg-about svg .e.dash{stroke:var(--grey);stroke-dasharray:4 4}
.wbg-about svg .mk{fill:var(--ink)}
.wbg-about svg .mkd{fill:var(--grey)}
.wbg-about svg .n.out ~ text.t,.wbg-about svg .n.out ~ text.d{fill:var(--paper)}
.wbg-about figcaption{color:var(--soft);font-size:.88rem;max-width:90ch;margin-top:10px}
.wbg-about .key{display:flex;flex-wrap:wrap;gap:8px 20px;list-style:none;margin:12px 0 0;padding:0;font-size:.85rem;color:var(--soft)}
.wbg-about .key li{display:flex;gap:7px;align-items:center}
.wbg-about .key i{width:16px;height:12px;border-radius:3px;border:1.4px solid var(--grey);background:var(--paper)}
.wbg-about .key .mod{background:var(--wash);border-color:var(--blue)}
.wbg-about .key .man{border-style:dashed}
.wbg-about .key .st{border-color:var(--ink);border-radius:8px}
.wbg-about .key .ar{width:26px;height:0;border-top:1.6px solid var(--ink)}
.wbg-about .key .ar.d{border-top:1.6px dashed var(--grey)}
.wbg-about .models{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}
.wbg-about .model{border:1px solid var(--line);border-radius:10px;padding:14px 16px;min-width:0;background:var(--paper)}
.wbg-about .model .role{font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;font-weight:600;color:var(--blue)}
.wbg-about .model h4{font-size:1rem;font-weight:600;margin:2px 0}
.wbg-about .model code{font-size:.78rem;color:var(--faint);overflow-wrap:anywhere}
.wbg-about .model p{color:var(--soft);font-size:.93rem;margin:6px 0 0}
.wbg-about .scale{margin-top:22px;max-width:820px}
.wbg-about .scale .strip,.wbg-about .scale .brace{display:grid;grid-template-columns:repeat(4,1fr);gap:3px}
.wbg-about .scale .g{padding:9px 10px;background:var(--mist);border-radius:6px;font-size:.85rem;min-width:0;color:var(--soft)}
.wbg-about .scale .g b{display:block;font-size:1rem;color:var(--ink)}
.wbg-about .scale .g.y{background:var(--wash)}
.wbg-about .scale .brace{margin-top:5px;font-size:.82rem;color:var(--soft)}
.wbg-about .scale .brace div:last-child{grid-column:3/5;border-top:2px solid var(--blue);padding-top:5px}
.wbg-about .cover{display:grid;gap:8px;max-width:820px}
.wbg-about .cover .row{display:grid;grid-template-columns:54px 1fr;gap:12px;align-items:start}
.wbg-about .cover .num{font-weight:600;font-size:1.3rem;line-height:26px;text-align:right;font-variant-numeric:tabular-nums}
.wbg-about .cover .b{height:26px;border-radius:5px;background:var(--blue);min-width:4px}
.wbg-about .cover .cell{min-width:0;display:grid;gap:4px}
.wbg-about .cover .lab{font-size:.9rem}
.wbg-about .cover .lab small{color:var(--faint);display:block;font-size:.82rem}
.wbg-about ol.limits{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:0 36px;counter-reset:l}
.wbg-about ol.limits li{counter-increment:l;padding:14px 0 14px 34px;border-top:1px solid var(--line);position:relative;min-width:0}
.wbg-about ol.limits li::before{content:counter(l);position:absolute;left:0;top:14px;font-weight:600;font-size:.78rem;line-height:22px;width:22px;height:22px;text-align:center;border-radius:50%;background:var(--mist);color:var(--soft)}
.wbg-about ol.limits h4{margin:0 0 3px;font-size:1rem;font-weight:600}
.wbg-about ol.limits p{color:var(--soft);font-size:.93rem;margin:0}
.wbg-about ol.limits .next{margin-top:5px;color:var(--ink);font-size:.88rem}
"""

MODELS = {"embedding": "openai/text-embedding-3-large", "decision": "typesafe/jev-1.13-20260917",
          "generative": "anthropic/claude-haiku-5.5"}


def _n(v, unit=None):
    """'1,234 sentences', or None when the count is missing."""
    if v is None:
        return None
    s = f"{int(v):,}"
    return f"{s} {unit}" if unit else s


def _p(v, fallback):
    """A threshold as '0.80', from the control panel when it is given."""
    return f"{float(v if v is not None else fallback):.2f}"


class _Figure:
    """The pipeline drawn as SVG: boxes on a fixed grid, arrows with a count."""
    W, H = 1350, 1530

    def __init__(self):
        self.o, self.top = [], []

    @staticmethod
    def wrap(text, w):
        return textwrap.wrap(text, max(10, int((w - 28) / 6.35)))

    def box(self, x, y, w, h, kind, sid, title, text="", model=None):
        store = kind == "st"
        self.o.append(f'<rect class="n {kind}" x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2 if store else 8}"/>')
        tx, ty = x + (26 if store else 14), y + 24
        if model:
            self.o.append(f'<text class="tag" x="{tx}" y="{y + 18}">{html.escape(model)}</text>')
            ty = y + 40
        cw = 0
        if sid:
            cw = len(sid) * 7 + 10
            self.o.append(f'<rect class="id {kind}" x="{tx}" y="{ty - 13}" width="{cw}" height="17" rx="4"/>'
                          f'<text class="idt {kind}" x="{tx + cw / 2}" y="{ty}" text-anchor="middle">{sid}</text>')
            cw += 7
        self.o.append(f'<text class="t" x="{tx + cw}" y="{ty}">{html.escape(title)}</text>')
        for i, line in enumerate(self.wrap(text, w - (24 if store else 0))):
            self.o.append(f'<text class="d" x="{tx}" y="{ty + 19 + i * 15}">{html.escape(line)}</text>')

    def arrow(self, pts, label=None, side="r", at=None, dash=False):
        p = " ".join(f"{x},{y}" for x, y in pts)
        self.o.append(f'<polyline class="e{" dash" if dash else ""}" points="{p}" marker-end="url(#wbg-{"ahd" if dash else "ah"})"/>')
        if not label:
            return
        tw = len(label) * 6.6 + 16
        if at:
            px, py = at
        else:
            (_, y1), (x2, y2) = pts[-2], pts[-1]
            py = (y1 + y2) / 2
            px = x2 + 9 if side == "r" else x2 - 9 - tw
        self.top.append(f'<rect class="pill" x="{px:.0f}" y="{py - 11:.0f}" width="{tw:.0f}" height="22" rx="11"/>'
                        f'<text class="pt" x="{px + 8:.0f}" y="{py + 4:.0f}">{html.escape(label)}</text>')

    def band(self, y, h, label):
        self.o.append(f'<rect class="band" x="26" y="{y}" width="{self.W - 26}" height="{h}" rx="10"/>'
                      f'<text class="bl" transform="translate(15,{y + h / 2}) rotate(-90)" text-anchor="middle">{label}</text>')

    def svg(self, label):
        marker = ('<marker id="wbg-{i}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" '
                  'orient="auto-start-reverse"><path class="{c}" d="M0,0.5 L10,5 L0,9.5 z"/></marker>')
        return (f'<svg viewBox="0 0 {self.W} {self.H}" role="img" aria-label="{html.escape(label)}"><defs>'
                + marker.format(i="ah", c="mk") + marker.format(i="ahd", c="mkd") + "</defs>"
                + "".join(self.o) + "".join(self.top) + "</svg>")


def figure(n: dict) -> str:
    """The pipeline figure. Steps are numbered in three groups: P preparation,
    C classification, O combination and output. The same step applied to
    measures and to assets carries the same number."""
    g = lambda group, key: (n.get(group) or {}).get(key)
    fl, st = n.get("floors") or {}, n.get("settings") or {}
    floor, cyber = _p(fl.get("floor.default"), 0.8), _p(fl.get("floor.cyber_security"), 0.9)
    f_type, f_pair = _p(fl.get("floor.types"), 0.7), _p(st.get("pair_check_floor"), 0.58)
    f_asset, f_pkg, f_link = _p(fl.get("asset.floor"), 0.8), _p(fl.get("link.asset_yes"), 0.67), _p(st.get("link_floor"), 0.7)
    f = _Figure()
    AX, AW, MX, MW, BX, BW, FX, FW, CX, CW, DX, DW = 44, 156, 222, 160, 410, 290, 722, 148, 892, 208, 1122, 204
    ax, mx, bx, cx, dx = AX + AW / 2, MX + MW / 2, BX + BW / 2, CX + CW / 2, DX + DW / 2
    TX, TW = 560, 430
    tx = TX + TW / 2
    for y, h, lab in ((6, 92, "SOURCES"), (106, 264, "PREPARATION"), (378, 762, "CLASSIFICATION"), (1148, 104, "STORES"),
                      (1260, 264, "COMBINATION AND OUTPUT")):
        f.band(y, h, lab)
    f.box(AX, 24, AW, 58, "src", None, "Project records", "Projects database")
    f.box(TX, 24, TW, 58, "src", None, "Project documents", "Appraisal documents and later project papers")
    f.box(DX, 24, DW, 58, "src", None, "Procurement records", "Plans, notices, contracts")
    f.box(TX, 140, TW, 86, "rule", "P1", "Read and split",
          "Each PDF is read into paragraphs, then sentences. Every sentence keeps its page, section and project component.")
    f.box(TX, 266, TW, 76, "mod", "P2", "Embed", "Each sentence is converted to a vector of its meaning.", "EMBEDDING MODEL")
    f.box(DX, 140, DW, 106, "rule", "P3", "Clean and reconcile",
          "One line per package across plan versions. Status from plan, notices and contracts.")
    f.box(DX, 280, DW, 76, "mod", "P4", "Embed", "Descriptions to vectors.", "EMBEDDING MODEL")
    sentences, packages = _n(g("text", "sentences"), "sentences"), _n(g("procurement", "packages"), "packages")
    f.arrow([(tx, 82), (tx, 140)], _n(g("text", "documents"), "documents"))
    f.arrow([(tx, 226), (tx, 266)], sentences)
    records = [_n(g("procurement", "plans"), "plans"), _n(g("procurement", "notices"), "notices"),
               _n(g("procurement", "contracts"), "contracts")]
    f.arrow([(dx, 82), (dx, 140)], " · ".join(r for r in records if r) or None, "l")
    f.arrow([(dx, 246), (dx, 280)], packages, "l")
    f.arrow([(tx, 342), (tx, 396), (bx, 396), (bx, 430)], sentences, at=(tx + 10, 369))
    f.arrow([(tx, 396), (cx, 396), (cx, 430)])
    heads = ((bx, f"MEASURES · {_n(g('labels', 'measures')) or ''}"), (cx, f"DIGITAL ASSETS · {_n(g('labels', 'assets')) or ''}"),
             (dx, "PACKAGES"))
    for x, t in heads:
        f.o.append(f'<text class="h" x="{x - 14}" y="420" text-anchor="end">{t.rstrip(" ·")}</text>')
    f.o.append(f'<text class="h" x="{MX}" y="420">INPUTS</text>')

    def routes(group):
        a, b = _n(g(group, "by_similarity")), _n(g(group, "by_pattern"))
        return f" {a} kept by similarity, {b} by pattern." if a and b else ""
    # measures
    f.box(BX, 430, BW, 134, "mod", "C1", "Shortlist",
          "Kept if the sentence’s vector is close enough (cosine similarity) to one of the measure’s search phrases, "
          "or it matches a word pattern." + routes("measure_routes"), "EMBEDDING MODEL")
    f.box(BX, 604, BW, 134, "mod", "C2", "Grade",
          "Each kept sentence is read with the measure’s definition. The model returns a probability for each grade, "
          "0 to 3. Probability of commitment = P(grade 2) + P(grade 3).", "DECISION MODEL")
    f.box(BX, 778, BW, 74, "rule", "C4", "Apply threshold",
          f"Kept if the probability is {floor} or more ({cyber} for cybersecurity).")
    tested = _n(g("measures", "overlap_tested"), "sentences tested")
    f.box(BX, 886, BW, 120, "mod", "C5", "Resolve overlaps",
          "A sentence kept by two measures is tested again for each, with the other definition beside it. "
          f"Kept at {f_pair} or more." + (f" {tested}." if tested else ""), "DECISION MODEL")
    f.box(BX, 1040, BW, 92, "mod", "C6", "Assign types",
          f"Each sentence takes every type of its measure it fits at {f_type} or more.", "DECISION MODEL")
    kept = _n(g("measures", "kept"), "sentences")
    f.arrow([(bx, 564), (bx, 604)], _n(g("measure_routes", "shortlisted"), "sentences"))
    f.arrow([(bx, 738), (bx, 778)], _n(g("measure_routes", "graded"), "sentences"))
    f.arrow([(bx, 852), (bx, 886)], _n(g("measures", "at_threshold"), "sentences"))
    f.arrow([(bx, 1006), (bx, 1040)], kept)
    typed = _n(g("measures", "with_type"))
    f.arrow([(bx, 1132), (bx, 1174)], f"{kept} · {typed} with a type" if kept and typed else kept)
    # assets
    f.box(CX, 430, CW, 134, "mod", "C1", "Shortlist",
          "As for measures, with each asset’s phrases and patterns." + routes("asset_routes"), "EMBEDDING MODEL")
    f.box(CX, 604, CW, 134, "mod", "C2", "Grade", "As for measures: does the project finance this asset?", "DECISION MODEL")
    f.box(CX, 778, CW, 90, "rule", "C4", "Apply threshold",
          f"Kept if the probability is {f_asset} or more. The most probable asset is kept.")
    with_asset = _n(g("assets", "at_threshold"), "sentences")
    f.arrow([(cx, 564), (cx, 604)], _n(g("asset_routes", "shortlisted"), "sentences"), "l")
    f.arrow([(cx, 738), (cx, 778)], _n(g("asset_routes", "graded"), "sentences"), "l")
    f.arrow([(cx, 868), (cx, 1174)], with_asset, "l", at=(cx - 9 - 121, 1010))
    # feedback
    added = [_n(g("measure_routes", "feedback_added")), _n(g("asset_routes", "feedback_added"))]
    f.box(FX, 596, FW, 154, "mod", "C3", "Feedback",
          "Sentences closest to those graded 2 or 3 are graded next."
          + (f" Adds {added[0]} (measures) and {added[1]} (assets)." if all(added) else ""), "EMBEDDING MODEL")
    f.arrow([(BX + BW, 650), (FX - 1, 650)])
    f.arrow([(FX, 694), (BX + BW + 1, 694)])
    f.arrow([(CX, 650), (FX + FW + 1, 650)])
    f.arrow([(FX + FW, 694), (CX - 1, 694)])
    # inputs
    graded = _n(g("grades", "graded_sentences"), "sentences")
    td, tp = _n(g("labels", "types_defined")), _n(g("labels", "types_proposed"))
    f.box(MX, 430, MW, 104, "man", None, "Search terms", "Search phrases and word patterns for each measure and asset.")
    f.box(MX, 604, MW, 104, "man", None, "Definitions", "One for each measure and asset, with one 0 to 3 grade scale.")
    f.box(MX, 768, MW, 96, "man", None, "Thresholds", "Set against graded samples" + (f": {graded}." if graded else "."))
    f.box(MX, 892, MW, 104, "mod", "C7", "Propose types", "Proposes further types for sentences that fit none.",
          "GENERATIVE MODEL")
    f.box(MX, 1030, MW, 106, "man", None, "Types",
          (f"{td} defined manually. {tp} proposed in C7 and accepted manually." if td and tp
           else "Defined manually, or proposed in C7 and accepted manually."))
    for y in (482, 656, 815, 1100):
        f.arrow([(MX + MW, y), (BX - 1, y)], dash=True)
    f.arrow([(BX, 1070), (BX - 14, 1070), (BX - 14, 944), (MX + MW + 1, 944)])
    f.arrow([(mx, 996), (mx, 1030)])
    # packages
    buys = _n(g("procurement", "with_asset"), "packages")
    f.box(DX, 430, DW, 166, "mod", "C8", "Assign assets",
          f"The four assets closest to the package are tested: does it buy or build this asset? Assigned at {f_pkg} or more."
          + (f" {buys} buy or build a digital asset." if buys else ""), "DECISION MODEL")
    f.arrow([(dx, 356), (dx, 430)], packages, "l")
    f.arrow([(dx, 596), (dx, 1174)], packages, "l", at=(dx - 9 - 115, 1010))
    # stores
    f.box(AX, 1174, AW, 56, "st", None, "Projects", "Project fields")
    f.box(BX, 1174, BW, 56, "st", None, "Measure findings", "Sentence, measure, type, probability")
    f.box(CX, 1174, CW, 56, "st", None, "Asset map", "Sentence, asset")
    f.box(DX, 1174, DW, 56, "st", None, "Packages", "Status, dates, assets")
    f.arrow([(ax, 82), (ax, 1174)], _n(g("projects", "cohort"), "projects"), at=(ax + 9, 250))
    # combination
    f.box(AX, 1300, CX + CW - AX, 96, "rule", "O1", "Assemble commitments",
          "Kept sentences are joined to their asset and their project, then grouped: one commitment for each project, "
          "measure, type and asset. Only investment project financing is kept. The same wording within a project counts once.")
    f.box(DX, 1290, DW, 134, "mod", "O2", "Link packages",
          f"Each commitment is tested against its project’s packages: would this package deliver it? Linked at {f_link} or more.",
          "DECISION MODEL")
    f.arrow([(ax, 1230), (ax, 1300)], _n(g("projects", "in_scope"), "projects in scope"))
    f.arrow([(bx, 1230), (bx, 1300)], kept)
    f.arrow([(cx, 1230), (cx, 1300)], with_asset, "l")
    f.arrow([(dx, 1230), (dx, 1290)], packages, "l")
    f.arrow([(CX + CW, 1348), (DX - 1, 1348)])
    f.box(AX, 1456, DX + DW - AX, 56, "out", "O3", "Dashboard",
          "Overview and Explore read the commitments with their sentences, source pages and linked packages. "
          "Rebuilt at each data load.")
    mid = AX + (CX + CW - AX) / 2
    c, cp = _n(g("measures", "commitments"), "commitments"), _n(g("measures", "commitment_projects"), "projects")
    f.arrow([(mid, 1396), (mid, 1456)], f"{c} in {cp}" if c and cp else c)
    lp, lc = _n(g("procurement", "linked_packages"), "packages"), _n(g("procurement", "linked_commitments"), "commitments")
    f.arrow([(dx, 1424), (dx, 1456)], f"{lp} linked to {lc}" if lp and lc else lp, "l")
    return f.svg("Pipeline. Project documents are read into sentences and embedded. Sentences are shortlisted, graded, "
                 "extended by feedback and thresholded in parallel for measures and digital assets; measures then pass "
                 "an overlap check and receive types. Procurement records are cleaned, embedded and assigned assets. "
                 "Projects, measure findings, the asset map and packages are stored, assembled into commitments, linked "
                 "to packages and shown in the dashboard.")


def _scope(n: dict) -> str:
    p = n.get("projects") or {}
    cohort = p.get("cohort")
    if not cohort:
        return ""
    with_doc, in_scope = p.get("with_document") or 0, p.get("in_scope") or 0
    not_approved, other = p.get("not_approved") or 0, p.get("other_instrument") or 0
    rest = cohort - with_doc - not_approved - other
    with_c = (n.get("measures") or {}).get("commitment_projects")
    rows = [(cohort, "Projects in the cohort", "Digital projects and projects with a digital component, selected manually."),
            (with_doc, "With a document read",
             f"Excluded: {not_approved} not yet approved, {other} policy loans and results-based programmes without one, "
             f"{rest} with no document found."),
            (in_scope, "Investment project financing", f"Excluded: {p.get('other_with_document') or 0} other operations with a document.")]
    if with_c is not None:
        rows.append((with_c, "With at least one commitment", ""))
    return '<div class="cover">' + "".join(
        f'<div class="row"><div class="num">{int(v):,}</div><div class="cell"><div class="b" style="width:{100 * v / cohort:.1f}%"></div>'
        f'<div class="lab">{html.escape(lab)}<small>{html.escape(note)}</small></div></div></div>' for v, lab, note in rows) + "</div>"


def page(n: dict) -> str:
    """The whole About view as HTML."""
    fl = n.get("floors") or {}
    floor, cyber = _p(fl.get("floor.default"), 0.8), _p(fl.get("floor.cyber_security"), 0.9)
    lab, p = n.get("labels") or {}, n.get("projects") or {}
    measures, assets = lab.get("measures") or 14, lab.get("assets") or 13
    types = (lab.get("types_defined") or 0) + (lab.get("types_proposed") or 0)
    as_of = (n.get("as_of") or {}).get("loaded")
    graded = (n.get("grades") or {}).get("graded_sentences")
    scope_n = p.get("in_scope")
    return f"""<style>{CSS}</style>
<div class="wbg-about">
<h2>Method</h2>
<p class="lede">This app identifies the climate resilience measures that World Bank investment projects commit to in their
disclosed documents, the digital assets those projects finance, and the procurement through which the commitments are
carried out. This page sets out the definitions, the scope, the pipeline, the models and the limitations.</p>
{f'<p class="asof">Data as of {as_of:%d %B %Y}</p>' if as_of is not None else ''}

<section><h3>Definitions</h3>
<dl class="words">
<div><dt>Commitment</dt><dd>A statement in a project document that the project will or may finance, deliver or require a
resilience measure. The unit of count is one project, measure, type and digital asset, supported by at least one sentence.</dd></div>
<div><dt>Measure</dt><dd>One of {measures} defined categories of climate resilience action, for example backup power, early
warning, or climate-informed siting.</dd></div>
<div><dt>Type</dt><dd>A subcategory of a measure, for example cell broadcast within early warning.{f' {types} types;' if types else ''}
a sentence may hold more than one.</dd></div>
<div><dt>Digital asset</dt><dd>One of {assets} defined categories of digital infrastructure or system a project finances, from
fibre networks to data infrastructure. A commitment whose sentence names none is shown as "No asset named".</dd></div>
<div><dt>Package</dt><dd>One line of a project's procurement plan, with its method, estimate, dates and status.</dd></div>
<div><dt>Probability</dt><dd>For a sentence and a definition, the probability the decision model gives to grades 2 and 3
together: P(grade 2) + P(grade 3). The strength marker beside a sentence shows how far above the threshold it is.</dd></div>
<div><dt>Stage</dt><dd>Where a commitment's linked procurement stands. Coming up: a package is planned, out to tender, or
past its planned date (overdue). Under way: a contract is signed or being carried out. Completed: a contract is complete.
Package dropped: a linked package was cancelled or left the plan; the commitment itself may stand. No package linked: none
was matched.</dd></div>
<div><dt>Regional project</dt><dd>A project covering several countries. It is counted under its region and is not in
country counts or on the map.</dd></div>
</dl></section>

<section><h3>Scope</h3>
<p class="sub">The cohort was selected manually: digital projects and projects with a digital component. The app reports
on those that are investment project financing and have a disclosed appraisal document or project paper.</p>
{_scope(n)}</section>

<section><h3>Pipeline</h3>
<p class="sub">Steps are numbered in three groups: P for preparation, C for classification, O for combination and output.
Each arrow shows what is passed on. Project documents are read into sentences and embedded once (P1, P2). The same
sentences are then classified twice in parallel, against the measure definitions and against the digital asset
definitions (C1 to C4); measures then pass C5 and C6. Procurement records are prepared separately (P3, P4, C8). The
results are held in four stores and combined (O1 to O3).</p>
<figure><div class="scroll">{figure(n)}</div>
<ul class="key"><li><i></i>Rule (fixed code)</li><li><i class="mod"></i>Model step, labelled with the model used</li>
<li><i class="man"></i>Specified manually</li><li><i class="st"></i>Store</li>
<li><span class="ar"></span>Data passed on, with its count</li><li><span class="ar d"></span>Input to a step</li></ul>
<figcaption>Counts are for the{f' {int(scope_n):,}' if scope_n else ''} projects in scope, as of the date above. Every sentence
count is a number of distinct sentences. A sentence can be kept for more than one measure, and C6 does not remove
sentences. Every answer of the decision model is stored with the model version, the exact text and the exact question,
and is reused on later runs.</figcaption></figure></section>

<section><h3>Models</h3>
<p class="sub">Three models are used, each for one task. Versions are fixed, so a later run uses the same model.</p>
<div class="models">
<div class="model"><div class="role">Similarity</div><h4>Embedding model</h4><code>{MODELS['embedding']}</code>
<p>Represents each sentence, search phrase and package description as a vector of 3,072 dimensions. Used in P2, P4, C1
and C3: to shortlist sentences by cosine similarity to a definition's search phrases, and to find more sentences like
those already graded 2 or 3. It takes no decision.</p></div>
<div class="model"><div class="role">Classification</div><h4>Decision model</h4><code>{MODELS['decision']}</code>
<p>Reads one item and one question and returns a probability for each permitted answer. Used in C2, C5, C6, C8 and O2:
wherever the pipeline grades or tests.</p></div>
<div class="model"><div class="role">Type proposal</div><h4>Generative model</h4><code>{MODELS['generative']}</code>
<p>Used in C7: for kept sentences that fit none of a measure's defined types, it proposes further types. A proposed type
is used only once accepted manually. It classifies nothing.</p></div>
</div>
<div class="scale"><div class="strip">
<div class="g"><b>0</b>Not described</div>
<div class="g"><b>1</b>Background, existing provision or another party's work</div>
<div class="g y"><b>2</b>The project may finance, deliver or require it</div>
<div class="g y"><b>3</b>The project explicitly finances, delivers or requires it</div></div>
<div class="brace"><div></div><div></div><div>Probability of commitment = P(2) + P(3). A sentence is kept at {floor} or
more; {cyber} for cybersecurity.</div></div></div></section>

<section><h3>Limitations and next steps</h3>
<p class="sub">Read the figures in this app with these in mind.</p>
<ol class="limits">
<li><h4>The method is tuned, not trained</h4><p>Definitions, search phrases and thresholds were adjusted against
{f'{int(graded):,}' if graded else 'a sample of'} graded sentences. No model was trained, and no held-out sample has been
graded, so the precision shown per measure is measured on the data used for tuning and may be optimistic. Against that,
the graded sentences were drawn mostly near the threshold, where classification is hardest.</p>
<p class="next"><b>Next:</b> grade a random evaluation sample.</p></li>
<li><h4>Asset attribution is conservative</h4><p>A commitment carries a digital asset only when its own sentence names
one, and a sentence keeps one asset. Inheritance from the surrounding paragraph is switched off. About half of
commitments therefore carry no asset.</p><p class="next"><b>Next:</b> improve asset recall without loosening precision.</p></li>
<li><h4>The probability layer is not applied</h4><p>Decisions use the decision model's probability directly against a
fixed threshold. A layer that adjusts it using graded neighbouring sentences has been fitted but did not outperform the
direct probability in testing, so it is switched off.</p><p class="next"><b>Next:</b> rebuild and validate the layer.</p></li>
<li><h4>A re-asked sentence can change grade</h4><p>The decision model does not return the identical answer every time:
in a repeat test on 160 sentences, 5% of grades changed. Stored answers are reused, so published figures are stable, but
a full re-run would move a small share of decisions.</p></li>
<li><h4>Package links are low confidence</h4><p>The link between a commitment and a package ranked only modestly above
chance on the graded sample, and most commitments have no linked package. Treat a link as a lead.</p>
<p class="next"><b>Next:</b> revise the link question and grade a larger sample.</p></li>
<li><h4>Types are precise but incomplete</h4><p>An assigned type is correct about 85% of the time, but about 4 in 10 of
the types a grader would assign are found. Many commitments show no type.</p></li>
<li><h4>No check yet on sentences under many measures</h4><p>A small number of sentences are kept under three or more
measures. Most are summary statements. They are counted under each measure.</p>
<p class="next"><b>Next:</b> grade these and set a rule.</p></li>
<li><h4>Documents record intent</h4><p>A commitment is what a document states the project will or may do. Neither a
commitment nor a completed contract is evidence of delivery. French, Spanish and Portuguese text is classified against
English definitions; accuracy there is unmeasured.</p></li>
</ol></section>
</div>"""
