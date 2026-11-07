"""Rebuild the paper's timing table and editable plot from saved block times."""
from pathlib import Path
import json
import math

ROOT = Path(__file__).resolve().parents[1]


def gm(values):
    xs = list(values)
    if not xs or not all(math.isfinite(x) and x > 0 for x in xs):
        raise ValueError("Expected positive finite service times/ratios")
    return math.exp(math.fsum(map(math.log, xs)) / len(xs))


def reconstruct(platform):
    data = json.loads((ROOT / "data" / f"{platform}_cost.json").read_text())
    blocks = data["blocks"]
    identity = "input" if platform == "rtx" else "input_id"
    inputs = {b[identity] for b in blocks}
    cells = {(b["session"], b[identity]) for b in blocks}
    expected = {(s, i) for s in range(6) for i in inputs}
    if len(inputs) != 24 or len(blocks) != 144 or cells != expected:
        raise ValueError("Incomplete, duplicate or unexpected timing panel")
    ratios = []
    for b in blocks:
        t = b.get("seconds", b.get("service_seconds"))
        if set(t) != {"R", "M_PQ", "M_QB", "C_PQ_A", "C_PQ_B", "C_QB"}:
            raise ValueError("Unexpected timing arms")
        if not all(math.isfinite(v) and v > 0 for v in t.values()):
            raise ValueError("Invalid measured time")
        pq = (t["C_PQ_A"] + t["C_PQ_B"]) / 2
        row = {
            "layout": t["C_QB"] / pq, "AA": t["C_PQ_A"] / t["C_PQ_B"],
            "D_QB": t["M_QB"] / t["C_QB"], "D_PQ": t["M_PQ"] / pq,
            "CQB_R": t["C_QB"] / t["R"], "MQB_R": t["M_QB"] / t["R"],
            "MPQ_R": t["M_PQ"] / t["R"], "CPQ_R": pq / t["R"],
            "MQB_MPQ": t["M_QB"] / t["M_PQ"],
        }
        for key in set(row).intersection(b):
            if not math.isclose(row[key], b[key], abs_tol=1e-12, rel_tol=1e-12):
                raise ValueError(f"Saved block ratio mismatch: {key}")
        ratios.append(row)
    means = {k: gm(r[k] for r in ratios) for k in ratios[0]}
    for key, value in data["means"].items():
        if not math.isclose(value, means[key], abs_tol=1e-12, rel_tol=1e-12):
            raise ValueError(f"Saved aggregate mismatch: {key}")
    aa = [gm(r["AA"] for r, b in zip(ratios, blocks) if b[identity] == i) for i in inputs]
    threshold = max(.02, max(max(v, 1/v) - 1 for v in aa))
    sessions = [gm(r["layout"] for r, b in zip(ratios, blocks) if b["session"] == s)
                for s in range(6)]
    registered = data.get("sessions", data.get("session_layout"))
    if not all(math.isclose(a, b, rel_tol=1e-12) for a, b in zip(sessions, registered)):
        raise ValueError("Session mismatch")
    if not math.isclose(threshold, data.get("AA_max_symmetric_input", data.get("AA_threshold")), rel_tol=1e-12):
        raise ValueError("A/A threshold mismatch")
    screen = 1-means["layout"] > threshold and all(x < 1 for x in sessions)
    if screen != data.get("practical_layout_gain", data.get("practical_layout_screen")):
        raise ValueError("Screen mismatch")
    return {"means": means, "sessions": sessions, "threshold": threshold,
            "screen": screen, "measured_values": 864,
            "C_slower_blocks": sum(r["layout"] > 1 for r in ratios),
            "M_slower_blocks": sum(r["MQB_MPQ"] > 1 for r in ratios)}


def write_table(results):
    r, v = (results[k] for k in ("rtx", "b570"))
    rows = [
        (r"$C_{\QB}/\overline{C_{\PQ}}$", "layout", "Speculative layout; primary"),
        (r"$M_{\QB}/M_{\PQ}$", "MQB_MPQ", "Target-only layout; post hoc"),
        (r"$M_{\QB}/C_{\QB}$", "D_QB", "Draft value; above one favors draft"),
        (r"$C_{\QB}/R$", "CQB_R", "Complete speculative path"),
        (r"$M_{\QB}/R$", "MQB_R", "Complete target-only path"),
    ]
    lines = [r"\begin{table*}[t]\centering\small",
             r"\caption{Reconstructed complete-request ratios on the two new Llama panels. Each platform uses all 144 paired blocks. The target-only layout comparison is post hoc; the practical screen applies to the speculative layout comparison.}",
             r"\label{tab:costs}",
             r"\begin{tabularx}{\textwidth}{@{}lrrY@{}}\toprule",
             r"Comparison & CUDA & Vulkan & Meaning\\\midrule"]
    for label, key, meaning in rows:
        lines.append(f"{label} & {r['means'][key]:.4f} & {v['means'][key]:.4f} & {meaning}"+r"\\")
    lines += [
        f"A/A screen & {100*r['threshold']:.3f}"+r"\% & "+f"{100*v['threshold']:.3f}"+r"\% & Predeclared engineering threshold\\",
        r"Speculative layout screen & Not passed & Passed & Requires all six sessions favorable\\",
        f"Slower speculative blocks & {r['C_slower_blocks']}/144 & {v['C_slower_blocks']}/144 & All blocks retained"+r"\\\bottomrule",
        r"\end{tabularx}\end{table*}"]
    (ROOT / "cost_table.tex").write_text("\n".join(lines)+"\n")


def write_plot(results):
    lines = [r"\begin{tikzpicture}"]
    for j, (platform, title, color) in enumerate((("rtx", "CUDA / RTX", "target"), ("b570", "Vulkan / B570", "qualified"))):
        d = results[platform]
        x = .6 + j * 8.3
        threshold = 1-d["threshold"]
        lines += [
            r"\begin{axis}["+f"at={{({x}cm,0cm)}},"+r"anchor=south west,scale only axis,",
            r"width=6.8cm,height=3.2cm,xmin=.935,xmax=1.005,ymin=.2,ymax=7.2,",
            r"ytick={1,2,3,4,5,6},yticklabels={1,2,3,4,5,6},",
            r"xtick={.94,.96,.98,1},xlabel={$C_{\QB}/\overline{C_{\PQ}}$},ylabel={Session},",
            f"title={{\\textbf{{{'A' if j==0 else 'B'}}}\\quad {title}}},"+
            r"title style={font=\small},tick label style={font=\footnotesize},",
            r"label style={font=\footnotesize},grid=major,grid style={gray!13},",
            r"axis lines*=left,axis line style={aux},clip=false]",
            r"\addplot[aux,densely dotted,forget plot] coordinates {(1,.2)(1,7.2)};",
            f"\\addplot[{color},dashed,forget plot] coordinates {{({threshold:.12f},.2)({threshold:.12f},7.2)}};",
        ]
        coords=" ".join(f"({a:.12f},{i+1})" for i,a in enumerate(d["sessions"]))
        lines.append(f"\\addplot[only marks,mark=*,mark size=2pt,{color}] coordinates {{{coords}}};")
        lines.append(f"\\addplot[only marks,mark=diamond*,mark size=3pt,{color}] coordinates {{({d['means']['layout']:.12f},6.8)}};")
        lines.append(f"\\node[font=\\scriptsize,anchor=west,text={color}] at (axis cs:{d['means']['layout']+.001:.12f},6.8) {{{d['means']['layout']:.4f}}};")
        lines.append(r"\end{axis}")
    lines.append(r"\end{tikzpicture}")
    (ROOT/"figures/layout_cost.tex").write_text("\n".join(lines)+"\n")


if __name__ == "__main__":
    results = {p: reconstruct(p) for p in ("rtx", "b570")}
    (ROOT / "data/RECOMPUTED.json").write_text(json.dumps(results, indent=2)+"\n")
    write_table(results)
    write_plot(results)
    print("Reconstructed 1,728 saved measured times, both tables/screens and the session plot.")
