from __future__ import annotations

import os

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(os.environ.get("HETEROSPEC_ROOT", Path(__file__).resolve().parents[1]))
LOG = ROOT / "logs" / "phase4-specbench-pilot-cap128-formal-20260906.json"
OUT = ROOT / "analysis"
FIG = ROOT / "reports" / "figures"
OUT.mkdir(exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)
L0 = 60.16
KS = [1, 2, 4, 6, 8]
RNG = np.random.default_rng(2755070)


def gmean(values):
    values = np.asarray(values, dtype=float)
    return float(np.exp(np.mean(np.log(values))))


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIG / f"{name}.png", dpi=220)
    fig.savefig(FIG / f"{name}.pdf")
    plt.close(fig)


def phase4_rows():
    data = json.loads(LOG.read_text(encoding="utf-8"))
    rows = []
    for q in data["questions"]:
        configs = {c["config"]: c for c in q["configs"]}
        b = configs["B0"]
        b_ms = b["seconds"] * 1000
        for k in KS:
            c = configs[f"SPEC-k{k}"]
            total = c["seconds"] * 1000
            rounds = [r for t in c["turns"] for r in (t.get("rounds") or [])]
            draft = sum(r["draft_ms"] for r in rounds)
            verify = sum(r["target_ms"] for r in rounds)
            residual = max(0.0, total - draft - verify)
            offered = sum(r["offered"] for r in rounds)
            accepted = sum(r["accepted"] for r in rounds)
            rows.append({"question_id": q["question_id"], "task": q["category"], "k": k,
                         "baseline_ms": b_ms, "spec_ms": total, "draft_ms": draft,
                         "verify_ms": verify, "residual_ms": residual,
                         "speedup": b_ms / total, "acceptance": accepted / offered})
    return pd.DataFrame(rows)


def predict(frame, latency):
    scale = latency / L0
    return gmean((frame.baseline_ms * scale) /
                 (frame.draft_ms + frame.residual_ms + frame.verify_ms * scale))


def predict_grid(frame, grid):
    scale = np.asarray(grid, dtype=float)[:, None] / L0
    baseline = frame.baseline_ms.to_numpy()[None, :] * scale
    spec = (frame.draft_ms + frame.residual_ms).to_numpy()[None, :] + frame.verify_ms.to_numpy()[None, :] * scale
    return np.exp(np.mean(np.log(baseline / spec), axis=1))


def main():
    d = phase4_rows()
    d.to_csv(OUT / "break_even_observations.csv", index=False)
    grid = np.linspace(30, 600, 286)
    curves = []
    thresholds = []
    for k in [1, 2, 4]:
        f = d[d.k == k].reset_index(drop=True)
        boots = np.empty((2000, len(grid)))
        for i in range(2000):
            sample = f.iloc[RNG.integers(0, len(f), len(f))]
            boots[i] = predict_grid(sample, grid)
        center = predict_grid(f, grid)
        low, high = np.quantile(boots, [0.025, 0.975], axis=0)
        for x, c, lo, hi in zip(grid, center, low, high):
            curves.append({"k": k, "target_latency_ms": x, "speedup": c,
                           "ci95_low": lo, "ci95_high": hi})
        crossing = np.where(center >= 1)[0]
        threshold = float(grid[crossing[0]]) if len(crossing) else np.nan
        boot_thresholds = []
        for row in boots:
            idx = np.where(row >= 1)[0]
            if len(idx): boot_thresholds.append(grid[idx[0]])
        thresholds.append({"k": k, "break_even_ms": threshold,
                           "ci95_low": np.quantile(boot_thresholds, .025) if boot_thresholds else np.nan,
                           "ci95_high": np.quantile(boot_thresholds, .975) if boot_thresholds else np.nan,
                           "bootstrap_crossing_fraction": len(boot_thresholds) / len(boots)})
    curves = pd.DataFrame(curves)
    thresholds = pd.DataFrame(thresholds)
    curves.to_csv(OUT / "break_even_curve.csv", index=False)
    thresholds.to_csv(OUT / "break_even_thresholds.csv", index=False)

    stats = d.groupby("k").agg(speedup=("speedup", gmean), acceptance=("acceptance", "mean")).reset_index()
    fig, ax = plt.subplots(figsize=(7, 4.4)); ax2 = ax.twinx()
    ax.plot(stats.k, stats.speedup, "o-", color="#1769aa", label="Geomean speedup")
    ax2.plot(stats.k, stats.acceptance * 100, "s--", color="#d1495b", label="Acceptance")
    ax.axhline(1, color="black", lw=1, ls=":"); ax.set(xticks=KS, xlabel="Speculation depth k", ylabel="Speedup vs RTX baseline")
    ax2.set_ylabel("Draft acceptance (%)"); ax.set_title("Qwen3 0.6B CPU → 8B RTX, 60 questions")
    ax.legend(loc="upper right"); ax2.legend(loc="center right"); save(fig, "figure1_pilot_speedup_vs_k")

    decomp = pd.DataFrame([
        ["RTX baseline", 0, 57.75, 0], ["CPU→RTX custom", 17.45, 61.82, 5.95],
        ["RTX→RTX custom", 23.66, 71.07, 6.19], ["RTX→RTX native", 0, 56.01, 0],
    ], columns=["config", "draft", "verify_or_decode", "residual"])
    fig, ax = plt.subplots(figsize=(8, 4.5)); bottom = np.zeros(len(decomp))
    for col, color in zip(["draft", "verify_or_decode", "residual"], ["#59a14f", "#4e79a7", "#f28e2b"]):
        ax.bar(decomp.config, decomp[col], bottom=bottom, label=col.replace("_", " "), color=color); bottom += decomp[col]
    ax.set_ylabel("Aggregate time (s), 12Q"); ax.set_title("Root-cause time decomposition"); ax.tick_params(axis="x", rotation=15); ax.legend(); save(fig, "figure2_root_cause_decomposition")

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for k, color in zip([1, 2, 4], ["#1769aa", "#59a14f", "#e15759"]):
        c = curves[curves.k == k]; ax.plot(c.target_latency_ms, c.speedup, label=f"CPU draft k={k}", color=color)
        ax.fill_between(c.target_latency_ms, c.ci95_low, c.ci95_high, color=color, alpha=.12)
    ax.axhline(1, color="black", ls=":"); ax.axvline(60.16, color="#777", ls="--"); ax.axvline(88.69, color="#999", ls="--")
    ax.text(60.16, .12, "8B", rotation=90, va="bottom"); ax.text(88.69, .12, "14B", rotation=90, va="bottom")
    ax.set(xlabel="Target autoregressive latency (ms/token)", ylabel="Predicted speculative speedup", ylim=(0, 1.35), title="Empirical break-even model (95% question bootstrap)")
    ax.legend(); save(fig, "figure6_empirical_break_even_curve")

    cross = pd.DataFrame({"target_latency_ms": [60.16, 88.69], "observed_speedup": [.733, .718], "label": ["8B", "14B"]})
    fig, ax = plt.subplots(figsize=(6.5, 4.2)); ax.plot(cross.target_latency_ms, cross.observed_speedup, "o-", color="#7b2cbf")
    ax.axhline(1, color="black", ls=":");
    for _, r in cross.iterrows(): ax.annotate(r.label, (r.target_latency_ms, r.observed_speedup), xytext=(5, 7), textcoords="offset points")
    ax.set(xlabel="Target token latency (ms/token)", ylabel="Observed CPU-assisted speedup", title="8B → 14B crossover did not reach break-even")
    save(fig, "figure3_target_size_crossover")

    vram = pd.DataFrame({"config": ["8B target", "8B target+draft", "14B target", "14B assisted"],
                         "cuda_gib": [5.905, 9.333, 9.678, 9.884], "nvml_gb": [6.694, 10.558, 10.646, 10.734]})
    fig, ax = plt.subplots(figsize=(7.5, 4.5)); x=np.arange(len(vram)); w=.36
    ax.bar(x-w/2, vram.cuda_gib, w, label="CUDA peak (GiB)"); ax.bar(x+w/2, vram.nvml_gb, w, label="NVML peak (decimal GB)")
    ax.axhline(12, color="#d1495b", ls="--", label="12 GB physical class (reference)")
    ax.set(xticks=x, xticklabels=vram.config, ylabel="Reported memory (different units)", title="VRAM capacity boundary—metrics shown separately")
    ax.tick_params(axis="x", rotation=15); ax.legend(); save(fig, "figure4_vram_capacity_boundary")

    report = {"method": "Question-level empirical scaling; verify time scales with target latency; draft/residual/acceptance frozen; 2000 bootstrap resamples.",
              "thresholds": thresholds.replace({np.nan: None}).to_dict("records")}
    (OUT / "break_even_summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))

if __name__ == "__main__": main()
