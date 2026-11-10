"""CPU-only protocol arithmetic and symbolic schedules. Never executes experiments.

All root/operand labels are slots, not measured data or admitted native jobs.
The admission check is a necessary structural check, not an authority verifier.
"""
import argparse
import itertools
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ARMS = ("G", "B", "C")
PERMS = tuple(itertools.permutations(ARMS))
PANEL_ORDERS = (
    ("GBC", "BCG", "CGB", "GCB"),
    ("BCG", "CGB", "GBC", "CBG"),
    ("CGB", "GBC", "BCG", "BGC"),
    ("GCB", "CBG", "BGC", "GBC"),
    ("CBG", "BGC", "GCB", "BCG"),
    ("BGC", "GCB", "CBG", "CGB"),
)
CELL_ROWS = ((0, 1, 3, 2), (1, 2, 0, 3), (2, 3, 1, 0), (3, 0, 2, 1))
REPLICA_ROOTS = (0, 1, 2, 6, 7, 8)


def need(condition, message):
    if not condition:
        raise ValueError(message)


def paired_worker(worker_id, arm, slot, round_id):
    return {
        "id": worker_id, "arm": arm, "slot": slot, "round": round_id,
        "operations": [
            {"id": worker_id + ":" + role, "role": role, "slot": slot, "arm": arm}
            for role in ("warm", "measured")
        ],
    }


def plan():
    diagnostic = []
    for repeat in range(3):
        for cell in range(4):
            orientation = ARMS if cell % 2 == 0 else ("G", "C", "B")
            order = orientation[repeat:] + orientation[:repeat]
            for arm in order:
                diagnostic.append(paired_worker(f"diag-c{cell}-r{repeat}-{arm}", arm, cell, repeat))
    panel = []
    for rnd in range(4):
        root_order = list(range(12))
        root_order = root_order[3 * rnd:] + root_order[:3 * rnd]
        for root in root_order:
            for arm in PANEL_ORDERS[root % 6][rnd]:
                w = paired_worker(f"panel-root{root:02d}-r{rnd}-{arm}", arm, root, rnd)
                w["domain"] = "code" if root < 6 else "math"
                panel.append(w)
    replica = []
    for rnd in range(3):
        root_order = list(range(6))
        root_order = root_order[2 * rnd:] + root_order[:2 * rnd]
        for slot in root_order:
            for arm in PANEL_ORDERS[slot][rnd]:
                w = paired_worker(f"replica-root{slot:02d}-r{rnd}-{arm}", arm, slot, rnd)
                w["primary_root_slot"] = REPLICA_ROOTS[slot]
                w["domain"] = "code" if slot < 3 else "math"
                replica.append(w)
    graph_probe = []
    for fixture in ("q1_decode", "q32_prefill"):
        for arm in ARMS:
            worker_id = f"graph-{fixture}-{arm}"
            graph_probe.append({"id": worker_id, "arm": arm, "fixture": fixture,
                                "operations": [{"id": f"{worker_id}:{kind}", "kind": kind}
                                               for kind in ("capture", "replay", "changed_signature")]})
    b2 = []
    cells = [(core, pos) for core in ("loop4", "packed") for pos in (248, 252)]
    for rnd, row in enumerate(CELL_ROWS):
        for cell in row:
            core, pos = cells[cell]
            warm = "ABBA" if rnd % 2 == 0 else "BAAB"
            measured = "ABBA" if rnd < 2 else "BAAB"
            worker_id = f"b2-r{rnd}-c{cell}"
            ops = []
            for role, order in (("warm", warm), ("measured", measured)):
                for ordinal, path in enumerate(order):
                    ops.append({"id": f"{worker_id}:{role}:{ordinal}", "role": role,
                                "path": path, "position": pos, "tokens": 8,
                                "reserved_rows": pos + 8})
            b2.append({"id": worker_id, "cell": cell, "core": core,
                       "position": pos, "round": rnd, "operations": ops})
    return {"status": "SYMBOLIC_DESIGN_ONLY_NOT_NATIVE_JOBS", "q32_diagnostic": diagnostic,
            "q32_panel": panel, "b2": b2, "q32_replica": replica, "graph_probe": graph_probe,
            "optional_status": {"second_device": "DEFER_NOT_AUTHORIZED",
                                "graph_probe": "NOT_ACTIVATED_NOT_AUTHORIZED"}}


def matrices(workers):
    blocks = defaultdict(list)
    for w in workers:
        blocks[(w["round"], w["slot"])].append(w["arm"])
    positions, adjacency, permutations = Counter(), Counter(), Counter()
    for arms in blocks.values():
        need(tuple(sorted(arms)) == tuple(sorted(ARMS)), "Invalid three-arm block")
        permutations["".join(arms)] += 1
        positions.update(f"{arm}@{position}" for position, arm in enumerate(arms))
        adjacency.update(f"{a}>{b}" for a, b in zip(arms, arms[1:]))
    return {"positions": dict(sorted(positions.items())),
            "within_block_directed_adjacency": dict(sorted(adjacency.items())),
            "permutations": dict(sorted(permutations.items()))}


def validate(p):
    ids = []
    for field, expected_workers, expected_requests in (
        ("q32_diagnostic", 36, 72), ("q32_panel", 144, 288), ("b2", 16, 128),
        ("q32_replica", 54, 108)
    ):
        workers = p[field]
        need(len(workers) == expected_workers, field + " worker count")
        ops = [op for w in workers for op in w["operations"]]
        need(len(ops) == expected_requests, field + " request count")
        need(Counter(op["role"] for op in ops) == {"warm": expected_requests // 2,
                                                    "measured": expected_requests // 2}, "Roles")
        ids.extend(w["id"] for w in workers)
        ids.extend(op["id"] for op in ops)
        if field != "b2":
            for w in workers:
                need([o["role"] for o in w["operations"]] == ["warm", "measured"], "Warm adjacency")
                need(all(o["slot"] == w["slot"] and o["arm"] == w["arm"]
                         for o in w["operations"]), "Warm and measured inputs differ")
    need(len(p["graph_probe"]) == 6, "Graph probe worker count")
    graph_cells = Counter()
    for w in p["graph_probe"]:
        graph_cells[(w["fixture"], w["arm"])] += 1
        need([o["kind"] for o in w["operations"]] == ["capture", "replay", "changed_signature"],
             "Graph capture/replay/invalidation sequence")
        ids.append(w["id"])
        ids.extend(o["id"] for o in w["operations"])
    need(graph_cells == Counter({(f, a): 1 for f in ("q1_decode", "q32_prefill") for a in ARMS}),
         "All graph probe arms and fixtures required")
    need(len(ids) == len(set(ids)), "Duplicate slot ID")
    need(p["optional_status"] == {"second_device": "DEFER_NOT_AUTHORIZED",
                                  "graph_probe": "NOT_ACTIVATED_NOT_AUTHORIZED"},
         "Symbolic optional designs never activate experiments")
    diag = matrices(p["q32_diagnostic"])
    need(set(diag["positions"].values()) == {4}, "Diagnostic position balance")
    need(len(diag["within_block_directed_adjacency"]) == 6 and
         set(diag["within_block_directed_adjacency"].values()) == {4}, "Diagnostic adjacency balance")
    for cell in range(4):
        m = matrices([w for w in p["q32_diagnostic"] if w["slot"] == cell])
        need(len(m["positions"]) == 9 and set(m["positions"].values()) == {1}, "Cell positions")
    panel = matrices(p["q32_panel"])
    need(len(panel["permutations"]) == 6 and set(panel["permutations"].values()) == {8}, "Panel permutations")
    need(len(panel["positions"]) == 9 and set(panel["positions"].values()) == {16}, "Panel position balance")
    need(len(panel["within_block_directed_adjacency"]) == 6 and
         set(panel["within_block_directed_adjacency"].values()) == {16}, "Panel adjacency balance")
    per_root = {}
    for root in range(12):
        ww = [w for w in p["q32_panel"] if w["slot"] == root]
        need(Counter(w["arm"] for w in ww) == {a: 4 for a in ARMS}, "Root replication")
        m = matrices(ww)
        need(len(m["positions"]) == 9 and set(m["positions"].values()) <= {1, 2}, "Root positions")
        per_root[str(root)] = m
    for domain in ("code", "math"):
        m = matrices([w for w in p["q32_panel"] if w["domain"] == domain])
        need(set(m["permutations"].values()) == {4}, "Domain permutations")
        need(set(m["positions"].values()) == {8}, "Domain positions")
    replica = matrices(p["q32_replica"])
    need(len(replica["permutations"]) == 6 and set(replica["permutations"].values()) == {3},
         "Replica permutations")
    need(len(replica["positions"]) == 9 and set(replica["positions"].values()) == {6}, "Replica positions")
    need(len(replica["within_block_directed_adjacency"]) == 6 and
         set(replica["within_block_directed_adjacency"].values()) == {6}, "Replica adjacency")
    replica_per_root = {}
    for slot in range(6):
        ww = [w for w in p["q32_replica"] if w["slot"] == slot]
        need(len(ww) == 9 and all(w["primary_root_slot"] == REPLICA_ROOTS[slot] for w in ww),
             "Replica fixed main-root subset")
        need(all(w["domain"] == ("code" if slot < 3 else "math") for w in ww), "Replica domain")
        m = matrices(ww)
        need(len(m["positions"]) == 9 and set(m["positions"].values()) == {1}, "Replica root positions")
        replica_per_root[str(slot)] = m
    for cell in range(4):
        ww = [w for w in p["b2"] if w["cell"] == cell]
        need(len(ww) == 4, "B2 cell process count")
        combos = Counter()
        for w in ww:
            ops = w["operations"]
            need([o["role"] for o in ops] == ["warm"] * 4 + ["measured"] * 4, "B2 role order")
            warm = "".join(o["path"] for o in ops[:4])
            measured = "".join(o["path"] for o in ops[4:])
            need(warm in ("ABBA", "BAAB") and measured in ("ABBA", "BAAB"), "B2 order")
            combos[(warm, measured)] += 1
            need(all(o["position"] == w["position"] and o["tokens"] == 8 and
                     o["reserved_rows"] == w["position"] + 8 for o in ops), "B2 row/restore contract")
        need(len(combos) == 4 and set(combos.values()) == {1}, "B2 2x2 order balance")
    b2_positions, b2_edges = Counter(), Counter()
    for rnd in range(4):
        row = [w["cell"] for w in p["b2"] if w["round"] == rnd]
        need(tuple(row) == CELL_ROWS[rnd], "B2 registered cell row")
        b2_positions.update((c, i) for i, c in enumerate(row))
        b2_edges.update(zip(row, row[1:]))
    need(len(b2_positions) == 16 and set(b2_positions.values()) == {1}, "B2 cell positions")
    need(len(b2_edges) == 12 and set(b2_edges.values()) == {1}, "B2 cell adjacency")
    rows = sum(o["reserved_rows"] for w in p["b2"] for o in w["operations"])
    need(rows == 33024, "B2 reserved rows")
    need(1909 + 128 == 2037 and 2048 - 2037 == 11, "B2 request arithmetic")
    need(3053954 + rows == 3086978, "B2 row arithmetic")
    need(640 - 514 == 126 and 288 > 126, "Old Q32 envelope cannot fit new panel")
    need(256 - 72 - 16 == 168 and 384 - 288 - 60 - 16 == 20, "Proposed phase reserves")
    need(108 + 12 + 18 == 138 and 192 - 108 - 12 - 18 - 16 == 38, "Replica qualification is extra")
    need(514 + 256 + 384 + 192 == 1346, "No second-device historical reset")
    return {"passed": True, "gpu_execution": "NOT_RUN", "numeric_qualification": "NOT_RUN",
            "request_counts": {"q32_diagnostic": 72, "q32_panel": 288, "b2": 128,
                               "optional_graph_candidates_only": 18, "optional_second_device_panel": 108},
            "q32_diagnostic_balance": diag, "q32_panel_balance": panel,
            "q32_per_root_balance": per_root,
            "q32_replica_balance": replica, "q32_replica_per_root_balance": replica_per_root,
            "optional_status": p["optional_status"],
            "limitations": ["Only within-block adjacency is checked; cross-block carryover is not balanced",
                            "Root ordinals rotate but do not cover all twelve positions",
                            "Symbolic slots do not bind actual inputs or admit execution",
                            "Graph probe counts exclude its R/gold/full qualification costs",
                            "Second-device panel needs at least 30 more R/bridge operations plus all other gates",
                            "Second-device roots repeat primary roots and cannot increase independent N"],
            "b2_reserved_rows": rows, "b2_post_requests": 2037, "b2_post_rows": 3086978}


def check_admission(data):
    """Necessary shape checks only. Evidence bytes/authorization require independent review."""
    need(data["status"] == "ADMITTED" and data["gpu_execution_authorized"] is True, "Not admitted or authorized")
    for field in ("authorization_reference", "allocation_reference"):
        need(isinstance(data[field], str) and bool(data[field].strip()), "Missing " + field)
    for field in ("remote_readback_receipt_sha256", "exact_job_manifest_sha256",
                  "qualification_manifest_sha256", "artifact_manifest_sha256", "oracle_freeze_sha256",
                  "actual_roots_or_operands_sha256", "analysis_source_sha256"):
        need(isinstance(data[field], str) and bool(re.fullmatch(r"[0-9a-f]{64}", data[field])), "Missing " + field)
    need(isinstance(data["source_commit"], str) and bool(re.fullmatch(r"[0-9a-f]{40}", data["source_commit"])), "Source SHA")
    dates = []
    for field in ("allocation_start_utc", "last_new_worker_utc", "delivery_deadline_utc"):
        need(isinstance(data[field], str), "Missing " + field)
        dt = datetime.fromisoformat(data[field].replace("Z", "+00:00"))
        need(dt.utcoffset() is not None and dt.utcoffset().total_seconds() == 0, "UTC required")
        dates.append(dt)
    need(dates[0] < dates[1] < dates[2], "Invalid date order")
    need(all(data[k] is True for k in ("guards_passed", "qualification_passed",
                                      "resource_and_whole_panel_cost_passed")), "Unpassed gates")
    need(data["phase"] in ("Q32_S2", "Q32_S3", "B2", "Q32_REPLICA"),
         "Structural checker only covers post-qualification timing")
    history = data["historical_8b" if data["phase"] == "B2" else "historical_q32"]
    need(isinstance(history["ledger_prefix_sha256"], str) and
         bool(re.fullmatch(r"[0-9a-f]{64}", history["ledger_prefix_sha256"])), "Missing ledger binding")
    for k in ("prospective_request_ceiling", "prospective_row_ceiling", "exact_incremental_requests",
              "exact_incremental_reserved_rows", "failure_closure_reserve_requests"):
        need(type(data[k]) is int and data[k] >= 0, "Missing integer " + k)
    minimum = {"Q32_S2": 72, "Q32_S3": 288, "B2": 128, "Q32_REPLICA": 108}[data["phase"]]
    need(data["exact_incremental_requests"] >= minimum, "Incomplete panel reservation")
    min_reserve = 8 if data["phase"] == "B2" else 16
    need(data["failure_closure_reserve_requests"] >= min_reserve, "Failure reserve")
    need(history["requests"] + data["exact_incremental_requests"] + data["failure_closure_reserve_requests"]
         <= data["prospective_request_ceiling"], "Request ceiling exceeded")
    need(history["reserved_rows"] + data["exact_incremental_reserved_rows"]
         <= data["prospective_row_ceiling"], "Row ceiling exceeded")
    if data["phase"] == "B2":
        need(data["prospective_request_ceiling"] == 2048 and data["prospective_row_ceiling"] == 8000000,
             "B2 may not silently raise old envelope")
        need(data["exact_incremental_reserved_rows"] >= 33024, "B2 row undercount")
    else:
        need(data["graph_assessment_mode"] in ("off_only", "assess_common_on"), "Graph mode")
        need(data["selected_graph_policy"] in ("off", "on"), "Common graph policy required")
        need(isinstance(data["graph_policy_decision_sha256"], str) and
             bool(re.fullmatch(r"[0-9a-f]{64}", data["graph_policy_decision_sha256"])), "Graph decision binding")
        need(data["graph_assessment_mode"] != "off_only" or data["selected_graph_policy"] == "off",
             "Off-only registration cannot silently enable graphs")
    if data["phase"] == "Q32_REPLICA":
        need(all(data[k] is True for k in ("second_device_separately_authorized",
                                          "replica_frozen_before_primary_results", "quiet_windows_nonoverlapping")),
             "Second-device separate activation/freeze/quiet windows missing")
        for field in ("own_device_R_sha256", "primary_device_binding_sha256", "replica_device_binding_sha256"):
            need(isinstance(data[field], str) and bool(re.fullmatch(r"[0-9a-f]{64}", data[field])), field)
        need(data["primary_device_binding_sha256"] != data["replica_device_binding_sha256"],
             "Second physical device must be distinct")
    return {"structural_checks_passed": True, "execution_admitted_by_this_script": False,
            "requires": "Independent verification of authority, current time, files, actual ledger, jobs and qualification"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--emit-plan", type=Path)
    group.add_argument("--check-admission", type=Path)
    args = parser.parse_args()
    if args.check_admission:
        result = check_admission(json.loads(args.check_admission.read_text()))
    else:
        p = plan()
        result = validate(p)
        if args.emit_plan:
            with args.emit_plan.open("x") as f:
                json.dump({"plan": p, "validation": result}, f, indent=2, sort_keys=True)
                f.write("\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
