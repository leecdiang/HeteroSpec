#!/usr/bin/env python3
"""Regenerate the JPDC manuscript's figures from pinned public data.

CPU only. The script reads the immutable input files under data/, checks their
SHA-256 identities, recomputes every plotted point estimate, and preserves the
published interval level and statistical unit. It does not load model weights,
contact a service, benchmark an accelerator, or change any input file.

Dependencies: Python 3.10+, numpy, pandas, matplotlib, Pillow; Inkscape is used
for vector PDF export when available. No rasterized data panels are used.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.collections import PathCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, FancyArrowPatch
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "figures"
GEN = ROOT / "generated"
OUT.mkdir(exist_ok=True)
GEN.mkdir(exist_ok=True)

INK = "#27353D"
BLUE = "#3F6C9B"
OCHRE = "#9D5F2D"
GRAY = "#6F767A"
PALE = "#D9DDE0"
LIGHT = "#F2F4F5"
BLUE_LIGHT = "#E6EEF6"
OCHRE_LIGHT = "#F5E8DC"
WHITE = "#FFFFFF"
HAS_INKSCAPE = shutil.which("inkscape") is not None
FAMILIES = {f.name for f in font_manager.fontManager.ttflist}
# P052 is Palatino-compatible. Its CFF outlines are exported via Inkscape,
# avoiding the OpenType/TrueType mismatch of direct Matplotlib PDF embedding.
FONT = "P052" if "P052" in FAMILIES and HAS_INKSCAPE else "DejaVu Serif"

STYLE = {
    "font.family": FONT, "font.size": 8.6,
    "axes.labelsize": 8.8, "axes.titlesize": 9.4,
    "xtick.labelsize": 8.2, "ytick.labelsize": 8.2,
    "legend.fontsize": 8.1, "text.color": INK,
    "axes.labelcolor": INK, "axes.edgecolor": GRAY,
    "xtick.color": INK, "ytick.color": INK,
    "axes.linewidth": .65, "lines.linewidth": 1.05,
    "xtick.major.width": .65, "ytick.major.width": .65,
    "xtick.major.size": 3, "ytick.major.size": 3,
    "savefig.facecolor": WHITE, "figure.facecolor": WHITE,
    "svg.fonttype": "none", "pdf.fonttype": 42, "ps.fonttype": 42,
    "mathtext.fontset": "dejavuserif", "hatch.linewidth": .55,
    "axes.unicode_minus": True,
}

METRICS: dict = {}
FIGURES: dict = {}
LAYOUT: dict = {}
CAPTIONS: dict[str, str] = {}
CHECKS: list[dict] = []
SOURCE_BY_LOCAL: dict = {}


def read_json(path):
    return json.loads((DATA / path).read_text())


def frame(path):
    return pd.read_csv(DATA / path)


def check_close(name, actual, expected, atol=2e-12):
    actual, expected = np.asarray(actual, dtype=float), np.asarray(expected, dtype=float)
    if actual.shape != expected.shape or not np.allclose(actual, expected, rtol=2e-12, atol=atol):
        raise AssertionError(f"{name}: recomputation differs from the published value")
    CHECKS.append({"name": name, "max_abs_error": float(np.max(np.abs(actual-expected))), "pass": True})


def verify_sources():
    manifest = json.loads((GEN / "figure_source_downloads.json").read_text())
    sources = manifest if isinstance(manifest, list) else manifest.get("sources", manifest.get("files", []))
    extra = GEN / "figure_sources_v2.json"
    if extra.exists():
        sources = sources + json.loads(extra.read_text())
    for item in sources:
        SOURCE_BY_LOCAL[item["local"]] = item
        p = ROOT / item["local"]
        if not p.exists():
            p = ROOT.parent / item["local"]
        actual = hashlib.sha256(p.read_bytes()).hexdigest()
        if actual != item["sha256"]:
            raise AssertionError(f"Source identity changed: {item['local']}")
    CHECKS.append({"name": "immutable source SHA-256 identities", "files": len(sources), "pass": True})


def clean(ax, grid="x"):
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_axisbelow(True)
    if grid:
        ax.grid(axis=grid, color=PALE, lw=.5, zorder=0)
    ax.tick_params(pad=3)
    return ax


def ptitle(ax, letter, text):
    ax.set_title(f"({letter})  {text}", loc="left", fontweight="bold", pad=9)


def refline(ax, direction="x"):
    if direction == "x":
        ax.axvline(1, color=INK, lw=.8, ls=(0, (3, 2)), zorder=1)
    else:
        ax.axhline(1, color=INK, lw=.8, ls=(0, (3, 2)), zorder=1)


def forest(ax, x, y, ci=None, color=BLUE, marker="D", filled=True, ms=4.7):
    if ci is not None:
        ax.plot(ci, [y, y], color=color, lw=1.6, zorder=4, solid_capstyle="butt")
        ax.plot(ci, [y, y], linestyle="none", marker="|", color=color, ms=5, mew=.9, zorder=4)
    ax.plot(x, y, marker=marker, color=color, mfc=color if filled else WHITE,
            ms=ms, mew=.95, linestyle="none", zorder=5)


def strip(ax, xs, y, color=GRAY, marker="o", spread=.14, s=14):
    """Deterministic alternating offsets: each dot remains one source root."""
    xs = np.asarray(xs)
    order = np.argsort(xs, kind="stable")
    offsets = np.resize(np.array([0, -.55, .55, -1, 1]), len(xs)) * spread
    yy = np.empty(len(xs))
    yy[order] = y + offsets
    ax.scatter(xs, yy, s=s, marker=marker, c=color, alpha=.55, linewidths=0, zorder=2)


def box(ax, x, y, w, h, text="", fill=LIGHT, edge=GRAY, hatch=None,
        fs=8.6, weight="normal", align="center", lw=.75):
    patch = Rectangle((x,y), w,h, facecolor=fill, edgecolor=edge, lw=lw, hatch=hatch)
    ax.add_patch(patch)
    if text:
        ax.text(x+w/2 if align=="center" else x+.06, y+h/2, text,
                ha=align, va="center", fontsize=fs, fontweight=weight, linespacing=1.15)
    return patch


def arrow(ax, xy, xy2, color=GRAY, lw=1.0, style="-|>", mutation=8):
    ax.add_patch(FancyArrowPatch(xy, xy2, arrowstyle=style, mutation_scale=mutation,
                               lw=lw, color=color, shrinkA=0, shrinkB=0))


def save(fig, stem, sources, width, height, markers=None):
    fig.set_size_inches(width, height, forward=True)
    # The CAS manuscript scales 7 in to 6.84 in; the supplement scales to
    # approximately 6.53 in. Keep the final embedded figure text at >= 8 pt.
    minimum_font = 8.6 if stem.startswith("supp") or stem == "fig05_application" else 8.2
    for t in fig.findobj(matplotlib.text.Text):
        if t.get_fontsize() < minimum_font:
            t.set_fontsize(minimum_font)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bounds = fig.bbox
    bad = []
    # Matplotlib creates labels for locator ticks outside the view limits; those
    # labels are not rendered. Exclude them from the physical-page bound check.
    suppressed_ticks = set()
    for ax in fig.axes:
        # No root or paired-observation dot may disappear beyond the view.
        for collection in ax.collections:
            if isinstance(collection, PathCollection):
                points = np.asarray(collection.get_offsets())
                if points.size:
                    xl, xh = sorted(ax.get_xlim()); yl, yh = sorted(ax.get_ylim())
                    if np.any(points[:,0] < xl) or np.any(points[:,0] > xh) or np.any(points[:,1] < yl) or np.any(points[:,1] > yh):
                        raise AssertionError(f"Data points outside displayed range: {stem}")
        for axis, limits in [(ax.xaxis, ax.get_xlim()), (ax.yaxis, ax.get_ylim())]:
            lo, hi = sorted(limits)
            for tick in axis.get_major_ticks() + axis.get_minor_ticks():
                if not lo-1e-10 <= tick.get_loc() <= hi+1e-10:
                    suppressed_ticks.update([tick.label1,tick.label2])
    for t in fig.findobj(matplotlib.text.Text):
        if t in suppressed_ticks or not t.get_visible() or not t.get_text().strip():
            continue
        b = t.get_window_extent(renderer)
        if b.x0 < -.8 or b.y0 < -.8 or b.x1 > bounds.x1+.8 or b.y1 > bounds.y1+.8:
            bad.append({"text": t.get_text(), "bbox_px": list(b.bounds)})
    LAYOUT[stem] = {"page_inches": [width,height], "font_family": FONT,
                    "minimum_source_text_pt": minimum_font,
                    "out_of_page_text": bad}
    if bad:
        raise AssertionError(f"Out-of-page text in {stem}: {bad}")
    svg = OUT / (stem+".svg")
    pdf = OUT / (stem+".pdf")
    fig.savefig(svg, dpi=300)
    fig.savefig(OUT / (stem+".png"), dpi=220)
    if HAS_INKSCAPE:
        r = subprocess.run(["inkscape", str(svg), "--export-type=pdf",
                            "--export-area-page", "--export-filename="+str(pdf)],
                           capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(r.stderr)
        exporter = "Matplotlib SVG -> Inkscape PDF; editable SVG text"
    else:
        fig.savefig(pdf)
        exporter = "Matplotlib PDF (TrueType font)"
    plt.close(fig)
    FIGURES[stem] = {"size_inches": [width,height], "source_files": sources,
                     "source_paths_relative_to": "paper/data",
                     "pinned_sources": [SOURCE_BY_LOCAL["data/"+s] for s in sources],
                     "generation_script": "paper/scripts/build_figures.py",
                     "exporter": exporter, "plotted_observations": markers,
                     "outputs": {ext: {"path": f"figures/{stem}.{ext}",
                         "sha256": hashlib.sha256((OUT/(stem+'.'+ext)).read_bytes()).hexdigest()}
                         for ext in ["pdf","svg","png"]}}


def data_table(pr):
    plan = read_json(f"closeout/{pr}/PLAN.json")
    d = frame(f"closeout/{pr}/TIMING_ROWS.csv")
    assert len(d) == len(plan["roots"]) * len(plan["arms"]) * 4
    assert not d.duplicated(["root", "session", "arm"]).any()
    sums = d.groupby(["root","arm"], sort=False).service_s.sum().unstack("arm").loc[plan["roots"]]
    result = read_json(f"closeout/{pr}/ORIGINAL_RESULTS.json")
    totals = result.get("totals", result.get("totals_s"))
    for arm in plan["arms"]:
        check_close(pr+" total "+arm, sums[arm].sum(), totals[arm])
    return plan, sums, result


def contrasts(result):
    return result.get("all_fixed_controls", result.get("contrasts"))


def pick_contrast(result, num, den):
    return next(c for c in contrasts(result) if c["numerator"] == num and c["denominator"] == den)


def interval(c):
    return c.get("interval", c.get("adjusted_interval"))


def overview():
    """One four-query example; the wider-prefill inset is explicitly separate."""
    fig = plt.figure(figsize=(7,5.2))
    ax = fig.add_axes([0,0,1,1]); ax.set_xlim(0,7); ax.set_ylim(-.2,5); ax.axis("off")
    ax.text(.12,4.81,"(a)  Four known queries; a wider call changes three physical ranges",fontsize=9.4,fontweight="bold")
    x0,cw=2.00,1.10
    ax.text(.12,4.46,"Known target inputs",fontsize=8.7,va="center")
    for i,label in enumerate(["seed s · 765","draft d1 · 766","draft d2 · 767","draft d3 · 768"]):
        ax.text(x0+cw*(i+.5),4.46,label,ha="center",va="center",fontsize=8.5)
    for y,label,exts in [(4.05,"Reference KV extent",[768,768,768,1024]),(3.65,"Direct wide extent",[1024]*4)]:
        ax.text(.12,y+.15,label,fontsize=8.7,va="center")
        for i,e in enumerate(exts):
            box(ax,x0+i*cw,y,cw-.035,.30,str(e),BLUE_LIGHT if e==768 else OCHRE_LIGHT,
                BLUE if e==768 else OCHRE,hatch=None if e==768 else "///",fs=8.6)
    ax.plot([x0,x0+cw*3-.035],[3.57,3.57],color=OCHRE,lw=1.2)
    ax.text(x0+cw*1.5,3.43,"Same causal visibility, different physical attention problem",ha="center",fontsize=8.4,color=OCHRE)

    ax.plot([.12,6.88],[3.30,3.30],color=PALE,lw=.7)
    ax.text(.12,3.12,"(b)  Preserve the numerical paths; change where the cut is paid",fontsize=9.4,fontweight="bold")
    left,right,width=.12,3.70,3.18
    for x,title in [(left,"SIMPLE · whole-call cut"),(right,"LOCAL · attention-only cut")]:
        ax.text(x+width/2,2.88,title,ha="center",fontweight="bold",fontsize=8.9)
    # Execution ribbons share the four-query column scale. SIMPLE's whole-call
    # frames split every decoder layer; LOCAL's frame spans all four rows.
    box(ax,left,1.82,width*.75-.035,.92,"",fill="none",edge=GRAY,lw=.9)
    box(ax,left+width*.75+.015,1.82,width*.25-.015,.92,"",fill="none",edge=GRAY,lw=.9)
    box(ax,right,1.82,width,.92,"",fill="none",edge=INK,lw=1.0)
    for x,n,w in [(left+.035,3,width*.75-.105),(left+width*.75+.05,1,width*.25-.085)]:
        label="Projection: 3-column tail" if n==3 else "1 col."
        box(ax,x,2.45,w,.23,label,LIGHT,PALE,fs=8.3,lw=.5)
        box(ax,x,2.15,w,.23,"Attention · 768" if n==3 else "1024",BLUE_LIGHT if n==3 else OCHRE_LIGHT,
            BLUE if n==3 else OCHRE,hatch=None if n==3 else "///",fs=8.3,lw=.6)
        box(ax,x,1.88,w,.20,"Output proj. / FFN: 3 rows" if n==3 else "1 row",LIGHT,PALE,fs=8.2,lw=.5)
    box(ax,right+.035,2.45,width-.07,.23,"Projection: one four-column group (a = 4)",LIGHT,INK,fs=8.35,lw=.65)
    box(ax,right+.035,2.15,width*.75-.055,.23,"Attention: first 3 rows · 768",BLUE_LIGHT,BLUE,fs=8.3,lw=.6)
    box(ax,right+width*.75+.015,2.15,width*.25-.05,.23,"last · 1024",OCHRE_LIGHT,OCHRE,hatch="///",fs=8.3,lw=.6)
    box(ax,right+.035,1.88,width-.07,.20,"Output proj. / FFN: all four rows",LIGHT,INK,fs=8.3,lw=.65)

    ax.text(.12,1.62,"(c)  Own every requested output; commit the accepted prefix",fontsize=9.4,fontweight="bold")
    for i in range(4):
        box(ax,.12+i*.47,1.06,.43,.27,f"z{i}",WHITE,INK,fs=8.6)
    ax.text(.12,1.43,"Outputs in row order",fontsize=8.3)
    arrow(ax,(2.03,1.195),(2.34,1.195),INK)
    ax.text(2.53,1.29,"z2 selects c",ha="center",fontsize=8.2)
    ax.text(2.53,1.07,"d1, d2 accepted",ha="center",fontsize=8.2)
    ax.text(3.25,1.43,"Keep KV through 767",fontsize=8.3)
    for i,t in enumerate(["…","s","d1","d2"]):
        box(ax,3.25+i*.46,1.06,.43,.27,t,BLUE_LIGHT,BLUE,fs=8.6)
    box(ax,5.18,1.06,.43,.27,"d3",LIGHT,GRAY,fs=8.6)
    ax.plot([5.19,5.60],[1.065,1.325],color=GRAY,lw=.8)
    ax.text(5.395,.91,"trim",ha="center",fontsize=8.2)
    box(ax,6.08,1.06,.76,.27,"c at 768",WHITE,INK,fs=8.4)
    ax.patches[-1].set_linestyle((0,(3,2)))
    ax.text(6.46,1.43,"Pending token",ha="center",fontsize=8.3)
    ax.text(6.46,.91,"not yet in KV",ha="center",fontsize=8.2)

    ax.plot([.12,6.88],[.79,.79],color=PALE,lw=.7)
    ax.text(.12,.62,"(d)  Cross-group packing: 8 known prefill rows; last output requested",fontsize=9.1,fontweight="bold")
    ix,iw=3.00,.48
    ax.text(.12,.41,"Positions / physical runs 7 + 1",fontsize=8.25,va="center")
    for i,p in enumerate(range(761,769)):
        box(ax,ix+i*iw,.30,iw-.015,.20,str(p),BLUE_LIGHT if i<7 else OCHRE_LIGHT,
            BLUE if i<7 else OCHRE,hatch=None if i<7 else "///",fs=8.3,lw=.45)
    ax.text(.12,.205,"Attention tiles: 4 + 3 + 1",fontsize=8.25,va="center")
    # The upper solid braces encode attention tiles, the lower dark braces
    # arithmetic 4+4. Their separate vertical placement prevents conflation.
    for off,n in [(0,4),(4,3),(7,1)]:
        xx=ix+off*iw;ww=n*iw-.015
        ax.plot([xx,xx,xx+ww,xx+ww],[.255,.205,.205,.255],color=BLUE if off<7 else OCHRE,lw=1.0)
    for off in [0,4]:
        xx=ix+off*iw;ww=4*iw-.015
        ax.plot([xx,xx,xx+ww,xx+ww],[.065,-.005,-.005,.065],color=INK,lw=1.0)
        ax.text(xx+ww/2,-.15,"a = 4",ha="center",va="bottom",fontsize=8.2)
    ax.text(.12,-.005,"Arithmetic groups: 4 + 4",fontsize=8.25,va="center")
    save(fig,"fig01_overview",["pr222/rewrite_figure_sources.json"],7,5.2,
         {"main_example_known_queries":4,"main_arithmetic_groups":1,"prefill_inset_known_rows":8,
          "prefill_inset_physical_runs":[7,1],"prefill_inset_attention_tiles":[4,3,1],"prefill_inset_arithmetic_groups":[4,4]})
    CAPTIONS["fig01_overview"] = (
        "Preserve each group's numerical path while changing the organization between groups. "
        "(a) The four known verification inputs at positions 765--768 require physical "
        "KV extents 768, 768, 768 and 1024. Draft proposals are known inputs to verification, "
        "not assumed future target tokens. (b) SIMPLE cuts whole calls 3+1; LOCAL retains "
        "one four-column projection group and cuts attention 3+1. Each used 1--4-column "
        "path must satisfy the backend's numerical contract. (c) All four requested vectors "
        "are owned in row order. In the illustrated acceptance outcome d1 and d2 are accepted, "
        "d3 is rejected, and z2 supplies correction c. KV is retained through position 767; "
        "c at 768 is pending until materialized. (d) A separate eight-row known-prefill "
        "example requests only its last output. Physical runs 7+1 give attention tiles "
        "4+3+1, while projection groups are 4+4. This is not the four-row k=3 verifier. "
        "The conceptual diagram was prepared with AI-assisted drawing code.")


def extent():
    fig = plt.figure(figsize=(7,2.15))
    ax = fig.add_axes([0,0,1,1]);ax.set_xlim(0,7);ax.set_ylim(0,2.15);ax.axis("off")
    ax.text(.1,1.98,"(a)  Exchange the physical range",fontsize=9.4,fontweight="bold")
    ax.text(3.75,1.98,"(b)  The full AV result follows the range",fontsize=9.4,fontweight="bold")
    ax.text(.1,1.72,"Native AV replay; q = 1 on both sides",fontsize=8.5)
    box(ax,.1,1.14,1.08,.35,"Scalar capture",BLUE_LIGHT,BLUE)
    box(ax,.1,.52,1.08,.35,"Wide capture",OCHRE_LIGHT,OCHRE,hatch="///")
    arrow(ax,(1.18,1.315),(1.55,1.315),BLUE)
    arrow(ax,(1.18,.695),(1.55,.695),OCHRE)
    ax.text(1.66,1.33,"Zero-pad P; use 1024-entry V",fontsize=8.5,va="center")
    ax.text(1.66,.71,"Crop P and V to 768 entries",fontsize=8.5,va="center")
    ax.text(.1,.17,"Visible probabilities remain unchanged; physical extent is exchanged.",fontsize=8.3)
    x,y,w,h=4.83,.49,.94,.47
    ax.text(4.83,1.72,"Replayed physical KV range",fontsize=8.5)
    for j,col in enumerate(["768","1024"]):ax.text(x+(j+.5)*w,1.45,col,ha="center",fontsize=8.7)
    ax.text(3.78,1.195,"Scalar capture",fontsize=8.4,va="center")
    ax.text(3.78,.725,"Wide capture",fontsize=8.4,va="center")
    for row in range(2):
        for col in range(2):
            box(ax,x+col*w,y+(1-row)*h,w,h,
                "Reference\nvector" if col==0 else "Wide-path\nvector",
                BLUE_LIGHT if col==0 else OCHRE_LIGHT,
                BLUE if col==0 else OCHRE,hatch=None if col==0 else "///",fs=8.5)
    ax.text(3.78,.17,"Exact AV output; state is a separate obligation.",fontsize=8.3)
    save(fig,"fig02_extent",["pr222/rewrite_figure_sources.json"],7,2.15,{"replay_conditions":4})
    CAPTIONS["fig02_extent"] = (
        "A two-way intervention isolates the effect of physical KV extent on the native "
        "attention-value (AV) result. Both captured AV operators have one query. Starting "
        "from the scalar capture, zero-padding the probability vector and supplying the "
        "corresponding 1024-entry V range reproduces the wide-path AV vector. Starting "
        "from the wide capture, cropping probabilities and V to 768 entries reproduces "
        "the scalar-reference AV vector. Each unmodified replay also matches its own "
        "captured path. These are full AV-output comparisons on the captured case; "
        "they do not constitute an intervention on complete downstream KV state.")


def strong_baseline():
    rows=frame("closeout/service/S3_TIMINGS.csv")
    measured=rows[rows.role=="measured"].copy()
    assert len(measured)==144
    pivot=measured.pivot(index=["slot","root","domain","round"],columns="arm",values="service_s").sort_index()
    pr=frame("pr218/PER_ROOT.csv").sort_values("slot")
    rr=np.exp(np.log(pivot.C/pivot.B).groupby(level="slot").mean()).sort_index()
    check_close("S3 per-root C/B",rr,pr.CB)
    result=read_json("closeout/service/ORIGINAL_RESULTS.json")["S3"]
    for c in result["contrasts"]:
        ratios=np.exp(np.log(pivot[c["candidate"]]/pivot[c["baseline"]]).groupby(level="slot").mean())
        check_close("S3 "+c["candidate"]+"/"+c["baseline"],np.exp(np.log(ratios).mean()),c["ratio"])
    audit=read_json("v2/s3_cost_audit.json")["groups"]
    phase={arm:audit[arm]["measured"] for arm in ["B","C"]}
    for arm in ["B","C"]:
        check_close("S3 phase-accounting service "+arm,phase[arm]["service_s"],measured.loc[measured.arm==arm,"service_s"].sum())
    keys=["prefill_s","decode_s","other_s","service_s"]
    for arm in ["B","C"]:
        phase[arm]["other_s"]=phase[arm]["service_s"]-phase[arm]["prefill_s"]-phase[arm]["decode_s"]
    delta={k:phase["C"][k]-phase["B"][k] for k in keys}
    check_close("S3 phase-change balance",delta['prefill_s']+delta['decode_s']+delta['other_s'],delta['service_s'],atol=1e-10)
    fig=plt.figure(figsize=(7,4.40))
    left=fig.add_axes([.115,.435,.36,.455]);right=fig.add_axes([.64,.58,.34,.31])
    clean(left);clean(right);refline(left);refline(right)
    ptitle(left,"a","Twelve roots, four paired rounds each")
    ptitle(right,"b","Beyond shared quantization")
    for slot in range(12):
        q=pivot.loc[slot];dots=(q.C/q.B).values;y=11-slot
        color=BLUE if slot<6 else OCHRE;marker="o" if slot<6 else "^"
        left.plot(dots,np.full(4,y),linestyle="none",marker=marker,ms=3.2,
                  mfc=WHITE,mec=color,mew=.6,alpha=.65,zorder=2)
        left.plot(rr.loc[slot],y,marker=marker,color=color,ms=4.6,ls="none",zorder=4)
    left.set_yticks(range(12),[f"Math {6-i}" for i in range(6)]+[f"Code {12-i}" for i in range(6,12)])
    left.set_xlim(.972,1.003);left.set_ylim(-.65,11.65)
    left.xaxis.set_major_locator(MultipleLocator(.01));left.xaxis.set_major_formatter(FormatStrFormatter("%.2f"))
    left.set_xlabel("C/B resident-service-time ratio")
    left.axhline(5.5,color=PALE,lw=.65)
    for i,c in enumerate(result["contrasts"]):
        y=2-i;color=BLUE if i==0 else GRAY
        forest(right,c["ratio"],y,c["interval"],color=color,marker="D" if i==0 else "s")
        right.text(.927,y+.29,f"{c['candidate']}/{c['baseline']} · {100*c['confidence']:g}% CI",fontsize=8.2,color=color)
    right.set_yticks([]);right.set_ylim(-.5,2.6);right.set_xlim(.925,1.003)
    right.xaxis.set_major_locator(MultipleLocator(.02));right.xaxis.set_major_formatter(FormatStrFormatter("%.2f"))
    right.set_xlabel("Equal-root geometric time ratio")
    fig.text(.64,.455,"C/B: 1.51% less service time",fontsize=10,fontweight="bold",color=BLUE)
    fig.text(.64,.407,"95% CI: 1.23%–1.79%",fontsize=8.8)
    fig.text(.115,.315,"Open: paired rounds    Filled: root means    Ratios below 1 favor the numerator",fontsize=8.3)
    fig.text(.115,.264,"(c)  Prefill explains the summed change",fontsize=9.4,fontweight="bold")
    fig.text(.58,.264,"B → C totals; 48 requests per arm",fontsize=8.4)
    ax=fig.add_axes([.405,.11,.55,.145]);clean(ax)
    ax.axvline(0,color=GRAY,lw=.8)
    labels=[]
    for y,k,name in zip([3,2,1,0],keys,["Prefill","Decode","Other + residual","Service"]):
        val=delta[k];col=INK if k=='service_s' else BLUE if val<0 else OCHRE
        ax.plot([0,val],[y,y],color=col,lw=3.2 if k!='service_s' else 3.8,solid_capstyle='butt')
        ax.plot(val,y,marker='D' if k=='service_s' else 'o',ms=3.6,color=col,ls='none')
        ax.text(val+(-.13 if val<0 else .13),y,f"{val:+.3f}",ha='right' if val<0 else 'left',va='center',fontsize=8.2,color=col)
        labels.append(f"{name}: {phase['B'][k]:.3f} → {phase['C'][k]:.3f}")
    ax.set_yticks([3,2,1,0],labels);ax.tick_params(axis='y',length=0,pad=8)
    ax.set_xlim(-8.1,2.1);ax.set_ylim(-.6,3.6);ax.set_xticks([-8,-6,-4,-2,0,2])
    ax.set_xlabel("Change in summed time, C − B (s)",labelpad=3)
    save(fig,"fig03_strong_baseline",["closeout/service/S3_TIMINGS.csv","closeout/service/ORIGINAL_RESULTS.json","pr218/PER_ROOT.csv","v2/s3_cost_audit.json"],7,4.40,
         {"roots":12,"paired_rounds":48,"contrasts":3,"descriptive_phase_totals_per_arm":4})
    METRICS["strong_baseline"]={"contrasts":result["contrasts"],"root_ratios":rr.tolist(),"measured_rows":144,"warm_rows":144,
                               "phase_totals_s":phase,"phase_changes_C_minus_B_s":delta,
                               "phase_scope":"Descriptive sums of 48 measured requests per arm; no additional independent samples or phase confidence intervals."}
    CAPTIONS["fig03_strong_baseline"] = (
        "Independent scalar groups reduce 32B target-only service time beyond shared quantization. "
        "A5000, Qwen3-32B mixed Q4_K/Q6_K, a=1 and whole-graph cuts. B shares activation "
        "quantization and loops over scalar backend calls; C exposes those scalar groups "
        "as channels; G is the graph-level scalar control. (a) Open markers retain all "
        "48 paired rounds; filled markers are means of log ratios within the twelve roots. "
        "(b) C/B is the primary equal-root geometric estimate, with a 95% stratified "
        "paired-root interval; G comparisons have 97.5% intervals. (c) Phase accounting "
        "uses sums of the same 48 measured requests per arm. Prefill falls by 5.942 s, "
        "decode rises by 0.027 s, and other named costs plus unpartitioned residual rise "
        "by 0.009 s. These sums explain the measured localization without replacing the "
        "root-weighted estimate or creating new independent samples. The resident timer "
        "includes reset and requested-output ownership, and excludes loading and capture.")


def factorial():
    fig=plt.figure(figsize=(7,3.35))
    axes=[fig.add_axes([.205,.27,.29,.59]),fig.add_axes([.68,.27,.29,.59])]
    labels=["LOCAL / SIMPLE\nwith loop4","LOCAL / SIMPLE\nwith packing",
            "Packing / loop4\nwith SIMPLE","Packing / loop4\nwith LOCAL","Interaction"]
    metrics=[]
    for ax,pr,model,letter in zip(axes,["pr204","pr208"],["Qwen3-8B","Qwen3-14B"],["a","b"]):
        plan,sums,result=data_table(pr)
        clean(ax);refline(ax);ptitle(ax,letter,model+" · 16 roots")
        cs=contrasts(result)
        for i,c in enumerate(cs):
            n,d=c["numerator"],c["denominator"]
            xs=(sums[n]/sums[d]).values
            value=float(sums[n].sum()/sums[d].sum())
            check_close(pr+" ratio "+n+"/"+d,value,c["total_ratio"])
            check_close(pr+" roots "+n+"/"+d,xs,c["root_ratios"])
            y=4-i
            strip(ax,xs,y+.14,s=13,spread=.1)
            color=OCHRE if i<2 else BLUE
            ci=interval(c)
            forest(ax,value,y-.15,ci,color,"D",not(ci[0]<=1<=ci[1]))
            metrics.append({"model":model,"numerator":n,"denominator":d,"ratio":value,"ci99":ci,"root_ratios":xs.tolist()})
        inter=((sums.L_P_D4/sums.W_P_D4)/(sums.L_L4_D4/sums.W_L4_D4)).values
        iv=float(np.exp(np.log(inter).mean()))
        check_close(pr+" interaction",iv,result["interaction"]["ratio"])
        strip(ax,inter,.14,s=13,spread=.1)
        forest(ax,iv,-.15,result["interaction"]["interval"],GRAY,"s")
        ax.axhline(.5,color=PALE,lw=.65)
        ax.set_xlim(.974,1.010);ax.set_ylim(-.65,4.6)
        ax.set_yticks(range(5),labels[::-1]);ax.tick_params(axis="y",length=0,pad=6)
        ax.xaxis.set_major_locator(MultipleLocator(.01));ax.xaxis.set_major_formatter(FormatStrFormatter("%.2f"))
        ax.set_xlabel("Service-time ratio")
        metrics.append({"model":model,"contrast":"interaction","geomean":iv,"ci99":result["interaction"]["interval"],"root_ratios":inter.tolist()})
    fig.text(.205,.075,"Gray dots: roots    Diamonds/squares: estimate and 99% CI",fontsize=8.4)
    fig.text(.205,.03,"Hollow estimates have intervals crossing 1. Interactions use a geometric ratio of ratios.",fontsize=8.25)
    save(fig,"fig04_factorial",[f"closeout/{pr}/{f}" for pr in ["pr204","pr208"] for f in ["PLAN.json","TIMING_ROWS.csv","ORIGINAL_RESULTS.json"]],7,3.35,
         {"roots_per_panel":16,"root_observations":160,"direct_contrasts":8,"interactions":2})
    METRICS["factorial"]=metrics
    CAPTIONS["fig04_factorial"] = (
        "Balanced four-arm attribution separates local attention cuts from projection "
        "packing on A5000. Each model uses the same 16 exposed roots in four sessions, "
        "with draft prefill microbatch D4 and proposal count fixed. Gray dots are "
        "per-root ratios after summing the four sessions. Direct estimates are ratios "
        "of total service times; intervals are the original 99% root-bootstrap intervals "
        "for the five-comparison family. The interaction is the geometric mean of "
        "(LOCAL-packed/WHOLE-packed)/(LOCAL-loop4/WHOLE-loop4). Packing gives the "
        "larger service increment; the LOCAL increment with packing is uncertain in "
        "both models. Hollow summary markers identify intervals containing 1. The "
        "root set is shared between the two models and is not an independent sample "
        "of 32 tasks. Service timing covers the resident request.")


def application():
    fig=plt.figure(figsize=(7,2.8))
    axes=[fig.add_axes([.13,.32,.33,.50]),fig.add_axes([.63,.32,.34,.50])]
    models=[("pr203","Qwen3-8B",16),("pr206","Qwen3-14B",16),("pr205","Llama-8B",12)]
    entries=[]
    for a,ax in enumerate(axes):
        clean(ax);refline(ax);ptitle(ax,"ab"[a],["Same D4 setup","Complete application vs target-only"][a])
        for i,(pr,model,nroots) in enumerate(models):
            plan,sums,result=data_table(pr)
            den="W_L4_D4" if a==0 else min([s for s in sums.columns if s.endswith("_M")],key=lambda k:sums[k].sum())
            c=pick_contrast(result,"L_P_D4",den)
            rr=(sums.L_P_D4/sums[den]).values
            val=float(sums.L_P_D4.sum()/sums[den].sum())
            check_close(pr+" app "+den,val,c["total_ratio"])
            check_close(pr+" app roots "+den,rr,c.get("root_ratios",c.get("per_root")))
            y=2-i
            strip(ax,rr,y+.14,spread=.10,s=16)
            forest(ax,val,y-.17,interval(c),BLUE,"D")
            ax.text(.5,y-.43,f"{100*(1-val):.2f}% less time",transform=ax.get_yaxis_transform(),ha="center",fontsize=8.2,color=BLUE)
            entries.append({"panel":a,"model":model,"numerator":"L_P_D4","denominator":den,"ratio":val,"ci99":interval(c),"root_ratios":rr.tolist()})
        ax.set_yticks([0,1,2],["Llama-8B\n12 roots","Qwen3-14B\n16 roots","Qwen3-8B\n16 roots"])
        ax.tick_params(axis="y",length=0,pad=6);ax.set_ylim(-.6,2.5)
        ax.set_xlim((.96,1.006) if a==0 else (.53,1.07))
        ax.xaxis.set_major_locator(MultipleLocator(.02 if a==0 else .1));ax.xaxis.set_major_formatter(FormatStrFormatter("%.2f" if a==0 else "%.1f"))
        ax.set_xlabel("Service-time ratio (lower is faster)")
    fig.text(.13,.10,"Dots: individual roots     Diamonds: ratio of totals with original 99% interval",fontsize=8.3)
    fig.text(.13,.035,"Panels use different controls and scales. The complete-application result includes drafting.",fontsize=8.25)
    save(fig,"fig05_application",[f"closeout/{pr}/{f}" for pr,_,_ in models for f in ["PLAN.json","TIMING_ROWS.csv","ORIGINAL_RESULTS.json"]],7,2.8,
         {"root_observations":88,"contrasts":6})
    METRICS["application"]=entries
    CAPTIONS["fig05_application"] = (
        "Application benefit and the method increment answer different questions. "
        "(a) LOCAL-packed D4 versus WHOLE-loop4 D4 retains the same draft setup; "
        "this is a combined packing-and-cut comparison. (b) LOCAL-packed D4 versus "
        "the fastest measured fixed target-only M implementation includes the benefit "
        "of drafting. Qwen3-8B and Qwen3-14B use a Qwen3-0.6B draft and the same "
        "16 exposed transfer roots; Llama-8B uses a Llama-1B draft and 12 roots "
        "selected after the rule freeze. Every root is measured in four sessions. "
        "Dots sum sessions within roots; diamonds show ratios of total resident-service "
        "time and the original 99% intervals for five fixed comparisons. All fixed M "
        "controls remain in the supplied data. The 8B D4-arm order was fixed, so the "
        "balanced experiment in Fig. 4 provides component attribution. Separate "
        "scales prevent the same-D4 increment from being confused with the complete "
        "speculative application gain.")


def geometry():
    data=read_json("pr222/b570_inputs.json")
    fig=plt.figure(figsize=(7,4.00))
    axs=[fig.add_axes([.09,.49,.39,.34]),fig.add_axes([.58,.49,.39,.34])]
    stats=[]
    for ax,ctx,letter in zip(axs,[1024,4096],["a","b"]):
        clean(ax,"y");refline(ax,"y");ptitle(ax,letter,f"B570 · capacity {ctx}")
        for j,q in enumerate([2,4,32]):
            for cond,offset,color,marker in [("crossing",-.13,BLUE,"^"),("inside",.13,OCHRE,"o")]:
                key=f"C{ctx}-q{q}-{cond}";a=np.asarray(data["cells"][key]);rr=a[2]/a[1];r=a[2].sum()/a[1].sum()
                check_close("B570 "+key,r,data["reported_L_over_S"][key])
                xx=j+offset
                ax.plot([xx,xx],[rr.min(),rr.max()],color=color,lw=1.2,zorder=2)
                ax.scatter(xx+np.array([-.037,0,.037]),rr,s=15,marker=marker,
                           facecolors=color if cond=="crossing" else WHITE,edgecolors=color,lw=.7,zorder=3)
                ax.plot(xx,r,marker="_",ms=10,mew=1.8,color=INK,zorder=4)
                stats.append({"cell":key,"ratio_of_totals":float(r),"paired_ratios":rr.tolist(),"range":[float(rr.min()),float(rr.max())]})
        ax.set_xlim(-.45,2.45);ax.set_ylim(.50,1.13);ax.set_xticks(range(3),["q = 2","q = 4","q = 32"])
        ax.yaxis.set_major_locator(MultipleLocator(.2))
        ax.yaxis.set_major_formatter(FormatStrFormatter("%.1f"))
        if ax is axs[0]:ax.set_ylabel("LOCAL / SIMPLE append time")
    fig.text(.09,.935,"Controlled opportunity: a 1 + (q − 1) boundary split",fontsize=9.7,fontweight='bold')
    handles=[Line2D([],[],color=BLUE,marker="^",ls="none",ms=5,label="Crossing: 20.34–44.68% less time"),
             Line2D([],[],color=OCHRE,marker="o",mfc=WHITE,ls="none",ms=5,label="Inside: 0.43–3.74% more time")]
    fig.legend(handles=handles,loc="lower center",bbox_to_anchor=(.53,.365),ncol=2,frameon=False,columnspacing=1.3)
    fig.add_artist(Line2D([.09,.97],[.355,.355],transform=fig.transFigure,color=PALE,lw=.7))
    natural=read_json("pr222/rewrite_figure_sources.json")["natural_geometry"]
    density=fig.add_axes([.09,.045,.39,.255]);density.set_xlim(0,1);density.set_ylim(0,1);density.axis('off')
    density.text(0,1.00,"(c)  Separate A5000 verification census",fontsize=9.2,fontweight='bold',va='top')
    frac=natural['whole_extra_call_cycles']/natural['logical_cycles']
    density.text(0,.64,f"{natural['whole_extra_call_cycles']} / {natural['logical_cycles']:,} cycles",fontsize=15.2,fontweight='bold',color=BLUE)
    density.text(.97,.66,f"{100*frac:.3f}%",fontsize=11,ha='right',color=BLUE)
    box(density,0,.37,.97,.13,"",LIGHT,PALE,lw=.6)
    box(density,0,.37,.97*frac,.13,"",BLUE,BLUE,lw=.5)
    density.text(0,.22,"An extra whole-call split was possible.",fontsize=8.4)
    density.text(0,.03,"Qwen3-8B; k = 3; opportunity count, not time.",fontsize=8.25)
    source=read_json('v2/local_cost_REPORT.json')
    static={x['arm']:x for x in source['source_derived_proposed_append_work'] if x['rows']==89}
    assert set(static)=={'W','L'}
    info=fig.add_axes([.58,.045,.39,.255]);info.set_xlim(0,1);info.set_ylim(0,1);info.axis('off')
    info.text(0,1.00,"(d)  Source-derived 89-row append",fontsize=9.2,fontweight='bold',va='top')
    for x,t in [(.67,'SIMPLE'),(.94,'LOCAL')]:info.text(x,.72,t,ha='right',fontsize=8.3,fontweight='bold')
    rows=[('Decoder calls','calls',1),('Tiles / projection','projection_4column_groups_per_fully_consumed_projection',1),
          ('Logical mask size (KiB)','logical_F32_mask_bytes',1024),('Concat nodes / layer','attention_concat_nodes_per_layer',1)]
    for y,(label,k,scale) in zip([.56,.40,.24,.08],rows):
        info.text(0,y,label,fontsize=8.3)
        for arm,x in [('W',.67),('L',.94)]:info.text(x,y,f"{static[arm][k]/scale:g}",ha='right',fontsize=8.6,color=INK if arm=='W' else BLUE)
    save(fig,"fig06_geometry",["pr222/b570_inputs.json","pr222/b570_append.json","pr222/rewrite_figure_sources.json","v2/local_cost_REPORT.json"],7,4.00,
         {"fixed_cells":12,"paired_observations":36,"timing_rows":108,"separate_natural_cycle_count":2224,"source_derived_proposed_append_rows":89})
    METRICS["geometry"]={"controlled":stats,"natural":natural,"source_derived_89_rows":static}
    CAPTIONS["fig06_geometry"] = (
        "Opportunity frequency and saved work explain different local-cut outcomes. "
        "(a,b) B570 SmolLM2-1.7B prepared-state appends retain all twelve controlled cells "
        "and three paired observations per cell. Triangles cross a boundary with a "
        "1+(q−1) split; hollow circles remain inside one range. Segments are paired "
        "min–max ranges, and black ticks are ratios of summed times. The timer includes "
        "binding, decode, synchronization and output copying, excluding preparation. "
        "(c) A separate A5000 Qwen3-8B census has 20 extra-call opportunities among "
        "2,224 verification cycles. It supplies an opportunity frequency, not the B570 "
        "saving per event. (d) Source analysis of a proposed 89-row supplied-history "
        "append reduces four decoder calls to three but retains 23 ordered projection "
        "tiles per fully consumed projection. Logical masks grow and concat nodes "
        "increase. These are graph-construction quantities, not measured GPU traffic "
        "or time. No cross-platform service gain is formed by multiplying the panels.")


def work_cost():
    """Separate fixed-work efficiency, changed live work, and live service."""
    eq=read_json('pr222/q8_equal_work.json');live=read_json('pr222/q8_recomputed.json')
    work=read_json('pr222/q8_phase_work.json')['work_by_k']
    original=read_json('v2/q8_live_ANALYSIS.json')
    arms=original['all_eight_arms']
    check_close('q8 repeated measurements per arm', [a['measurements'] for a in arms], [128]*8)
    assert sum(a['measurements'] for a in arms)==original['measured_requests']==1024
    fields=[('cycles','cycles'),('proposed','proposed'),('verify_physical_rows','verify_rows'),('emitted_tokens','output_tokens')]
    expected=[];observed=[]
    for arm in arms:
        k=arm['label'].rsplit('k',1)[1]
        observed.append([arm[source_key] for source_key,_ in fields])
        expected.append([work[k][projection_key] for _,projection_key in fields])
    check_close('q8 shared per-arm work counts, not a sum across methods',observed,expected)
    fig=plt.figure(figsize=(7,3.30))
    a=fig.add_axes([.09,.30,.235,.49]);b=fig.add_axes([.425,.30,.24,.49]);c=fig.add_axes([.755,.30,.225,.49])
    clean(a,'y');refline(a,'y');ptitle(a,'a','Same eight known tokens')
    eqpoints=[]
    for i,cell in enumerate(eq['cells']):
        ratios=np.asarray(cell['q8'])/np.asarray(cell['q4pair']);val=sum(cell['q8'])/sum(cell['q4pair'])
        a.scatter(i+np.linspace(-.09,.09,4),ratios,s=17,marker='o' if cell['geometry']=='within' else '^',
                  facecolors=BLUE if cell['geometry']=='within' else WHITE,edgecolors=BLUE,lw=.75,zorder=3)
        a.plot(i,val,marker='_',ms=13,mew=2,color=INK,zorder=4,ls='none')
        eqpoints.append({'projection':cell['projection'],'geometry':cell['geometry'],'ratio':val,'origin_ratios':ratios.tolist()})
    a.set_xlim(-.5,3.5);a.set_ylim(.79,1.10);a.set_xticks(range(4),['L4\ninside','L4\ncross','P\ninside','P\ncross'])
    a.set_ylabel('q = 8 / two q = 4 operation time');a.yaxis.set_major_locator(MultipleLocator(.1))
    a.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
    a.text(.5,-.31,'Four origin aggregates per cell',transform=a.transAxes,ha='center',fontsize=8.2)
    clean(b,'y');ptitle(b,'b','Live work changes')
    counts=[('cycles','Cycles',BLUE,'v'),('output_tokens','Emitted',GRAY,'o'),('verify_rows','Verified',OCHRE,'s'),('proposed','Proposals',OCHRE,'^')]
    work_ratios={}
    for key,label,col,marker in counts:
        ratio=work['7'][key]/work['3'][key];work_ratios[key]=ratio
        b.plot([0,1],[1,ratio],color=col,lw=1.3,marker=marker,ms=4,
               mfc=WHITE if key=='output_tokens' else col,mew=.8,zorder=3)
        b.text(1.12,ratio,label,fontsize=8.2,va='center',color=col)
    b.axhline(1,color=GRAY,lw=.6,ls=(0,(3,2)))
    b.set_xlim(-.13,2.10);b.set_ylim(.54,1.65);b.set_xticks([0,1],['k = 3','k = 7'])
    b.set_ylabel('Work relative to k = 3');b.set_yticks([.6,1.0,1.4,1.6])
    b.text(.5,-.31,'Per-arm counts; same emitted total',transform=b.transAxes,ha='center',fontsize=8.2)
    clean(c,'y');refline(c,'y');ptitle(c,'c','Service becomes slower')
    primary=[x for x in live['contrasts'] if x['family']=='primary']
    for i,item in enumerate(primary):
        ratios=item['root_ratios'];strip_offsets=np.resize([-.10,-.05,0,.05,.10],len(ratios))
        c.scatter(i+np.asarray(strip_offsets),ratios,s=9,color=GRAY,alpha=.5,lw=0,zorder=2)
        lo,hi=item['adjusted_interval'];val=item['ratio']
        c.plot([i,i],[lo,hi],color=OCHRE,lw=1.5,zorder=4)
        c.plot([i,i],[lo,hi],marker='_',color=OCHRE,ms=5,ls='none',zorder=4)
        c.plot(i,val,marker='D',color=OCHRE,ms=4,ls='none',zorder=5)
    c.set_xlim(-.5,3.5);c.set_ylim(.98,1.40);c.set_xticks(range(4),['L4','P','L4','P'])
    c.text(.25,-.19,'SIMPLE',transform=c.transAxes,ha='center',fontsize=8.2)
    c.text(.75,-.19,'LOCAL',transform=c.transAxes,ha='center',fontsize=8.2)
    c.set_ylabel('k = 7 / k = 3 service time');c.set_yticks([1.0,1.2,1.4])
    c.text(.5,-.31,'16 roots; original 98.75% intervals',transform=c.transAxes,ha='center',fontsize=8.2)
    fig.text(.09,.945,'Faster fixed-work execution can coexist with slower service',fontsize=10,fontweight='bold')
    fig.text(.09,.105,'Each arm: 11,472 emitted tokens; verified rows 14,016 → 18,368; proposals 10,512 → 16,072.',fontsize=8.45)
    fig.text(.09,.04,'Windows RTX: fixed-work operation and live resident-service measurements have separate clocks.',fontsize=8.3)
    save(fig,'fig07_work_cost',['pr222/q8_equal_work.json','pr222/q8_recomputed.json','pr222/q8_root_sums.json','pr222/q8_phase_work.json','v2/q8_live_ANALYSIS.json'],7,3.30,
         {'equal_work_origin_aggregates':16,'live_root_ratios':64,'workload_counts':8})
    METRICS['work_cost']={'equal_work':eqpoints,'work_counts':work,'work_count_scope':'Per-arm sums over 128 requests (16 roots x eight repeated order blocks); shared across all four methods at each k, not summed over methods.','work_ratios_k7_over_k3':work_ratios,'live_contrasts':primary}
    CAPTIONS['fig07_work_cost']=(
        'Wider execution changes both efficiency and live work. (a) One q=8 call is compared '
        'with two q=4 calls for the same eight known tokens and requested outputs. Points '
        'are four origin-level operation aggregates per cell; black ticks are ratios of totals. '
        '(b) Per-arm counts cover 128 measured requests (sixteen roots in eight repeated order '
        'blocks). The four methods share the displayed counts at each k. Normalized to '
        'k=3, verification cycles fall from 3,504 to 2,296 at k=7, '
        'while verified rows and draft proposals rise; the emitted total remains 11,472. '
        '(c) All sixteen root ratios per method remain visible. Diamonds show total resident-service '
        'ratios with the original 98.75% paired-root intervals for four contrasts. L4 denotes '
        'backend-loop4 and P packed projection. The fixed-work operation experiment and live-service '
        'experiment are separate; the panels explain the observed tradeoff without fitting a service prediction.')


def width_tradeoff():
    eq=read_json("pr222/q8_equal_work.json");live=read_json("pr222/q8_recomputed.json");work=read_json("pr222/q8_phase_work.json")
    fig=plt.figure(figsize=(7,3.8))
    ax1=fig.add_axes([.16,.42,.30,.43]);ax2=fig.add_axes([.65,.42,.32,.43])
    for ax in [ax1,ax2]:clean(ax);refline(ax)
    ptitle(ax1,"a","Equal work: q = 8 / two q = 4 calls")
    ptitle(ax2,"b","Live service: k = 7 / k = 3")
    labels=[];eqmetrics=[]
    for i,c in enumerate(eq["cells"]):
        rr=np.asarray(c["q8"])/np.asarray(c["q4pair"]);val=sum(c["q8"])/sum(c["q4pair"])
        strip(ax1,rr,3-i+.12,s=19,spread=.08)
        forest(ax1,val,3-i-.14,None,BLUE,"D")
        labels.append(c["projection"]+", "+("inside" if c["geometry"]=="within" else "crossing"))
        eqmetrics.append({"projection":c["projection"],"geometry":c["geometry"],"ratio":val,"origin_ratios":rr.tolist()})
    ax1.set_yticks(range(4),labels[::-1]);ax1.tick_params(axis="y",length=0,pad=5)
    ax1.set_xlim(.78,1.10);ax1.set_ylim(-.6,3.5);ax1.set_xlabel("Operation-time ratio")
    ax1.xaxis.set_major_locator(MultipleLocator(.1));ax1.xaxis.set_major_formatter(FormatStrFormatter("%.1f"))
    primary=[c for c in live["contrasts"] if c["family"]=="primary"]
    rootdata=read_json("pr222/q8_root_sums.json")
    arm_totals=dict(zip(rootdata["arms"],np.asarray(rootdata["sums"]).sum(axis=1)))
    labs=[]
    for i,c in enumerate(primary):
        val=arm_totals[c["numerator"]]/arm_totals[c["denominator"]]
        check_close("live width "+c["numerator"],val,c["ratio"])
        strip(ax2,c["root_ratios"],3-i+.12,s=13,spread=.09)
        forest(ax2,val,3-i-.14,c["adjusted_interval"],OCHRE,"D")
        labs.append(c["numerator"].replace("-k7","").replace("W-","SIMPLE ").replace("L-","LOCAL "))
    ax2.set_yticks(range(4),labs[::-1]);ax2.tick_params(axis="y",length=0,pad=5)
    ax2.set_xlim(.98,1.40);ax2.set_ylim(-.6,3.5);ax2.set_xlabel("Resident-service-time ratio")
    ax2.xaxis.set_major_locator(MultipleLocator(.1));ax2.xaxis.set_major_formatter(FormatStrFormatter("%.1f"))
    # Exact work counts are shown as a compact table, never with invented errors.
    at=fig.add_axes([.16,.045,.81,.22]);at.axis("off")
    counts=work["work_by_k"]
    rowkeys=[("Verification cycles","cycles"),("Proposals","proposed"),("Verified rows","verify_rows"),("Emitted tokens","output_tokens")]
    at.text(0,.99,"(c)  Live work changes even when the emitted output count is fixed",fontweight="bold",fontsize=9.2)
    for j,(label,key) in enumerate(rowkeys):
        x=.125+j*.25
        at.text(x,.64,label,ha="center",fontsize=8.4)
        at.text(x,.18,f"{counts['3'][key]:,}  →  {counts['7'][key]:,}",ha="center",fontsize=9.5,color=OCHRE if key!="output_tokens" else INK)
    save(fig,"supp01_width_tradeoff",["pr222/q8_equal_work.json","pr222/q8_recomputed.json","pr222/q8_root_sums.json","pr222/q8_phase_work.json"],7,3.8,
         {"equal_work_origin_ratios":16,"live_root_ratios":64,"work_counts":8})
    METRICS["width_tradeoff"]={"equal_work":eqmetrics,"live":primary,"work":counts}
    CAPTIONS["supp01_width_tradeoff"] = (
        "Wider execution is beneficial at equal work and adverse when it changes live "
        "speculative work in this RTX experiment. (a) Each dot is one of four published "
        "origin-level operation aggregates; the diamond is the ratio of total q8 time "
        "to the time of two q4 calls. No operation-level distribution is reconstructed. "
        "(b) Each dot is one of 16 root-level live-service ratios; diamonds and segments "
        "are the reported total-time estimates and 98.75% root-bootstrap intervals "
        "for four primary contrasts. All eight measured blocks remain inside each root. "
        "(c) Per-arm counts over 128 measured requests are shared by the four methods at "
        "each k. They show fewer verification cycles but more proposals and verified rows "
        "at k=7, with the same emitted-token count. Operation and resident "
        "service timers belong to separate experiments and have separate scales.")


def width_cost():
    data=read_json("pr222/q8_phase_work.json");a=data["arms"][6];b=data["arms"][7]
    assert a["arm"]==6 and b["arm"]==7
    labels={"target_prefill_s":"Target prefill","draft_prefill_s":"Draft prefill", "target_verify_s":"Target verify",
            "draft_sync_s":"Draft sync","draft_propose_s":"Draft propose","setup_s":"Setup",
            "teardown_s":"Teardown","planning_s":"Planning","owned_output_copy_s":"Output copy","unassigned_residual_s":"Residual"}
    ds={k:b["phases"][k]-a["phases"][k] for k in a["phases"]}
    total=sum(b["session_service_s"])-sum(a["session_service_s"])
    check_close("width phase balance",sum(ds.values()),total,atol=1e-8)
    fig=plt.figure(figsize=(7,2.85));ax=fig.add_axes([.19,.17,.76,.69]);clean(ax)
    ax.axvline(0,color=INK,lw=.8)
    ys=np.arange(len(ds)+1)[::-1]
    for y,(key,val) in zip(ys[:-1],ds.items()):
        col=BLUE if val<0 else OCHRE
        ax.plot([0,val],[y,y],color=col,lw=3.4,solid_capstyle="butt")
        ax.plot(val,y,marker="o",color=col,ms=3.2,ls="none")
        number=f"{val:+.6f}" if abs(val)<.001 else f"{val:+.3f}"
        ax.text(val+(.35 if val>=0 else -.35),y,number,ha="left" if val>=0 else "right",va="center",fontsize=8.1)
    ax.axhline(.5,color=PALE,lw=.7)
    ax.plot([0,total],[0,0],color=INK,lw=3.8);ax.plot(total,0,marker="D",color=INK,ms=4)
    ax.text(total+.35,0,f"{total:+.3f}",va="center",fontsize=8.2,fontweight="bold")
    ax.set_yticks(ys,[labels[k] for k in ds]+["Complete service"]);ax.tick_params(axis="y",length=0)
    ax.set_ylim(-.7,10.7);ax.set_xlim(min(ds.values())-4,max(total,max(ds.values()))+4)
    ax.set_xlabel("Host-phase time change, k = 7 minus k = 3 (s)")
    ptitle(ax,"a","LOCAL-packed: every signed phase contribution")
    save(fig,"supp02_width_cost",["pr222/q8_phase_work.json"],7,2.85,{"phase_differences":10,"service_difference":1})
    METRICS["width_cost"]={"differences_s":ds,"service_difference_s":total}
    CAPTIONS["supp02_width_cost"] = (
        "Signed host-phase costs for LOCAL-packed in the live-width experiment. Values "
        "are complete phase sums for k=7 minus k=3, with the same 16 roots and eight "
        "blocks per arm. Negative contributions, including draft synchronization, "
        "remain visible. The residual is the difference between the complete service "
        "timer and named phases; it is not assigned to a hypothesized mechanism. "
        "The ten contributions reproduce the complete service difference. These are "
        "host accounting totals rather than isolated GPU-kernel times.")


def historical_geometry():
    d=read_json("pr222/historical_evidence.json")["vulkan_width"]
    deployments=list(dict.fromkeys(c["deployment"] for c in d));qs=[2,4,8,16,32]
    fig=plt.figure(figsize=(7,2.45));ax=fig.add_axes([0,0,1,1]);ax.set_xlim(0,7);ax.set_ylim(0,2.45);ax.axis("off")
    ax.text(.1,2.28,"Historical fixed-work geometry: LOCAL / SIMPLE time",fontsize=9.4,fontweight="bold")
    for j,q in enumerate(qs):ax.text(2.29+j*.95,1.97,f"q = {q}",ha="center",fontsize=8.8)
    rows=[]
    for i,dep in enumerate(deployments):
        y=1.62-i*.55
        label=dep.replace("Qwen C","Qwen · C").replace("Smol C","Smol · C").replace(" dual-resident","\ndual resident").replace(" target-only","\ntarget only")
        ax.text(.1,y,label,va="center",fontsize=8.6)
        for j,q in enumerate(qs):
            c=next((c for c in d if c["deployment"]==dep and c["q"]==q),None)
            x=1.84+j*.95
            if c is None:
                box(ax,x,y-.22,.90,.44,"Not measured",LIGHT,PALE,hatch="..",fs=8.1)
                continue
            crossing,inside=1/c["cross"],1/c["inside"]
            fill=BLUE_LIGHT if crossing<1 else OCHRE_LIGHT
            col=BLUE if crossing<1 else OCHRE
            box(ax,x,y-.22,.90,.44,"",fill,PALE)
            ax.text(x+.45,y+.055,f"{crossing:.3f}",ha="center",fontsize=9.8,color=col,fontweight="bold")
            ax.text(x+.45,y-.115,f"inside {inside:.3f}",ha="center",fontsize=8.0)
            rows.append({"deployment":dep,"q":q,"local_over_whole_crossing":crossing,"local_over_whole_inside":inside,"blocks":c["blocks"]})
    ax.text(.1,.10,"All measured and unmeasured cells retained. These splits differ from the 1 + (q − 1) panel.",fontsize=8.6)
    save(fig,"supp03_historical_geometry",["pr222/historical_evidence.json"],7,2.45,{"measured_cells":14,"inside_controls":14,"unmeasured_cells":1})
    METRICS["historical_geometry"]=rows
    CAPTIONS["supp03_historical_geometry"] = (
        "Archived Vulkan fixed-work geometry retains the adverse wide-query cases. "
        "Each measured cell reports the crossing LOCAL/WHOLE time ratio and its "
        "inside-range control; all ratios are reciprocals of the archived WHOLE/LOCAL "
        "estimator. The q=32 crossing cases use the historical split geometry, including "
        "16+16 cuts, and favor WHOLE in these configurations. The unmeasured Smol q=4 "
        "cell is labeled explicitly. These historical deployments and block estimators "
        "are separate from the final controlled 1+(q-1) B570 panel; no intervals or "
        "unobserved timings are invented.")


def old32_and_lifecycle():
    d=frame("pr222/q32_measurements.csv");result=read_json("pr222/q32_recomputed.json")
    arms=list(result["totals"]);means=d.groupby(["root","arm"]).service_s.mean().unstack().loc[:,arms]
    check_close("32B totals",d.groupby("arm").service_s.sum().loc[arms].values,list(result["totals"].values()))
    fig=plt.figure(figsize=(7,3.45));ax1=fig.add_axes([.15,.30,.335,.53]);ax2=fig.add_axes([.68,.30,.29,.53])
    clean(ax1);clean(ax2);ptitle(ax1,"a","Earlier 32B: six fixed arms");ptitle(ax2,"b","Llama: the lifecycle reverses rank")
    for i,arm in enumerate(arms):
        xs=means[arm].values
        strip(ax1,xs,5-i+.11,s=20,spread=.075)
        forest(ax1,xs.mean(),5-i-.12,None,BLUE if arm.endswith("_M") else OCHRE,"D")
    labels=["W scalar · M","W grouped · M","L scalar · M","L grouped · M","W scalar · D4","L grouped · D4"]
    ax1.set_yticks(range(6),labels[::-1]);ax1.tick_params(axis="y",length=0,pad=5)
    ax1.set_ylim(-.6,5.5);ax1.set_xlim(4.0,12.5);ax1.set_xlabel("Resident service per request (s)")
    app=next(a for a in read_json("pr222/applications.json") if a["pr"]==205)
    controls=["W_L4_M","W_P_M","L_L4_M","L_P_M"]
    ratios=[]
    refline(ax2)
    for i,ctrl in enumerate(controls):
        y=3-i
        service=app["totals"]["L_P_D4"]/app["totals"][ctrl]
        worker=app["process_s"]["L_P_D4"]/app["process_s"][ctrl]
        ax2.plot([service,worker],[y,y],color=PALE,lw=1.0,zorder=1)
        forest(ax2,service,y,None,BLUE,"o",ms=4.4)
        forest(ax2,worker,y,None,OCHRE,"s",filled=False,ms=4.4)
        ratios.append({"control":ctrl,"service":service,"worker":worker})
    ax2.set_yticks(range(4),["LOCAL-packed M","LOCAL-loop4 M","SIMPLE-packed M","SIMPLE-loop4 M"])
    ax2.tick_params(axis="y",length=0,pad=5);ax2.set_ylim(-.6,3.5);ax2.set_xlim(.85,1.065)
    ax2.xaxis.set_major_locator(MultipleLocator(.1));ax2.xaxis.set_major_formatter(FormatStrFormatter("%.1f"))
    ax2.set_xlabel("LOCAL-packed D4 / fixed M time")
    fig.legend(handles=[Line2D([],[],marker="o",color=BLUE,ls="none",label="Resident service"),
                        Line2D([],[],marker="s",color=OCHRE,mfc=WHITE,ls="none",label="Complete worker")],
               loc="lower center",bbox_to_anchor=(.53,.10),ncol=2,frameon=False)
    fig.text(.115,.035,"Four exposed 32B roots. Worker totals include process/load/primer work; source values are rounded.",fontsize=8.6)
    save(fig,"supp04_prior32b_lifecycle",["pr222/q32_measurements.csv","pr222/q32_recomputed.json","pr222/applications.json"],7,3.45,
         {"prior32b_root_means":24,"lifecycle_control_ratios":8})
    METRICS["prior32b_lifecycle"]={"prior32b_mean_s":means.mean().to_dict(),"llama_ratios":ratios}
    CAPTIONS["supp04_prior32b_lifecycle"] = (
        "Two limits of favorable resident-service results. (a) The earlier mixed-Q4 "
        "32B panel shows all six arms and four exposed-root means (four rounds per "
        "root). Its grouped path improves on graph-scalar controls, but LOCAL-grouped "
        "D4 is slower than the fastest M. These graph-scalar comparisons do not "
        "replace the later strong backend-scalar control. (b) Llama LOCAL-packed "
        "D4 is faster than each fixed M within the resident-service timer but slower "
        "within the complete-worker timer, which includes process, file-check, model-load "
        "and primer work. The worker totals are source-rounded, the OS cache was "
        "not cleared, and these measurements do not estimate production cold-start "
        "latency or TTFT. Neither panel is assigned a new population interval.")


def rtx_contracts():
    fig=plt.figure(figsize=(7,2.65))
    axs=[fig.add_axes([.17,.37,.21,.41]),fig.add_axes([.45,.37,.225,.41]),fig.add_axes([.745,.37,.225,.41])]
    spec=[("pr230/TIMING_SAMPLES.csv","C","C · legacy contract",6),
          ("pr234/ALL_SAMPLES.csv","C1","C1 · legacy contract",12),
          ("pr237/ALL_SAMPLES.csv","U","U · changed contract",12)]
    out=[]
    analysis=read_json("pr237/ANALYSIS.json")
    for ax,(f,candidate,title,npairs),letter in zip(axs,spec,["a","b","c"]):
        d=frame(f);clean(ax);refline(ax);ptitle(ax,letter,title)
        for j,mode in enumerate(["kernel-only","complete-operator"]):
            sub=d[d["mode"]==mode].copy()
            # Compute from the stored event duration, not the float-rounded
            # per_operator_ms convenience column in the U experiment.
            sub["operator_ms"] = sub.event_ms / sub.batch_repetitions
            tab=sub.pivot(index="block",columns="arm",values="operator_ms")
            if candidate not in tab:
                # C1 is the implementation name; its measurement arm is C.
                cand="C" if candidate=="C1" and "C" in tab else candidate
            else:cand=candidate
            rr=(tab[cand]/tab.B).values
            assert len(rr)==npairs
            value=float(np.exp(np.log(rr).mean()))
            strip(ax,rr,1-j+.12,s=16,spread=.08)
            ci=None
            if candidate=="U":
                a=analysis["summary"][mode];check_close("RTX U "+mode,value,a["U_over_B_geomean"])
                ci=a["paired_log_bootstrap_95pct"]
            forest(ax,value,1-j-.16,ci,OCHRE if value>1 else BLUE,"D")
            ax.text(.5,1-j-.43,f"{value:.4f}",transform=ax.get_yaxis_transform(),ha="center",fontsize=8.2)
            out.append({"candidate":candidate,"mode":mode,"ratio_geomean":value,"paired_ratios":rr.tolist(),"ci95":ci})
        ax.set_ylim(-.65,1.55);ax.set_xlim((.54,1.04) if candidate=="U" else (.95,1.20))
        ax.xaxis.set_major_locator(MultipleLocator(.2 if candidate=="U" else .1));ax.xaxis.set_major_formatter(FormatStrFormatter("%.1f"))
        ax.set_yticks([0,1],["Quant. + projection","Projection"] if ax is axs[0] else ["",""])
        ax.tick_params(axis="y",length=0);ax.set_xlabel(candidate+"/B operator-time ratio")
    fig.text(.145,.15,"One captured input; each panel is a separate experiment. Dots are paired blocks, not inputs.",fontsize=8.6)
    fig.text(.145,.07,"U differs in 32,766/32,768 outputs. The complete modern backend was not timed.",fontsize=8.6)
    save(fig,"supp05_rtx_contracts",[s[0] for s in spec]+["pr237/ANALYSIS.json"],7,2.65,
         {"paired_ratios":60,"independent_captured_inputs":1,"modern_full_backend_timings":0})
    METRICS["rtx_contracts"]=out
    CAPTIONS["supp05_rtx_contracts"] = (
        "The RTX operator studies distinguish optimization within a reference from "
        "changing the numerical contract. Each study uses one captured Qwen3-8B "
        "Q8_0 projection input (4096 by 4096 weights, eight query columns) on the "
        "RTX 5070 Ti Laptop. C and C1 preserve the legacy contract but their "
        "complete-operator geometric ratios exceed 1; U is an extracted modern "
        "upstream path with a different quantization/arithmetic contract. All paired "
        "blocks are shown (six for C, twelve each for C1 and U at each boundary). "
        "U's displayed intervals are the original paired-log 95% intervals, conditional "
        "on this captured input and session. The quantization-plus-projection U/B "
        "ratio is 0.612924 [0.607906, 0.618665], not a service improvement produced "
        "by the fixed-reference method. Event timers exclude allocation, copies and "
        "checking; CUDA graphs are off. U differs in 32,766 of 32,768 output elements "
        "from B. The full default modern backend was not run; it is not plotted as zero.")


def natural_table():
    d=frame("closeout/service/FREE_EPISODES.csv")
    p=d.pivot(index=["case","round"],columns="arm",values="service_s")
    rows=[]
    for (case,rd),r in p.iterrows():
        rows.append({"case":case,"round":int(rd),"WHOLE_s":r.W,"LOCAL_s":r.L,"LOCAL_over_WHOLE":r.L/r.W})
    summary=read_json("closeout/service/ORIGINAL_RESULTS.json")["free"]
    check_close("natural multi-turn aggregate",p.L.sum()/p.W.sum(),summary["L_over_W"])
    METRICS["natural_multiturn"]={"pairs":rows,"WHOLE_total_s":float(p.W.sum()),"LOCAL_total_s":float(p.L.sum()),"ratio":float(p.L.sum()/p.W.sum()),"independent_cases":2,"rounds":2,"confidence_interval":None}
    (DATA/"derived").mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(DATA/"derived"/"natural_pairs.csv",index=False,float_format="%.15g")
    row_end=chr(92)*2
    tex=["% Generated from the pinned public FREE_EPISODES.csv; no new CI.",
         "\\begin{tabular}{llrrr}","\\toprule", "Case & Round & SIMPLE (s) & LOCAL (s) & L/W "+row_end,"\\midrule"]
    for r in rows:tex.append(f"{r['case']} & {r['round']+1} & {r['WHOLE_s']:.4f} & {r['LOCAL_s']:.4f} & {r['LOCAL_over_WHOLE']:.4f} "+row_end)
    tex += ["\\midrule",f"Total & & {p.W.sum():.4f} & {p.L.sum():.4f} & {p.L.sum()/p.W.sum():.4f} "+row_end,"\\bottomrule","\\end{tabular}"]
    (GEN/"figure_natural_table.tex").write_text("\n".join(tex)+"\n")


def application_controls_table():
    row_end=chr(92)*2
    tex=["% All five fixed application comparisons per model; generated from public timing rows.",
         "% Requires booktabs. Numerator throughout: L_P_D4. W denotes SIMPLE.",
         "\\begin{tabular}{llrrr}","\\toprule",
         "Target & Fixed comparator & Time ratio & 99\\% lower & 99\\% upper "+row_end,"\\midrule"]
    entries=[]
    for idx,(pr,model,nroot) in enumerate([("pr203","Qwen3-8B",16),("pr206","Qwen3-14B",16),("pr205","Llama-8B",12)]):
        plan,sums,result=data_table(pr)
        for j,c in enumerate(contrasts(result)):
            den=c["denominator"];num=c["numerator"]
            val=float(sums[num].sum()/sums[den].sum());ci=interval(c)
            check_close(pr+" all fixed controls "+den,val,c["total_ratio"])
            entry={"model":model,"roots":nroot,"numerator":num,"denominator":den,
                   "ratio_of_totals":val,"ci99_low":ci[0],"ci99_high":ci[1],
                   "numerator_total_s":float(sums[num].sum()),"denominator_total_s":float(sums[den].sum()),
                   "source_timing":f"closeout/{pr}/TIMING_ROWS.csv","source_interval":f"closeout/{pr}/ORIGINAL_RESULTS.json"}
            entries.append(entry)
            dlabel=den.replace("_",chr(92)+"_")
            tex.append(f"{model if j==0 else ''} & \\texttt{{{dlabel}}} & {val:.6f} & {ci[0]:.6f} & {ci[1]:.6f} "+row_end)
        if idx<2:tex.append("\\addlinespace")
    tex += ["\\bottomrule","\\end{tabular}"]
    (GEN/"figure_application_controls.tex").write_text("\n".join(tex)+"\n")
    pd.DataFrame(entries).to_csv(DATA/"derived"/"application_controls.csv",index=False,float_format="%.15g")
    METRICS["all_application_controls"]=entries


def finish():
    (GEN/"figure_metrics.json").write_text(json.dumps(METRICS,indent=2,ensure_ascii=False)+"\n")
    (GEN/"figure_manifest.json").write_text(json.dumps(FIGURES,indent=2,ensure_ascii=False)+"\n")
    (GEN/"figure_layout_check.json").write_text(json.dumps(LAYOUT,indent=2,ensure_ascii=False)+"\n")
    (GEN/"figure_numeric_checks.json").write_text(json.dumps(CHECKS,indent=2)+"\n")
    captions=["% Caption drafts; root manuscript author may edit prose, not statistical scope."]
    for name,text in CAPTIONS.items():
        escaped=text.replace("WHOLE","SIMPLE").replace("%","\\%").replace("_","\\_")
        captions += ["% "+name, "\\expandafter\\def\\csname caption"+name+"\\endcsname{"+escaped+"}",""]
    (GEN/"figure_captions.tex").write_text("\n".join(captions)+"\n")
    report={"figure_count":len(FIGURES),"numeric_checks":len(CHECKS),"all_pass":all(x["pass"] for x in CHECKS),"font":FONT,"source_input_mutations":0,"GPU_runs":0}
    print(json.dumps(report,indent=2))


def main():
    verify_sources()
    with plt.rc_context(STYLE):
        overview();extent();strong_baseline();factorial();application();geometry();work_cost()
        width_tradeoff();width_cost();historical_geometry();old32_and_lifecycle();rtx_contracts();natural_table();application_controls_table()
    finish()


if __name__ == "__main__":
    main()
