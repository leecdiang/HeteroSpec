"""CPU-only R-input handoff. Does not create, launch or authorize a worker."""
import copy
import hashlib
import json
from pathlib import Path

OLD_TEMPLATE_SHA = "4287bde0bfb1b34b35fbd2a4b0d9ef39106e1fefa864eea760196ecbc3c063ac"
ROLES = ("RESIDENT_R", "REPEAT_RESIDENT_R", "COLD_CANONICAL_ORACLE",
         "STRONG_WHOLE_RECHUNK_LOOP4")
EOG = {128247, 151643, 151645, 151662, 151663, 151664}


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def tokens(value):
    need(type(value) is list and value and
         all(type(t) is int and 0 <= t < 151936 for t in value),
         "complete bound dense token vector required")
    return value


def load_template(repo=None):
    p = (Path(repo) / "benchmarks/server_expansion_v1/N/native_chain_successor_20261112/NATIVE_JOB_TEMPLATE.json"
         if repo is not None else Path(__file__).resolve().parent.parent /
         "native_chain_successor_20261112/NATIVE_JOB_TEMPLATE.json")
    b = p.read_bytes()
    need(hashlib.sha256(b).hexdigest() == OLD_TEMPLATE_SHA, "frozen input template changed")
    return json.loads(b)


def reference_id(operation):
    fields = operation.split("/")
    need(len(fields) >= 4 and fields[1] in ROLES, "unplanned operation ID")
    fields[1] = ROLES[0]
    return "/".join(fields)


def validate_reference_inputs(repo, run_id, inputs):
    template = load_template(repo)
    fixed = {o["id"]: (e["kind"], o) for j in template["jobs"] if j["role"] == ROLES[0]
             for e in j["episodes"] for o in e["operations"]}
    need(type(inputs) is dict and set(inputs) == set(fixed), "all eighteen R inputs are required")
    for ident, item in inputs.items():
        kind, op = fixed[ident]
        need(type(item) is dict, "R input certificate item")
        q, generated = tokens(item.get("canonical_ids")), tokens(item.get("generated_ids"))
        cap = op["cap"]
        need(item.get("generation_cap") == cap and type(item.get("generation_cap")) is int,
             "R cap changed")
        keep = item.get("retained_head")
        need(type(keep) is int and 0 <= keep < len(q) and len(q) + cap - 1 <= 4096,
             "R retained alignment or capacity invalid")
        need(0 < len(generated) <= cap and not any(t in EOG for t in generated[:-1]),
             "R generated/stop lifecycle invalid")
        stop = item.get("stop_reason")
        need((stop == "EOG" and generated[-1] in EOG) or
             (stop == "CAP" and len(generated) == cap and not any(t in EOG for t in generated)),
             "R EOG/cap mismatch")
        if kind == "SCRIPTED_RAW_TOKEN_CONTROL":
            need(q == op["canonical_ids"] and generated == op["forced_terminal_ids"],
                 "R scripted control changed")
        elif ident.endswith("/0"):
            need(q == op["expected_canonical_ids"], "R initial canonical input changed")
        for name, phase in (("post_reconcile_snapshot", "POST_RECONCILE"),
                            ("terminal_snapshot", "TERMINAL")):
            d = item.get(name)
            need(type(d) is dict and d.get("operation_id") == ident and
                 d.get("phase") == phase and d.get("run_id") == run_id and
                 type(d.get("file")) is str and
                 all(type(d.get(k)) is str and len(d[k]) == 64 and
                     all(c in "0123456789abcdef" for c in d[k])
                     for k in ("sha256", "executable_sha256")),
                 "R handoff lacks exact verified snapshot provenance")
    return copy.deepcopy(inputs)


def prepare_stage_jobs(repo, manifest, stage, reference_certificate=None):
    """Return NO_GO job templates; expected R IDs never force a free producer."""
    need(stage in ROLES, "unknown stage")
    template = load_template(repo)
    need(manifest.get("mode") == "CPU_MOCK_ONLY" and
         manifest.get("native_execution_authorized") is False,
         "this preparer has no native admission path")
    inputs = None
    if stage != ROLES[0]:
        cert = reference_certificate
        need(type(cert) is dict and cert.get("schema") == "hs.N1controller.R-input-certificate.v1"
             and cert.get("run_id") == manifest["run_id"] and
             cert.get("native_execution_authorized") is False and
             cert.get("scope") == "PROVIDED_R_SELF_CHECKS_NOT_COLD_EQUIVALENCE",
             "missing verified R handoff; repeat alone cannot replace cold oracle")
        inputs = validate_reference_inputs(repo, manifest["run_id"], cert["reference_inputs"])
    jobs = []
    for old in template["jobs"]:
        if old["role"] != stage:
            continue
        job = copy.deepcopy(old)
        job["execution_authorized"] = False
        job["run_id"] = manifest["run_id"]
        job["accounting_manifest_sha256"] = manifest["manifest_sha256"]
        job["controller_owner"] = None
        job["owner_lease_sha256"] = None
        job["preexec_placement_reservation"] = None
        job["source_gate"] = "NATIVE_PRODUCTION_GATE_CLOSED"
        bind = manifest.get("worker_bindings", {}).get(job["worker_id"], {})
        for key in ("source_sha256", "executable_sha256", "writer_sha256", "identity"):
            if key in bind:
                job[key] = copy.deepcopy(bind[key])
        for episode in job["episodes"]:
            for op in episode["operations"]:
                if inputs is None:
                    continue
                ref = inputs[reference_id(op["id"])]
                if stage == ROLES[2]:
                    op["canonical_ids"] = list(ref["canonical_ids"])
                    op["reference_retained_head"] = ref["retained_head"]
                    op["input_scope"] = ("SCRIPTED_CONTROL_ORACLE_REPLAY" if
                        episode["kind"] == "SCRIPTED_RAW_TOKEN_CONTROL" else
                        "ACTUAL_R_CANONICAL_INPUT_ORACLE_REPLAY")
                else:
                    op["expected_canonical_ids"] = list(ref["canonical_ids"])
                    # The candidate keeps its own user/producer path. It cannot
                    # consume these expected IDs as a forced natural tape.
                    op["input_scope"] = ("SCRIPTED_CONTROL_WITH_R_INPUT_ASSERTION" if
                        episode["kind"] == "SCRIPTED_RAW_TOKEN_CONTROL" else
                        "OWN_FREE_PRODUCER_WITH_R_INPUT_ASSERTION")
                op.pop("unresolved", None)
        job["unresolved_native_admission"] = [
            "Separate approval/device/budget/window", "Actual loaded identities",
            "Reviewed launcher owner/BINDCHILD/close-before-worker connector",
            "Verified cgroup membership, complete bounded log/exit witness",
            "Controller endpoint/lease/model path/source/writer/executable identity"]
        jobs.append(job)
    need(len(jobs) == 2, "one natural and one control worker required")
    return jobs

