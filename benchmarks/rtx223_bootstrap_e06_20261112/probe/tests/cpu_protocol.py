"""Actual anonymous pipes and delayed grants to one pinned CPU-only executable."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
BUILD = WORK / "rtx223-e06/build/probes-attempt-002"
EXE = BUILD / "cpu-probe.exe"
EXPECTED = "8a5cc2607dfdf3e59902dbb359e09e20e4348aa736b7bd3fac788fa996f449cb"
PARSER = WORK / "rtx223-round1-resume-20261112-e04/e04/frontend/pe_identity_v2.py"
STAGES = ["METER", "LOAD", "COUNT", "UUID", "CLOSE", "FLUSH"]
tick = ctypes.windll.kernel32.GetTickCount64
tick.restype = ctypes.c_uint64


def need(ok, why):
    if not ok:
        raise ValueError(why)


def pin():
    recipe = json.loads((BUILD / "RECIPE.json").read_bytes())
    link = recipe["link"][EXE.name]
    objects = {Path(s).name for s in link if s.lower().endswith(".obj")}
    need(objects == {"main.obj", "fake.obj"}, "link does not use fake backend exclusively")
    build = json.loads((BUILD / "BUILD.json").read_bytes())
    need(build["outputs"][EXE.name]["sha256"] == EXPECTED, "unexpected build")
    need(hashlib.sha256(PARSER.read_bytes()).hexdigest()
         == "a5029ff6f885991793fb04dffb56a74bef8db188151d6cb879680f3c228fdb3c", "PE reader")
    pe = runpy.run_path(str(PARSER))["inspect"](EXE)
    need(pe["sha256"] == EXPECTED and pe["imports"] == ["KERNEL32.dll"]
         and not pe["delay_imports"] and not pe["is_dll"], "unexpected actual executable/PE")
    return {"sha256": EXPECTED, "imports": pe["imports"], "objects": sorted(objects)}


def payload(stages):
    return b"".join(("GO_" + stage + "\n").encode("ascii") for stage in stages)


def run_case(label, fail_at=None, *, fault="", before=None, invalid=None, delay_at=None,
             deadline_kind=None, reason=None):
    need(hashlib.sha256(EXE.read_bytes()).hexdigest() == EXPECTED, "fake executable changed")
    deadline = tick() + (900 if delay_at else 5000)
    env = {"SystemRoot": os.environ["SystemRoot"], "HS_B_FAULT": fault,
           "HS_B_DEADLINE_TICK": str(deadline)}
    if deadline_kind == "absent":
        del env["HS_B_DEADLINE_TICK"]
    if deadline_kind == "expired":
        env["HS_B_DEADLINE_TICK"] = str(tick() - 1)
    if deadline_kind == "excess":
        env["HS_B_DEADLINE_TICK"] = str(tick() + 90000)
    with subprocess.Popen([str(EXE)], cwd=BUILD, env=env, stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          creationflags=subprocess.CREATE_NO_WINDOW) as child:
        guard = threading.Timer(5, child.kill)
        guard.start()
        prefix = []
        try:
            if delay_at:
                prefix.append(child.stdout.readline())
                need(prefix[-1] == b"READY\n", "fake missing READY")
                index = STAGES.index(delay_at)
                for stage in STAGES[:index]:
                    child.stdin.write(payload([stage]))
                    child.stdin.flush()
                    prefix.append(child.stdout.readline())
                    need(prefix[-1] == ("OK_" + stage + "\n").encode(), "prerequisite failed")
                time.sleep(max(0, deadline + 50 - tick()) / 1000)
                data = payload(STAGES[index:])
            elif invalid is not None:
                data = payload(STAGES[:STAGES.index(before)]) + invalid
            else:
                data = payload(STAGES)
            stdout, stderr = child.communicate(data)
        finally:
            guard.cancel()
            guard.join()
    lines = (b"".join(prefix) + stdout).decode("ascii").splitlines()
    item = {"case": label, "exit": child.returncode, "stdout": lines, "stderr": stderr.decode("ascii")}
    if fail_at:
        need(child.returncode == 2 and lines and lines[-1].startswith("ERROR " + fail_at + " ")
             and "END" not in lines and not stderr, f"{label}: {item}")
        if reason:
            need(reason in lines[-1], f"{label}: {item}")
        if fail_at in STAGES:
            allowed = STAGES[:STAGES.index(fail_at)]
            # A fault at the final evidence seal may be detected after OK_FLUSH.
            if fault == "late":
                allowed = STAGES
            need(lines[:-1] == ["READY", *("OK_" + s for s in allowed)], f"{label}: {item}")
    else:
        expected = ["READY", *("OK_" + s for s in STAGES)]
        need(child.returncode == 0 and lines[:-2] == expected and lines[-1] == "END" and not stderr,
             f"{label}: {item}")
        receipt = json.loads(lines[-2].removeprefix("RECEIPT "))
        need(receipt["backend"] == "cpu-fake" and receipt["pid"] == child.pid
             and receipt["physical_upper_bound"] is None and receipt["api_callbacks"] == 4
             and receipt["drop_reads"] == [0, 0] and receipt["drained"], "fake receipt")
    return item


def main():
    evidence = {"scope": "CPU fake; actual Windows pipes. No CUPTI/DLL/CUDA or Job qualification.",
                "binary": pin(), "checks": [], "normal_numeric_DLL_loads": 0,
                "GPU_contexts": 0, "kernel_launches": 0, "models": 0}
    cases = evidence["checks"]
    cases.append(run_case("all_grants"))
    for kind in ["absent", "expired", "excess"]:
        cases.append(run_case("deadline_" + kind, "PREFLIGHT", deadline_kind=kind))
    for stage in STAGES:
        cases.append(run_case("fault_" + stage.lower(), stage, fault=stage.lower()))
        cases.append(run_case("eof_" + stage.lower(), stage, before=stage, invalid=b""))
    for stage in STAGES[:4]:
        cases.append(run_case("stale_grant_" + stage.lower(), stage, delay_at=stage,
                              reason="deadline_elapsed"))
    cases.append(run_case("late_cleanup_allowed", delay_at="CLOSE"))
    cases.append(run_case("wrong_order", "METER", before="METER", invalid=b"GO_LOAD\n"))
    cases.append(run_case("parent_stop", "COUNT", before="COUNT", invalid=b"STOP\n"))
    for fault, stage, reason in [
        ("count2", "COUNT", "device_count"), ("wrong_uuid", "UUID", "device_identity"),
        ("drop", "FLUSH", "dropped_first=1"), ("kernel", "FLUSH", "kernels=1"),
        ("pool", "FLUSH", "trace_incomplete"), ("incomplete", "FLUSH", "trace_incomplete"),
        ("unattributed", "FLUSH", "trace_attribution"), ("late", "FLUSH", "late_callback"),
    ]:
        cases.append(run_case(fault, stage, fault=fault, reason=reason))
    json.dump(evidence, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
