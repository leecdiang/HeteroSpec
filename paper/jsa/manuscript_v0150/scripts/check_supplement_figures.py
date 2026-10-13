#!/usr/bin/env python3
"""Independently check supplementary plotted coordinates against reported medians.

This is a CPU-only report/figure audit. It does not execute the figure generator,
load native timing records, restore CAS archives, or run a model. The parser checks
literal PGFPlots/TikZ coordinates as well as their task labels, rather than trusting
metadata-only claims about the figures.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "provenance/SUPPLEMENT_FIGURE_CHECKS_V0152.json"
FAMILIES = ("Qwen3", "SmolLM2", "Llama")
ALL_PAIRS = {
    "M_PQ/M_QB", "C_PQ/C_QB", "M_GS/M_QB", "C_GS/C_QB",
    "M_QB/C_QB", "R/M_QB", "R/C_QB",
}
TASK_PAIRS = ("C_PQ/C_QB", "M_QB/C_QB")
SESSION_PAIRS = ("M_PQ/M_QB", "C_PQ/C_QB")
NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
SERIES = re.compile(
    r"^% series: (?P<kind>\w+) family=(?P<family>\S+) "
    r"comparison=(?P<comparison>\S+)(?: session=(?P<session>\d+))?[^\S\n]*\n"
    r"\s*\\addplot(?:\[[\s\S]*?\])?\s*coordinates\s*\{(?P<body>[\s\S]*?)\};",
    re.MULTILINE,
)
COORD = re.compile(
    rf"\(\s*(?P<x>{NUMBER})\s*,\s*(?P<y>{NUMBER})\s*\)"
    r"[^\S\n]*% task: (?P<task>\S+)"
)
ANY_COORD = re.compile(rf"\(\s*{NUMBER}\s*,\s*{NUMBER}\s*\)")
SEGMENT = re.compile(
    r"^% session-pair: family=(?P<family>\S+) comparison=(?P<comparison>\S+) "
    r"task=(?P<task>\S+)[^\S\n]*\n"
    r"\s*\\draw(?:\[[^\]]*\])?\s*"
    rf"\(axis cs:\s*(?P<first>{NUMBER})\s*,\s*(?P<y1>{NUMBER})\s*\)\s*--\s*"
    rf"\(axis cs:\s*(?P<second>{NUMBER})\s*,\s*(?P<y2>{NUMBER})\s*\)\s*;",
    re.MULTILINE,
)


def side(value: float) -> int:
    return (value > 1.0) - (value < 1.0)


def session_direction(first: float, second: float) -> str:
    return {
        (1, 1): "QB_faster_both_sessions",
        (-1, -1): "PQ_faster_both_sessions",
        (-1, 1): "PQ_first_QB_second",
        (1, -1): "QB_first_PQ_second",
    }.get((side(first), side(second)), "includes_exact_parity")


def main() -> None:
    tests: list[dict] = []
    result: dict = {
        "version": "0.15.2",
        "status": "RUNNING",
        "scope": (
            "Independently recomputes task/session ratios from the pinned report's "
            "arm median times and parses literal coordinates in two supplementary "
            "figures. This is not a native/raw/CAS audit or independent GPU replication."
        ),
        "new_GPU_runs": 0,
        "raw_archives_reaudited": False,
        "tests": tests,
    }

    def check(name: str, condition: bool, details=None) -> None:
        item = {"check": name, "pass": bool(condition)}
        if details is not None:
            item["details"] = details
        tests.append(item)

    def require(name: str, condition: bool, details=None) -> None:
        check(name, condition, details)
        if not condition:
            raise ValueError(name)

    try:
        paths = {
            "report_extract": ROOT / "data/rtx_repair_report_extract.json",
            "regression_panel": ROOT / "data/task_regressions.json",
            "task_cost": ROOT / "figures/task_cost.tex",
            "session_tasks": ROOT / "figures/session_tasks.tex",
            "figure_text": ROOT / "supplement/04_cost.tex",
        }
        for name, path in paths.items():
            require(name + "_exists", path.is_file())
        result["input_sha256"] = {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths.values()
        }
        report = json.loads(paths["report_extract"].read_text())
        ledger = json.loads(paths["regression_panel"].read_text())
        panel = ledger["panel"]
        require("twelve_unique_tasks", len(panel) == len(set(panel)) == 12)
        check("two_balanced_task_domains", sum(t.startswith("MBPP/") for t in panel) == 6
              and sum(t.startswith("GSM8K/test/") for t in panel) == 6)
        check("fixed_report_blob", report["source_blob_sha"] == "4d77a2743a8521fb9be130bbc3061c87902a4cd4")
        check("fixed_report_commit", "3235d44c26edd92db33e574094c26af8e29d2452" in report["source_url"])
        check("fixed_report_sha256", report["source_sha256"] == "f41bb797802b552fd16656f21a64dcd72d6565e26583830fe344f6a15492dfe2")
        result["report_source"] = {k: report[k] for k in ("source_url", "source_blob_sha", "source_sha256")}
        comparison_rows = report["comparisons"]
        expected_keys = {(f, p) for f in FAMILIES for p in ALL_PAIRS}
        require("all_twenty_one_comparisons", len(comparison_rows) == 21
                and {(r["family"], r["pair"]) for r in comparison_rows} == expected_keys)

        # Recompute from timing medians; source ratios are verification targets only.
        computed: dict[tuple, tuple[float, float, float]] = {}
        shared_arm_medians: dict[tuple, tuple] = {}
        for row in comparison_rows:
            family, pair = row["family"], row["pair"]
            tag = family + "/" + pair
            effects = row["task_effects"]
            require(tag + "/complete_qualified_panel", row["qualified"] is True
                    and len(effects) == 12 and {e["task"] for e in effects} == set(panel))
            left_arm, right_arm = pair.split("/")
            session_values = [[], []]
            negative_tasks = set()
            for effect in effects:
                task = effect["task"]
                tasktag = tag + "/" + task
                left = effect["left_session_median_ms"]
                right = effect["right_session_median_ms"]
                require(tasktag + "/two_positive_medians", len(left) == len(right) == 2
                        and all(math.isfinite(v) and v > 0 for v in left + right))
                for arm, values in ((left_arm, left), (right_arm, right)):
                    key = family, task, arm
                    if key in shared_arm_medians:
                        check(tasktag + "/shared_" + arm + "_medians_exact", shared_arm_medians[key] == tuple(values))
                    else:
                        shared_arm_medians[key] = tuple(values)
                first, second = left[0] / right[0], left[1] / right[1]
                aggregate = math.exp((math.log(first) + math.log(second)) / 2)
                computed[family, pair, task] = first, second, aggregate
                check(tasktag + "/source_session_ratios", len(effect["session_ratios"]) == 2
                      and math.isclose(first, effect["session_ratios"][0], rel_tol=1e-12)
                      and math.isclose(second, effect["session_ratios"][1], rel_tol=1e-12))
                check(tasktag + "/source_task_ratio", math.isclose(aggregate, effect["ratio"], rel_tol=1e-12))
                session_values[0].append(first)
                session_values[1].append(second)
                if aggregate < 1:
                    negative_tasks.add(task)
            session_aggregates = [math.exp(sum(map(math.log, values)) / 12) for values in session_values]
            family_aggregate = math.sqrt(session_aggregates[0] * session_aggregates[1])
            check(tag + "/source_family_session_aggregates", all(math.isclose(a, b, rel_tol=1e-12)
                  for a, b in zip(session_aggregates, row["session_ratios"])))
            check(tag + "/source_family_aggregate", math.isclose(family_aggregate, row["cost_ratio"], rel_tol=1e-12))
            check(tag + "/regression_names", negative_tasks == set(ledger["regressions"][family][pair]))
        check("all_252_shared_arm_median_pairs", len(shared_arm_medians) == 3 * 12 * 7)
        check("all_252_task_comparison_ratios", len(computed) == 3 * 12 * 7)

        task_source = paths["task_cost"].read_text()
        session_source = paths["session_tasks"].read_text()
        plotted: dict[str, dict[tuple, tuple]] = {}
        for kind, source, expected_series, offset in (
            ("task_cost", task_source, {(f, p, None) for f in FAMILIES for p in TASK_PAIRS}, True),
            ("session_tasks", session_source, {(f, p, str(s)) for f in FAMILIES for p in SESSION_PAIRS for s in (1, 2)}, False),
        ):
            series = list(SERIES.finditer(source))
            require(kind + "/all_series_parse", len(series) == len(re.findall(r"^% series:", source, re.MULTILINE)))
            series_keys = [(m["family"], m["comparison"], m["session"]) for m in series]
            require(kind + "/complete_unique_series", len(series_keys) == len(expected_series)
                    and set(series_keys) == expected_series)
            values = {}
            for match in series:
                family, pair, session = match["family"], match["comparison"], match["session"]
                label = kind + "/" + family + "/" + pair + "/" + str(session)
                check(label + "/correct_kind", match["kind"] == kind)
                coords = list(COORD.finditer(match["body"]))
                require(label + "/complete_task_coordinates", len(coords) == 12
                        and len(ANY_COORD.findall(match["body"])) == 12
                        and [m["task"] for m in coords] == panel)
                for coordinate in coords:
                    task = coordinate["task"]
                    x, y = float(coordinate["x"]), float(coordinate["y"])
                    expected_x = computed[family, pair, task][2 if session is None else int(session) - 1]
                    expected_y = 12 - panel.index(task)
                    if offset:
                        expected_y += 0.13 if pair == "C_PQ/C_QB" else -0.13
                    else:
                        expected_y += 0.15 if session == "1" else -0.15
                    point_tag = label + "/" + task
                    check(point_tag + "/literal_x_from_medians", math.isclose(x, expected_x, rel_tol=0, abs_tol=5.1e-13))
                    check(point_tag + "/task_y_alignment", math.isclose(y, expected_y, rel_tol=0, abs_tol=1e-9))
                    check(point_tag + "/parity_direction_preserved", side(x) == side(expected_x))
                    values[family, pair, session, task] = x, y
            plotted[kind] = values
        check("task_figure_72_literal_points", len(plotted["task_cost"]) == 36 * 2)
        check("session_figure_144_literal_points", len(plotted["session_tasks"]) == 72 * 2)
        for kind, source, axes in (("task_cost", task_source, 3), ("session_tasks", session_source, 6)):
            bounds = {}
            for bound in ("xmin", "xmax", "ymin", "ymax"):
                literals = re.findall(rf"\b{bound}\s*=\s*({NUMBER})", source)
                require(kind + "/single_shared_" + bound, len(literals) == 1)
                bounds[bound] = float(literals[0])
            check(kind + "/all_markers_inside_shared_axes", all(
                bounds["xmin"] < x < bounds["xmax"] and bounds["ymin"] < y < bounds["ymax"]
                for x, y in plotted[kind].values()))
            check(kind + "/expected_panel_count", source.count(r"\begin{axis}") == axes)
            check(kind + "/parity_inside_axis", bounds["xmin"] < 1 < bounds["xmax"])
        task_axes = re.findall(r"\\begin\{axis\}\[([^\n]+)", task_source)
        check("task_figure_each_axis_explicitly_logarithmic", len(task_axes) == 3 and all(re.search(r"\bxmode\s*=\s*log\b", options) for options in task_axes))
        check("session_figure_linear_axis", not re.search(r"\bxmode\s*=\s*log\b", session_source))

        segments = list(SEGMENT.finditer(session_source))
        require("session_figure_all_segments_parse", len(segments)
                == len(re.findall(r"^% session-pair:", session_source, re.MULTILINE)) == 72)
        segment_keys = [(m["family"], m["comparison"], m["task"]) for m in segments]
        require("session_figure_72_unique_task_pairs", len(set(segment_keys)) == 72
                and set(segment_keys) == {(f, p, t) for f in FAMILIES for p in SESSION_PAIRS for t in panel})
        for segment in segments:
            family, pair, task = segment["family"], segment["comparison"], segment["task"]
            tag = "session_segment/" + family + "/" + pair + "/" + task
            first, second, _ = computed[family, pair, task]
            x1, x2 = float(segment["first"]), float(segment["second"])
            y1, y2 = float(segment["y1"]), float(segment["y2"])
            check(tag + "/both_endpoints_from_medians", abs(first - x1) <= 5.1e-13
                  and abs(second - x2) <= 5.1e-13)
            check(tag + "/connects_actual_markers", (x1, y1) == plotted["session_tasks"][family, pair, "1", task]
                  and (x2, y2) == plotted["session_tasks"][family, pair, "2", task])
            check(tag + "/direction_and_crossing_preserved", session_direction(first, second) == session_direction(x1, x2))

        counts = {}
        for family in FAMILIES:
            for pair in SESSION_PAIRS:
                counts[family + "/" + pair] = dict(Counter(
                    session_direction(*computed[family, pair, task][:2]) for task in panel
                ))
        expected_counts = {
            "Qwen3/M_PQ/M_QB": {"PQ_first_QB_second": 11, "QB_faster_both_sessions": 1},
            "Qwen3/C_PQ/C_QB": {"QB_faster_both_sessions": 12},
            "SmolLM2/M_PQ/M_QB": {"QB_faster_both_sessions": 12},
            "SmolLM2/C_PQ/C_QB": {"QB_faster_both_sessions": 12},
            "Llama/M_PQ/M_QB": {"PQ_first_QB_second": 5, "QB_faster_both_sessions": 7},
            "Llama/C_PQ/C_QB": {"QB_faster_both_sessions": 8, "PQ_first_QB_second": 2, "QB_first_PQ_second": 2},
        }
        check("all_six_task_direction_counts", counts == expected_counts)
        result["task_session_direction_counts"] = counts
        near_parity = computed["Llama", "C_PQ/C_QB", "GSM8K/test/141"][2]
        near_plotted = plotted["task_cost"]["Llama", "C_PQ/C_QB", None, "GSM8K/test/141"][0]
        check("Llama_GSM141_unrounded_regression", near_parity < 1 and near_plotted < 1
              and format(near_parity, ".6f") == "0.999919")
        caption_path = paths["figure_text"]
        visible_tex = re.sub(r"(?<!\\)%[^\n]*", "", task_source + "\n" + caption_path.read_text())
        check("Llama_GSM141_visible_precision_disclosure", bool(re.search(r"0\.999919(?:\d*)|0\.99992(?!\d)", visible_tex)))
        result["near_parity_task"] = {
            "family": "Llama", "task": "GSM8K/test/141", "comparison": "C_PQ/C_QB",
            "recomputed_ratio": near_parity, "plotted_ratio": near_plotted,
            "six_decimal_display": format(near_parity, ".6f"), "QB_is_slower": True,
        }
        result["figure_counts"] = {"family_task_units": 36, "task_ratio_points": 72,
                                   "session_pairs": 72, "session_points": 144}
        result["scientific_boundaries"] = [
            "The panel has 12 exposed tasks evaluated in each of three families; 36 family-task units are not 36 independent tasks.",
            "Each plotted session ratio uses reported four-repeat arm medians; adjacent sessions are not independent dates.",
            "Per-task overall ratios give the two sessions equal log weights; family aggregates also give the 12 tasks equal log weights.",
            "C_PQ/C_QB and M_QB/C_QB share a C_QB denominator; juxtaposition does not establish a causal or statistical association.",
            "The figures report qualified inclusive request-time ratios, not isolated GPU/kernel costs, uncertainty intervals or predictive effects.",
            "Values below one are retained using full precision, including Llama GSM8K141 at 0.9999190595925469.",
        ]
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    result["checks"] = len(tests)
    result["failed_checks"] = [t["check"] for t in tests if not t["pass"]]
    result["status"] = "PASS_SUPPLEMENT_FIGURE_COORDINATES" if not result["failed_checks"] and "error" not in result else "FAIL_SUPPLEMENT_FIGURE_COORDINATES"
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"{result['status']}: {len(tests)} checks; {len(result['failed_checks'])} failures.")
    if result["status"].startswith("FAIL"):
        print(result.get("error", ""))
        for failure in result["failed_checks"]:
            print(failure)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
