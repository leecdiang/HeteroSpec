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
    minimum_font = 8.6 if stem.startswith("supp") else 8.2
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
    fig = plt.figure(figsize=(7,3.45))
    ax = fig.add_axes([0,0,1,1]); ax.set_xlim(0,7); ax.set_ylim(0,3.45); ax.axis("off")
    ax.text(.10,3.29,"(a)  The same visible keys can take different paths",fontsize=9.2,fontweight="bold")
    ax.text(3.74,3.29,"(b)  Two different reasons to group queries",fontsize=9.2,fontweight="bold")
    # A measured example. The source's logical positions are not cache indices.
    x0,cw=1.12,.52
    ax.text(.1,2.91,"Query position",fontsize=8.3,va="center")
    for i,p in enumerate([765,766,767,768]):
        ax.text(x0+cw*(i+.5),2.91,str(p),ha="center",va="center",fontsize=8.5)
    ax.text(.1,2.55,"Scalar reference",fontsize=8.3,va="center")
    ax.text(.1,2.16,"Direct wide call",fontsize=8.3,va="center")
    for i,e in enumerate([768,768,768,1024]):
        box(ax,x0+i*cw,2.39,cw,.30,str(e),BLUE_LIGHT if e==768 else OCHRE_LIGHT,
            BLUE if e==768 else OCHRE,hatch=None if e==768 else "///",fs=8.4)
        box(ax,x0+i*cw,2.00,cw,.30,"1024",OCHRE_LIGHT,OCHRE,hatch="///",fs=8.4)
    ax.text(1.12,1.78,"Physical KV range changes for the first three rows.",fontsize=8.25)
    ax.text(.1,1.54,"A causal mask fixes visibility; it need not fix reduction geometry.",fontsize=8.2)
    # Independent schematic: 8 known columns, a=4 arithmetic inner groups.
    xx=4.63; ww=.272
    ax.text(3.74,2.91,"Eight columns",fontsize=8.25,va="center")
    for i in range(8):
        ax.text(xx+ww*(i+.5),2.91,str(i+1),ha="center",va="center",fontsize=8.3)
    ax.text(3.74,2.55,"KV range",fontsize=8.25,va="center")
    for i in range(8):
        box(ax,xx+i*ww,2.39,ww,.30,"",BLUE_LIGHT if i<3 else OCHRE_LIGHT,
            BLUE if i<3 else OCHRE,hatch=None if i<3 else "///")
    ax.text(3.74,2.16,"Arithmetic",fontsize=8.25,va="center")
    for i in range(8):
        box(ax,xx+i*ww,2.00,ww,.30,"",LIGHT,GRAY,lw=.45)
    for g in range(2):
        box(ax,xx+g*4*ww,1.97,4*ww,.36,"",fill="none",edge=INK,lw=1.1)
    ax.text(xx+ww*2,1.78,"a = 4",ha="center",fontsize=8.3)
    ax.text(xx+ww*6,1.78,"a = 4",ha="center",fontsize=8.3)
    ax.text(3.74,1.54,"Outer groups expose parallel work; inner order stays fixed.",fontsize=8.2)
    ax.plot([.1,6.9],[1.35,1.35],color=PALE,lw=.8)
    ax.text(.1,1.17,"(c)  Cut at the affected consumer, then rejoin in query order",fontsize=9.2,fontweight="bold")
    box(ax,.1,.42,.72,.54,"Known\nqueries",LIGHT,GRAY)
    arrow(ax,(.82,.69),(1.02,.69))
    box(ax,1.02,.42,1.13,.54,"QKV projection\nwide group",BLUE_LIGHT,BLUE)
    arrow(ax,(2.15,.69),(2.35,.69))
    box(ax,2.35,.71,1.26,.30,"Attention: 3 rows",BLUE_LIGHT,BLUE,fs=8.3)
    box(ax,2.35,.34,1.26,.30,"Attention: 1 row",OCHRE_LIGHT,OCHRE,hatch="///",fs=8.3)
    ax.text(2.98,.14,"768 / 1024 KV entries",ha="center",fontsize=8.1)
    arrow(ax,(3.61,.69),(3.84,.69))
    box(ax,3.84,.42,1.12,.54,"O / FFN projection\nwide group",BLUE_LIGHT,BLUE,fs=8.3)
    arrow(ax,(4.96,.69),(5.17,.69))
    box(ax,5.17,.71,1.72,.30,"Full vectors → next consumer",WHITE,INK,fs=8.2)
    box(ax,5.17,.34,1.72,.30,"KV and pending state → reuse",WHITE,INK,fs=8.2)
    save(fig,"fig01_overview",["pr222/rewrite_figure_sources.json"],7,3.45,
         {"measured_positions":4,"arithmetic_schematic_columns":8})
    CAPTIONS["fig01_overview"] = (
        "Preserving a numerical reference leaves more than one way to organize work. "
        "(a) At the measured 765--768 position boundary, scalar calls use physical KV "
        "ranges 768, 768, 768, and 1024, whereas a direct wide call uses 1024 for all rows. "
        "(b) The eight-column drawing is a schematic: physical-range groups and arithmetic "
        "groups need not share boundaries. The illustrated inner width a=4 is used for the "
        "qualified Q8_0 path; the mixed Q4_K/Q6_K path keeps a=1. Independent outer "
        "groups expose parallel work without reordering operations inside a group. "
        "(c) LOCAL confines the 3+1 split to attention and preserves wider projections, "
        "ordered full-vector outputs, and the state required by later consumers. "
        "The diagram describes execution structure, not unrestricted concurrency or a proof "
        "for arbitrary backends. This conceptual figure was produced with AI-assisted code; "
        "the authors are responsible for its content.")


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
    measured=rows[rows.role=="measure"].copy()
    if measured.empty: measured=rows[rows.role=="measured"].copy()
    assert len(measured)==144
    pivot=measured.pivot(index=["slot","root","domain","round"],columns="arm",values="service_s").sort_index()
    pr=frame("pr218/PER_ROOT.csv").sort_values("slot")
    rr=np.exp(np.log(pivot.C/pivot.B).groupby(level="slot").mean()).sort_index()
    check_close("S3 per-root C/B",rr,pr.CB)
    result=read_json("closeout/service/ORIGINAL_RESULTS.json")["S3"]
    for c in result["contrasts"]:
        ratios=np.exp(np.log(pivot[c["candidate"]]/pivot[c["baseline"]]).groupby(level="slot").mean())
        check_close("S3 "+c["candidate"]+"/"+c["baseline"],np.exp(np.log(ratios).mean()),c["ratio"])
    fig=plt.figure(figsize=(7,3.38))
    left=fig.add_axes([.115,.23,.36,.63]);right=fig.add_axes([.64,.40,.34,.46])
    clean(left);clean(right);refline(left);refline(right)
    ptitle(left,"a","C/B for each independent root")
    ptitle(right,"b","The baseline changes the conclusion")
    for slot in range(12):
        q=pivot.loc[slot]
        dots=(q.C/q.B).values
        y=11-slot
        color=BLUE if slot<6 else OCHRE;marker="o" if slot<6 else "^"
        left.plot(dots,np.full(4,y),linestyle="none",marker=marker,ms=3.2,
                  mfc=WHITE,mec=color,mew=.6,alpha=.65,zorder=2)
        left.plot(rr.loc[slot],y,marker=marker,color=color,ms=4.6,ls="none",zorder=4)
    left.set_yticks(range(12),[f"Math {6-i}" for i in range(6)]+[f"Code {12-i}" for i in range(6,12)])
    left.set_xlim(.972,1.003);left.set_ylim(-.65,11.65)
    left.xaxis.set_major_locator(MultipleLocator(.01))
    left.xaxis.set_major_formatter(FormatStrFormatter("%.2f"))
    left.set_xlabel("C/B service-time ratio (lower is faster)")
    left.axhline(5.5,color=PALE,lw=.65)
    for i,c in enumerate(result["contrasts"]):
        y=2-i
        color=BLUE if i==0 else GRAY
        forest(right,c["ratio"],y,c["interval"],color=color,marker="D" if i==0 else "s")
        right.text(.927,y+.27,
                   f"{c['candidate']}/{c['baseline']}  ·  {100*c['confidence']:g}% CI",fontsize=8.1,color=color)
    right.set_yticks([]);right.set_ylim(-.5,2.6);right.set_xlim(.925,1.003)
    right.xaxis.set_major_locator(MultipleLocator(.02))
    right.xaxis.set_major_formatter(FormatStrFormatter("%.2f"))
    right.set_xlabel("Equal-root geometric service-time ratio")
    fig.text(.64,.20,"C/B: 1.51% less service time",fontsize=10.0,fontweight="bold",color=BLUE)
    fig.text(.64,.13,"95% CI: 1.23%–1.79%",fontsize=8.8)
    fig.text(.115,.045,"Open symbols: paired rounds     Filled symbols: root geometric means",fontsize=8.3)
    save(fig,"fig03_strong_baseline",["closeout/service/S3_TIMINGS.csv","closeout/service/ORIGINAL_RESULTS.json","pr218/PER_ROOT.csv"],7,3.38,
         {"roots":12,"paired_rounds":48,"contrasts":3})
    METRICS["strong_baseline"]={"contrasts":result["contrasts"],"root_ratios":rr.tolist(),"measured_rows":144,"warm_rows":144}
    CAPTIONS["fig03_strong_baseline"] = (
        "Strong same-contract service comparison on A5000 with Qwen3-32B-Q4_K_M, "
        "target-only generation and WHOLE execution. G uses graph-level scalar calls; "
        "B quantizes the input once and invokes the backend scalar projection for each "
        "column; C uses independent scalar arithmetic channels. B is not a four-column "
        "loop4 kernel. (a) Four paired rounds are retained inside each of 12 roots "
        "(six code, six mathematics); the filled symbol is the root geometric mean. "
        "(b) Equal-root geometric ratios use the registered stratified root bootstrap "
        "with 20,000 draws. C/B has a 95% interval; the two G comparisons use 97.5% "
        "intervals. C/B is 0.984864 [0.982148, 0.987721], a 1.51% reduction. The resident "
        "service timer includes reset and executed planning, and excludes model/context "
        "creation and terminal heavy exports. Generation is capped at 128 tokens. "
        "The result is a same-deployment target-only increment, not a speculative or "
        "cross-backend service comparison.")


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
    data=read_json("pr222/b570_inputs.json");summary=read_json("pr222/b570_append.json")
    fig=plt.figure(figsize=(7,2.95))
    axs=[fig.add_axes([.09,.36,.39,.48]),fig.add_axes([.58,.36,.39,.48])]
    stats=[]
    for ax,ctx,letter in zip(axs,[1024,4096],["a","b"]):
        clean(ax,"y");refline(ax,"y");ptitle(ax,letter,f"B570 · context capacity {ctx}")
        for j,q in enumerate([2,4,32]):
            for cond,offset,color,marker in [("crossing",-.13,BLUE,"^"),("inside",.13,OCHRE,"o")]:
                key=f"C{ctx}-q{q}-{cond}"
                a=np.asarray(data["cells"][key]);rr=a[2]/a[1];r=a[2].sum()/a[1].sum()
                check_close("B570 "+key,r,data["reported_L_over_S"][key])
                xx=j+offset
                ax.plot([xx,xx],[rr.min(),rr.max()],color=color,lw=1.2,zorder=2)
                ax.scatter(xx+np.array([-.037,0,.037]),rr,s=15,marker=marker,
                           facecolors=color if cond=="crossing" else WHITE,edgecolors=color,lw=.7,zorder=3)
                ax.plot(xx,r,marker="_",ms=10,mew=1.8,color=INK,zorder=4)
                stats.append({"cell":key,"ratio_of_totals":float(r),"paired_ratios":rr.tolist(),"range":[float(rr.min()),float(rr.max())]})
        ax.set_xlim(-.45,2.45);ax.set_ylim(.50,1.13);ax.set_xticks(range(3),["q = 2","q = 4","q = 32"])
        ax.set_xlabel("Append width");ax.yaxis.set_major_locator(MultipleLocator(.1))
        ax.yaxis.set_major_formatter(FormatStrFormatter("%.1f"))
        if ax is axs[0]:ax.set_ylabel("LOCAL / SIMPLE append time")
    handles=[Line2D([],[],color=BLUE,marker="^",ls="none",ms=5,label="Crossing: 1 + (q − 1) split"),
             Line2D([],[],color=OCHRE,marker="o",mfc=WHITE,ls="none",ms=5,label="Inside one physical range")]
    fig.legend(handles=handles,loc="lower center",bbox_to_anchor=(.53,.105),ncol=2,frameon=False,columnspacing=2)
    natural=read_json("pr222/rewrite_figure_sources.json")["natural_geometry"]
    fig.text(.09,.035,f"Natural A5000 Qwen3-8B workload: {natural['whole_extra_call_cycles']:,}/{natural['logical_cycles']:,} verification cycles required an extra SIMPLE call.",fontsize=8.3)
    save(fig,"fig06_geometry",["pr222/b570_inputs.json","pr222/b570_append.json","pr222/rewrite_figure_sources.json"],7,2.95,
         {"fixed_cells":12,"paired_observations":36,"timing_rows":108})
    METRICS["geometry"]={"controlled":stats,"natural":natural}
    CAPTIONS["fig06_geometry"] = (
        "Local cuts help when a physical-range boundary would split a larger amount "
        "of projection work. The controlled B570 SmolLM2-1.7B panel retains all 12 "
        "fixed cells and three paired observations per cell. Crossing cells use a "
        "1+(q-1) split; inside controls remain in one physical range. Symbols are "
        "the paired LOCAL/SIMPLE append-time ratios, segments show their minimum "
        "and maximum, and short black ticks are ratios of summed times. These "
        "ranges are descriptive, not confidence intervals. Crossing reductions "
        "range from 20.34% to 44.68%; inside aggregate ratios are 0.43%--3.74% "
        "slower. The separate natural A5000 Qwen3-8B census found 20 extra-call "
        "cycles among 2,224 logical verification cycles (2,244 WHOLE versus 2,224 "
        "LOCAL physical calls). That count explains a small opportunity fraction; "
        "it is not a service-time measurement from the controlled B570 panel.")


def width_tradeoff():
    eq=read_json("pr222/q8_equal_work.json");live=read_json("pr222/q8_recomputed.json");work=read_json("pr222/q8_phase_work.json")
    fig=plt.figure(figsize=(7,3.8))
    ax1=fig.add_axes([.16,.42,.30,.43]);ax2=fig.add_axes([.65,.42,.32,.43])
    for ax in [ax1,ax2]:clean(ax);refline(ax)
    ptitle(ax1,"a","Equal work: one q8 / two q4 calls")
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
        "(c) Exact work counts show fewer verification cycles but more proposals and "
        "verified rows at k=7, with the same emitted-token count. Operation and resident "
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
        overview();extent();strong_baseline();factorial();application();geometry()
        width_tradeoff();width_cost();historical_geometry();old32_and_lifecycle();rtx_contracts();natural_table();application_controls_table()
    finish()


if __name__ == "__main__":
    main()
