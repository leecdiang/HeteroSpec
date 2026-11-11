"""Independent host checks of exact entry contracts and synthetic policy edges.

The generated vectors and receipts are HOST_ONLY parser fixtures. They are not
model output, numerical qualification, performance evidence or production runs.
"""
from __future__ import annotations
import argparse
from array import array
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True


def need(value, message):
    if not value:
        raise RuntimeError(message)


def identity(path):
    data = Path(path).read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--production", type=Path, required=True)
    parser.add_argument("--controller", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    need(not args.out.exists() and not args.out.is_symlink(), "Fresh output required")
    args.out.mkdir(parents=True)
    names = [("protocol", args.production / "protocol.py"),
             ("independent_production", args.production / "verify_production.py"),
             ("independent_causal", args.controller / "causal_policy.py")]
    before = {name: identity(path) for name, path in names}
    protocol = load(*names[0])
    verifier = load(*names[1])
    policy = load(*names[2])
    checks = []

    def passed(name, detail):
        checks.append({"check": name, "status": "PASS", "detail": detail})

    # An initial EOG request reaches the original entry's terminal observer,
    # which writes two files. Worker snapshots write three, including metadata.
    fixture = args.out / "HOST_ONLY_initial_EOG_parser_fixture"
    (fixture / "target/state/initial").mkdir(parents=True)
    (fixture / "target/state/terminal").mkdir()
    (fixture / "draft").mkdir()
    token = verifier.EOG[0]
    values = array('f', [0.0]) * verifier.VOCAB
    values[token] = 1.0
    if sys.byteorder != 'little':
        values.byteswap()
    payload = values.tobytes()
    (fixture / "target/initial.f32").write_bytes(payload)
    for name in ("initial", "terminal"):
        (fixture / f"target/state/{name}/frontier.f32").write_bytes(payload)
        (fixture / f"target/state/{name}/sequence.bin").write_bytes(b"HOST_ONLY_NOT_NATIVE_STATE")
    state_bytes = (fixture / "target/state/initial/sequence.bin").stat().st_size
    (fixture / "target/state/initial/capture.txt").write_text(
        f"frontier_row=-1\nvocab={verifier.VOCAB}\nsequence_bytes={state_bytes}\n"
        "position_min=0\nposition_max=0\npayload_kind=raw_native_sequence\nactive_kv_extraction_required=true\n")
    (fixture / "HOST_ONLY.txt").write_text("Manually constructed parser fixture; not model output or a native-state qualification.\n")
    receipt = {"cycles": [], "ids": [token], "eog": [True], "length": 1,
               "terminal_id": token, "stop_reason": "EOG"}
    need(verifier.logical_walk(receipt, fixture, {"prompt_ids": [1]}) == 1,
         "Correct two-file terminal contract rejected")
    passed("original_entry_terminal_two_files", "Initial EOG parser fixture accepted; no terminal capture.txt invented")
    missing = fixture / "target/state/terminal/sequence.bin"
    saved = missing.read_bytes(); missing.unlink()
    try:
        verifier.logical_walk(receipt, fixture, {"prompt_ids": [1]})
    except ValueError as error:
        need(str(error) == "checkpoint members differ", "Unexpected missing-state rejection")
    else:
        raise RuntimeError("Terminal state was optional")
    missing.write_bytes(saved)
    passed("terminal_state_still_required", "Missing sequence payload rejected before a qualification can be claimed")

    # A 151-token prefill is one draft API call and 38 physical draft ubatches.
    case = {"prompt_ids": [1] * 151}
    for deferred, draft_steps in ((0, 16), (1, 15)):
        mock = {"cycles": [{"accepted": 7}, {"accepted": 3}], "target_calls": 7,
                "draft_calls": 1 + draft_steps,
                "target_physical_width_hist": {"32": 4, "23": 1, "8": 2},
                "draft_physical_width_hist": {"4": 37, "3": 1, "1": draft_steps},
                "draft_tail_skipped": deferred, "draft_tail_recovered": deferred}
        work = protocol.actual_work(mock, case, deferred)
        need(work == {"target_decode_calls": 7, "draft_decode_calls": 1 + draft_steps,
                      "target_physical_microbatches": 7, "draft_physical_microbatches": 38 + draft_steps,
                      "target_rows": 167, "draft_rows": 151 + draft_steps}, "API/physical or recovery budget conflated")
    passed("API_vs_physical_and_tail_recovery", "Manual two-cycle counterexample: eager17/deferred16 draft API calls; physical54/53; recovered one fully accepted tail")
    inputs = json.loads((args.production / "INPUTS.json").read_text())
    plan = protocol.make_plan(inputs)
    work = plan["work_ceiling"]
    need(plan["processes"] == 6 and plan["request_ceiling"] == 12 and
         work["target_decode_calls"] + work["draft_decode_calls"] == 1686 and
         work["target_physical_microbatches"] + work["draft_physical_microbatches"] == 2082 and
         work["target_rows"] + work["draft_rows"] == 6096, "Fixed full-plan budget changed")
    need(plan["performance_admitted"] is False, "Preparation became performance admission")
    passed("fixed_production_plan_budget", "12 requests maximum; 1686 decode APIs; 2082 physical microbatches; 6096 total rows; no execution")

    for name, status, completed, attempted, expected in (
        ("complete_with_only_capture_pair", "COMPLETE_PREPARATION_NOT_PERFORMANCE_ADMITTED", [{}, {}], 2,
         "status/process count is partial, excessive, or inconsistent"),
        ("capture_pair_after_failed_extra_attempt", "CAPTURE_COMPLETE_PENDING_COMPARISON", [{}, {}], 3,
         "status/process count is partial, excessive, or inconsistent"),
        ("cross_run_record", "CAPTURE_COMPLETE_PENDING_COMPARISON",
         [{"name": plan["jobs"][0]["name"], "run_id": "different-host-fixture"}, {}], 2,
         "cross-run or skipped job"),
    ):
        directory = args.out / ("HOST_ONLY_" + name)
        directory.mkdir()
        for filename, value in (("INPUTS.json", inputs), ("PLAN.json", plan)):
            (directory / filename).write_text(json.dumps(value, indent=2) + "\n")
        run = {"status": status, "completed": completed, "attempted_processes": attempted,
               "run_id": "host-fixture", "plan_identity": identity(directory / "PLAN.json"),
               "inputs_identity": identity(directory / "INPUTS.json")}
        (directory / "RUN.json").write_text(json.dumps(run, indent=2) + "\n")
        (directory / "HOST_ONLY.txt").write_text("Negative lifecycle parser fixture; no native process or evidence exists.\n")
        try:
            verifier.verify_directory(directory)
        except ValueError as error:
            need(str(error) == expected, name + " failed for an unrelated reason: " + str(error))
        else:
            raise RuntimeError("Invalid lifecycle admitted: " + name)
        passed(name, "Rejected before any request/vector record was read: " + expected)

    snap = policy.Snapshot("deployment-A", "state-A", tuple(range(10, 17)), 0, 8, 4)
    branches = policy.outcomes(snap, 0, 4, (0.5,) * 7)
    terminal = next(x for x in branches if x.label == "accepted_terminal:4")
    need(terminal.target_materializations == 1 and terminal.draft_materializations == 0,
         "p4 terminal did not price the missing target input")
    bad_prices = {x.label: policy.Price(1, 0, 0, "HOST_ONLY_POSTCONDITION") for x in branches}
    bad = policy.SyntheticModel("deployment-A", "state-A", 100, 0,
                               (policy.SyntheticStage(0, 4, bad_prices),), {})
    decision = policy.solve_model(snap, bad, (0.5,) * 7)
    need(decision["action"] is None and
         any(x["reason"] == "UNPRICED_REQUIRED_MATERIALIZATION" for x in decision["rejected_actions"]),
         "Underpriced terminal action accepted")
    prices = dict(bad_prices)
    prices[terminal.label] = policy.Price(2, 1, 0, "HOST_ONLY_MATERIALIZED_P4")
    model = policy.SyntheticModel("deployment-A", "state-A", 100, 0,
                                 (policy.SyntheticStage(0, 4, prices),), {})
    need(policy.solve_model(snap, model, (0.5,) * 7)["action"] == "VERIFY_NEXT", "Complete synthetic action rejected")
    passed("terminal_p4_materialization_gate", "Unpriced target q1 is unavailable; explicitly synthetic complete branch can be modeled")
    history = policy.PastAcceptance()
    history.announce("observed-action", 0, 4, 7)
    learned = history.observe("observed-action", (True, False, True, True))
    need(learned == ((1, True), (2, False)) and sum(history.success) == 1 and sum(history.failure) == 1,
         "Censored suffix affected acceptance history")
    try:
        history.observe("observed-action", (True, False, True, True))
    except policy.PolicyError:
        pass
    else:
        raise RuntimeError("Observation replay accepted")
    passed("causal_observation_and_censoring", "First mismatch closes learning; later bits ignored; duplicate event rejected")
    future = {"deployment_key": "deployment-A", "state_key": "state-A", "candidate_tokens": tuple(range(10, 17)),
              "verified_rows": 0, "draft_materialized_rows": 8, "remaining_cap": 4, "future_acceptance": 7}
    try:
        policy.Snapshot.from_mapping(future)
    except policy.PolicyError as error:
        need("FUTURE_OR_UNKNOWN_FIELDS" in str(error), "Future field failed for unrelated reason")
    else:
        raise RuntimeError("Future acceptance exposed to decision")
    passed("future_fields_rejected", "Snapshot interface rejects explicit future acceptance")
    control = policy.CausalController(overhead_limit_nanoseconds=10**9)
    for artifact in (None, {"schema": "legacy"}, {"schema": "heterospec.typed-macro-costs.v2",
                                               "online_stage_cost_eligible": True}, model):
        answer = control.decide_runtime(snap, artifact)
        need(answer["status"] == "ABSTAIN" and answer["action"] is None and not answer["actuation_allowed"],
             "Runtime promoted missing, old, relabeled macro or synthetic cost")
    passed("runtime_abstains_from_every_available_cost_type", "Even a relabeled macro cannot enable actuation")
    ticks = iter((0, 2, 2, 3))
    limited = policy.CausalController(overhead_limit_nanoseconds=1, clock=lambda: next(ticks))
    first = limited.decide_runtime(snap); second = limited.decide_runtime(snap)
    need(first["controller_span_nanoseconds"] == 2 and first["controller_disabled"] and
         second["controller_span_total_nanoseconds"] == 3 and second["reason"] == "CONTROLLER_DISABLED_AFTER_OVERHEAD",
         "Incurred decision overhead was erased")
    passed("fallback_overhead_accounted", "Over-budget evaluation remains charged and disables later recommendations")
    need(before == {name: identity(path) for name, path in names}, "Source changed during audit")
    report = {"schema": "heterospec.independent-new-components-audit.v1", "status": "PASS_HOST_ONLY_CONTRACT_CHECKS",
              "sources": before, "auditor": identity(__file__), "checks": checks,
              "new_model_executions": 0, "CUDA_driver_calls": 0, "native_executable_runs": 0,
              "production_qualification": "NOT_RUN", "performance_admitted": False,
              "limitations": ["Synthetic parser/policy cases test software contracts only.",
                              "No measured stage costs or real controller action were admitted.",
                              "Production GPU integration, historical R and clean-state bridge remain open."]}
    with (args.out / "AUDIT.json").open("x") as stream:
        json.dump(report, stream, indent=2); stream.write("\n")
    print(json.dumps({"status": report["status"], "checks": len(checks), "new_model_executions": 0, "performance_admitted": False}))


if __name__ == "__main__":
    main()
