"""CPU-only design: paired factors, same-QB controls, balanced acquisition orders.

No GPU/runtime imports and no dependence on old latency outcomes. A generated
plan describes tasks; it does not resolve tensor bytes or authorize old runs.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import random

PARENT = "c6eb66368bc876332afe82f9df5ea51fe0b4b5ec"
ARMS = ("PQ", "QB_A", "QH_C", "QB_B")
LAYOUT = {"PQ": "PQ", "QB_A": "QB", "QH_C": "QH_C", "QB_B": "QB"}
# Four-period Williams design: each arm occupies each position once and each
# directed carryover occurs once per complete four-block cycle.
ORDERS = ((0, 1, 3, 2), (1, 2, 0, 3), (2, 3, 1, 0), (3, 0, 2, 1))


def digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def geometry(gid, q, keys=256, d=128, g=8, storage="permuted", mask="causal", **extra):
    return dict(geometry_id=gid, q=q, keys=keys, d=d, Hq=32, Hkv=g,
                storage=storage, mask=mask, **extra)


def geometries():
    rows, edges = [], []
    for q in (2, 4):
        base = f"q{q}-k256"
        for keys in (255, 256, 257, 1023, 1024, 1025):
            rows.append(geometry(f"q{q}-k{keys}", q, keys, factor="length", cohort="confirmation"))
        for low, high in ((255, 256), (256, 257), (1023, 1024), (1024, 1025)):
            edges.append(dict(base=f"q{q}-k{low}", changed=f"q{q}-k{high}", factor="keys"))
        for g in (1, 32):
            gid = f"q{q}-g{g}"
            rows.append(geometry(gid, q, g=g, factor="GQA", cohort="confirmation"))
            edges.append(dict(base=base, changed=gid, factor="Hkv"))
        gid = f"q{q}-compact"
        rows.append(geometry(gid, q, storage="compact", factor="Q_storage", cohort="confirmation"))
        edges.append(dict(base=base, changed=gid, factor="storage"))
        for mask in ("irregular", "single_visible"):
            gid = f"q{q}-{mask}"
            rows.append(geometry(gid, q, mask=mask, factor="mask", cohort="confirmation"))
            edges.append(dict(base=base, changed=gid, factor="mask"))
        gid = f"q{q}-d64"
        rows.append(geometry(gid, q, d=64, factor="head_dimension", cohort="confirmation"))
        edges.append(dict(base=base, changed=gid, factor="d"))
    rows.extend([
        geometry("q1-short", 1, 128, factor="common_path_control", cohort="confirmation"),
        geometry("q1-long", 1, 1024, d=64, g=32, factor="common_path_control", cohort="confirmation"),
    ])
    for g in (4, 8):
        for keys in (511, 512, 513):
            rows.append(geometry(f"hold-q3-g{g}-k{keys}", 3, keys, g=g,
                                 factor="prospective_q3_boundary", cohort="holdout"))
    return rows, edges


def make_plan(samples=30, seed=20261018, qualification_method="H1"):
    if samples not in (30, 50):
        raise ValueError("measured calls must be 30 or 50; select before confirmation")
    if qualification_method not in ("H0", "H1"):
        raise ValueError("qualification method must be H0 or H1")
    geoms, edges = geometries()
    cases = []
    for g in geoms:
        for realization in (0, 1):
            cases.append(dict(g, case_id=f"{g['geometry_id']}-v{realization}", realization=realization,
                              data_recipe="coordinate_hash_v1", seed=20261018 + realization + (10000 if g["cohort"] == "holdout" else 0),
                              prior_exposure="structural confirmation;no latency-based selection" if
                              g["cohort"] == "confirmation" else "prospective holdout;do not inspect before rule freeze"))
    anchor_ids = [f"{g}-v0" for g in ("q1-short", "q1-long", "q2-k256", "q4-k256",
                                                    "q2-k1024", "q4-k1024", "q2-d64", "q4-d64")]
    tasks = []

    def add(stage, case, method, arm, block, session, position, warmups, calls, **extra):
        gates = {"reference": ["input_freeze"],
                 "qualification": ["input_freeze", "independent_reference"],
                 "aa_pilot": ["pilot_freeze", "method_numerical_qualification"],
                 "confirm": ["method_decision", "selected_method_qualification", "confirmation_freeze"],
                 "holdout": ["method_decision", "selected_method_qualification", "confirmation_freeze"]}[stage].copy()
        if case["cohort"] == "holdout":
            gates.insert(0, "prediction_freeze")
        tasks.append(dict(task_id=f"{stage}-{len(tasks):05d}", stage=stage,
                          case_id=case["case_id"], geometry_id=case["geometry_id"],
                          realization=case["realization"], method=method, arm=arm,
                          layout=LAYOUT.get(arm, arm), block=block, session=session,
                          position=position, warmups=warmups, measured_calls=calls,
                          optional=case["cohort"] == "holdout", requires=gates, **extra))

    # New bytes need independent serial q1 references. Each query is captured
    # twice in separate hosts; a reference capture is never a qualified candidate.
    for c in cases:
        for query in range(c["q"]):
            for repeat in range(2):
                add("reference", c, "H1", "PQ", repeat, "preparation", query, 0, 1,
                    query_index=query, capture_reference=True)
        for layout in ("PQ", "QB", "QH_C"):
            for repeat in range(2):
                add("qualification", c, qualification_method, layout, repeat, "preparation", 0, 2, 32)
        if c["case_id"] in anchor_ids:
            for repeat in range(2):
                add("qualification", c, "H0" if qualification_method == "H1" else "H1", "QB", repeat, "preparation", 0, 2, 32)

    anchors = [next(c for c in cases if c["case_id"] == cid) for cid in anchor_ids]
    for block in range(6):
        ordered = anchors.copy()
        random.Random(seed + 100 + block).shuffle(ordered)
        for index, c in enumerate(ordered):
            methods = ("H0", "H1") if (block + index) % 2 == 0 else ("H1", "H0")
            for method in methods:
                labels = ("QB_A", "QB_B") if (block + anchors.index(c)) % 2 == 0 else ("QB_B", "QB_A")
                for position, arm in enumerate(labels):
                    add("aa_pilot", c, method, arm, block, "pilot", position, 8, samples)

    for stage, cohort in (("confirm", "confirmation"), ("holdout", "holdout")):
        selected = [c for c in cases if c["cohort"] == cohort]
        for block in range(8):
            ordered = selected.copy()
            random.Random(seed + (1000 if stage == "holdout" else 0) + block).shuffle(ordered)
            for c in ordered:
                ci = selected.index(c)
                sequence = ORDERS[(block + ci) % 4]
                for position, arm_index in enumerate(sequence):
                    add(stage, c, "SELECTED", ARMS[arm_index], block,
                        f"{stage}-session{block // 4}", position, 8, samples)

    counts = {}
    for stage in ("reference", "qualification", "aa_pilot", "confirm", "holdout"):
        for optional in (False, True):
            selected = [t for t in tasks if t["stage"] == stage and t["optional"] == optional]
            if selected:
                counts[f"{stage}/{'optional' if optional else 'core'}"] = dict(
                    native_hosts=len(selected), graph_calls=sum(t["warmups"] + t["measured_calls"] for t in selected))
    plan = dict(schema_version=1, kind="CPU_TASK_PLAN_NOT_EXECUTION_AUTHORIZATION", parent_commit=PARENT,
                seed=seed, samples=samples, qualification_method=qualification_method, arms=list(ARMS), arm_to_layout=LAYOUT,
                order_cycles=[[ARMS[i] for i in order] for order in ORDERS],
                cases=cases, factor_edges=edges, aa_anchor_ids=anchor_ids, tasks=tasks, counts=counts,
                session_note="two separately started acquisition sessions;not independent dates",
                numerical_reference="independent serial q1 under pinned PR120 numerical stack",
                lifecycle="independently owned persistent inputs",
                unresolved=["actual input/reference hashes", "compiled runtime/source hashes", "GPU identity",
                            "selected method", "actual session IDs", "formal freeze", "raw run root"],
                resource_defaults=dict(wall_seconds=28800, closure_seconds=3600, new_storage_bytes=8*1024**3,
                                       host_ram_bytes=8*1024**3, GPU_workers=1, native_timeout_seconds=120),
                scientific_state="NOT_RUN")
    plan["plan_sha256"] = digest(plan)
    validate_plan(plan)
    return plan


def validate_plan(plan):
    copy = dict(plan)
    expected = copy.pop("plan_sha256")
    if digest(copy) != expected:
        raise ValueError("plan identity mismatch")
    ids = [t["task_id"] for t in plan["tasks"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate task IDs")
    case_map = {c["case_id"]: c for c in plan["cases"]}
    if len(case_map) != len(plan["cases"]):
        raise ValueError("duplicate case IDs")
    for t in plan["tasks"]:
        if t["case_id"] not in case_map or t["warmups"] + t["measured_calls"] > 64:
            raise ValueError("unresolved case or native call bound")
    by_geom = {g["geometry_id"]: g for g in plan["cases"] if g["realization"] == 0}
    numeric_fields = ("q", "keys", "d", "Hq", "Hkv", "storage", "mask")
    for edge in plan["factor_edges"]:
        changed = [key for key in numeric_fields if by_geom[edge["base"]][key] != by_geom[edge["changed"]][key]]
        if changed != [edge["factor"]]:
            raise ValueError("factor edge changes multiple declared factors")
    for stage in ("confirm", "holdout"):
        for cid in {t["case_id"] for t in plan["tasks"] if t["stage"] == stage}:
            for cycle in (0, 1):
                rows = [t for t in plan["tasks"] if t["stage"] == stage and t["case_id"] == cid and t["block"] // 4 == cycle]
                positions = collections.Counter((t["arm"], t["position"]) for t in rows)
                transitions = collections.Counter()
                for block in range(cycle*4, cycle*4+4):
                    order = sorted((t for t in rows if t["block"] == block), key=lambda t: t["position"])
                    transitions.update((a["arm"], b["arm"]) for a, b in zip(order, order[1:]))
                if len(positions) != 16 or set(positions.values()) != {1} or len(transitions) != 12 or set(transitions.values()) != {1}:
                    raise ValueError("unbalanced position/carryover cycle")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--samples", type=int, choices=(30, 50), default=30)
    parser.add_argument("--qualification-method", choices=("H0", "H1"), default="H1")
    args = parser.parse_args()
    plan = make_plan(args.samples, qualification_method=args.qualification_method)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8", newline="\n") as file:
        json.dump(plan, file, ensure_ascii=False, indent=2)
        file.write("\n")
    print(json.dumps(dict(plan_sha256=plan["plan_sha256"], counts=plan["counts"]), indent=2))


if __name__ == "__main__":
    main()
