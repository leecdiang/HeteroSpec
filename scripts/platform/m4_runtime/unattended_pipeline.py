#!/usr/bin/env python3
"""Run the frozen M4 study end to end without live agent supervision."""

import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "benchmarks/m4_runtime"
RUNS = ROOT / "runs/m4/runtime_profitability_control_20260924"
PYTHON = ROOT / ".venv-m4/bin/python"
STUDY = ROOT / "scripts/platform/m4_runtime/run_runtime_study.py"
BRANCH = "runtime/m4-profitability-control-v0.1"


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def output(*command):
    return subprocess.check_output(command, cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()


def write_json(path, data):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def environment():
    power = output("pmset", "-g", "batt")
    thermal = output("pmset", "-g", "therm")
    settings = output("pmset", "-g", "custom")
    if "AC Power" not in power:
        raise RuntimeError("AC power is required for an uninterrupted M4 attempt")
    if "No thermal warning level has been recorded" not in thermal:
        raise RuntimeError("Thermal warning is active or unavailable")
    values = re.findall(r"^\s*lowpowermode\s+(\d+)\s*$", settings, re.MULTILINE)
    if not values or any(value != "0" for value in values):
        raise RuntimeError("Low Power Mode must be off for both power profiles")
    return {"power": power, "thermal": thermal, "lowpowermode": values,
            "hardware_model": output("sysctl", "-n", "hw.model"),
            "macos_build": output("sw_vers", "-buildVersion")}


def sleep_event_count():
    result = subprocess.run(["pmset", "-g", "log"], cwd=ROOT, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    if result.returncode:
        raise RuntimeError("Could not audit macOS sleep log")
    return len(re.findall(r"Entering Sleep", result.stdout, re.IGNORECASE))


def preflight():
    if output("git", "branch", "--show-current") != BRANCH:
        raise RuntimeError("Unexpected study branch")
    if output("git", "status", "--porcelain"):
        raise RuntimeError("Study working tree must be clean before starting")
    binary = RUNS / "build/m4-runtime-runner"
    manifest = json.loads((RUNS / "build/manifest.json").read_text())
    if sha(binary) != manifest["binary_sha256"]:
        raise RuntimeError("Runtime binary does not match the build manifest")
    if sha(ROOT / "scripts/platform/m4_runtime/runtime_runner.cpp") != manifest["source_sha256"]:
        raise RuntimeError("Runtime source does not match the build manifest")
    if "5266f24da" not in output("/opt/homebrew/bin/llama-server", "--version"):
        raise RuntimeError("Pinned llama.cpp is unavailable")
    subprocess.run([str(PYTHON), "scripts/platform/m4_runtime/validate_runtime_scaffold.py"],
                   cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    subprocess.run([str(PYTHON), "scripts/platform/m4_runtime/validate_r0_traces.py"],
                   cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    return environment()


def audit_attempt(stage, attempt_id, expected, sleep_before):
    directory = RUNS / stage / attempt_id
    completion = json.loads((directory / "completion.json").read_text())
    raw = directory / "observations.jsonl"
    if completion["status"] != "COMPLETE" or completion["observations"] != expected or completion["observations_sha256"] != sha(raw):
        raise RuntimeError(f"{stage} attempt incomplete or changed")
    with raw.open(encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream]
    if len(rows) != expected:
        raise RuntimeError(f"{stage} observation count changed")
    for row in rows:
        state = row["power_thermal"]
        if "AC Power" not in state["power"] or "No thermal warning level has been recorded" not in state["thermal"]:
            raise RuntimeError(f"{stage} had an invalid power or thermal observation")
        modes = re.findall(r"^\s*lowpowermode\s+(\d+)\s*$", state["power_settings"], re.MULTILINE)
        if not modes or any(value != "0" for value in modes):
            raise RuntimeError(f"{stage} had Low Power Mode enabled")
    if sleep_event_count() != sleep_before:
        raise RuntimeError(f"macOS sleep log changed during {stage}")
    return {"observations": expected, "sha256": sha(raw)}


def main():
    if len(sys.argv) != 2 or not re.fullmatch(r"[a-z0-9][a-z0-9-]{7,63}", sys.argv[1]):
        raise SystemExit("Usage: unattended_pipeline.py <unique-run-id>")
    run_id = sys.argv[1]
    directory = RUNS / "pipeline" / run_id
    directory.mkdir(parents=True, exist_ok=False)
    lock_path = RUNS / "pipeline.lock"
    with lock_path.open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Another unattended M4 pipeline is already running") from exc
        lock.write(str(os.getpid()) + "\n")
        lock.flush()
        os.fsync(lock.fileno())
        log_path = directory / "pipeline.log"
        status_path = directory / "status.json"
        with log_path.open("a", encoding="utf-8", buffering=1) as log:
            def log_line(message):
                log.write(f"{utc()} {message}\n")
                log.flush()
                os.fsync(log.fileno())

            state = {"schema": "heterospec.m4_runtime.pipeline.v0.1", "run_id": run_id,
                     "status": "STARTING", "started_utc": utc(), "pid": os.getpid(),
                     "branch": BRANCH, "head_at_start": output("git", "rev-parse", "HEAD"),
                     "stages": {}, "log_path": str(log_path)}
            write_json(status_path, state)
            assertion = subprocess.Popen(["caffeinate", "-disu", "-w", str(os.getpid())],
                                         stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                         start_new_session=True)
            try:
                state["preflight_environment"] = preflight()
                write_json(status_path, state)
                sleep_before = sleep_event_count()

                def run_stage(name, command, audit=None):
                    nonlocal sleep_before
                    environment()
                    if assertion.poll() is not None:
                        raise RuntimeError("macOS wake assertion is no longer active")
                    state["status"] = "RUNNING"
                    state["current_stage"] = name
                    state["stages"][name] = {"status": "RUNNING", "started_utc": utc()}
                    write_json(status_path, state)
                    log_line(f"START {name}: {' '.join(map(str, command))}")
                    result = subprocess.run(command, cwd=ROOT, stdin=subprocess.DEVNULL,
                                            stdout=log, stderr=subprocess.STDOUT)
                    if result.returncode:
                        raise RuntimeError(f"{name} exited {result.returncode}")
                    details = audit(sleep_before) if audit else {}
                    environment()
                    if sleep_event_count() != sleep_before:
                        raise RuntimeError(f"macOS sleep log changed during {name}")
                    sleep_before = sleep_event_count()
                    state["stages"][name] = {"status": "COMPLETE", "completed_utc": utc(), **details}
                    write_json(status_path, state)
                    log_line(f"COMPLETE {name}")

                baseline = run_id + "-baseline"
                candidate = run_id + "-candidate"
                qualification = run_id + "-qualification"
                formal = run_id + "-formal"
                run_stage("baseline", [str(PYTHON), "-u", str(STUDY), "baselines", "--attempt", baseline],
                          lambda count: audit_attempt("calibration_baselines", baseline, 240, count))
                run_stage("candidates", [str(PYTHON), "-u", str(STUDY), "candidates", "--attempt", candidate,
                                         "--baseline-attempt", baseline],
                          lambda count: audit_attempt("calibration_candidates", candidate, 1080, count))
                run_stage("freeze", [str(PYTHON), "-u", str(STUDY), "freeze", "--baseline-attempt", baseline,
                                     "--candidate-attempt", candidate])
                if json.loads((BASE / "CALIBRATION_FREEZE.json").read_text())["status"] != "CALIBRATION_FROZEN":
                    raise RuntimeError("Calibration freeze is incomplete")
                subprocess.run(["git", "add", "benchmarks/m4_runtime/CALIBRATION_FREEZE.json"], cwd=ROOT, check=True)
                subprocess.run(["git", "commit", "-m", "Freeze prospective M4 runtime guard policy"],
                               cwd=ROOT, check=True, stdout=log, stderr=subprocess.STDOUT)
                if output("git", "status", "--porcelain"):
                    raise RuntimeError("Tree dirty after calibration freeze commit")
                run_stage("qualification", [str(PYTHON), "-u", str(STUDY), "qualify", "--attempt", qualification],
                          lambda count: audit_attempt("qualification", qualification, 144, count))
                if json.loads((BASE / "QUALIFICATION_REPORT.json").read_text())["status"] != "PASS":
                    raise RuntimeError("Qualification did not pass")
                subprocess.run(["git", "add", "benchmarks/m4_runtime/QUALIFICATION_REPORT.json"], cwd=ROOT, check=True)
                subprocess.run(["git", "commit", "-m", "Record M4 runtime guard qualification"],
                               cwd=ROOT, check=True, stdout=log, stderr=subprocess.STDOUT)
                if output("git", "status", "--porcelain"):
                    raise RuntimeError("Tree dirty before formal measurement")
                run_stage("formal", [str(PYTHON), "-u", str(STUDY), "formal", "--attempt", formal],
                          lambda count: audit_attempt("formal", formal, 540, count))
                run_stage("analysis", [str(PYTHON), "-u",
                                       str(ROOT / "scripts/platform/m4_runtime/analyze_runtime_study.py"),
                                       "--attempt", formal])
                subprocess.run(["git", "add", "benchmarks/m4_runtime/FORMAL_ANALYSIS.json",
                                "benchmarks/m4_runtime/FORMAL_REPORT.md"], cwd=ROOT, check=True)
                subprocess.run(["git", "commit", "-m", "Report prospective M4 runtime guard results"],
                               cwd=ROOT, check=True, stdout=log, stderr=subprocess.STDOUT)
                if output("git", "status", "--porcelain"):
                    raise RuntimeError("Tree dirty after final report commit")
                state["status"] = "COMPLETE"
                state["current_stage"] = None
                state["completed_utc"] = utc()
                state["head_at_completion"] = output("git", "rev-parse", "HEAD")
                state["formal_report"] = str(BASE / "FORMAL_REPORT.md")
                write_json(status_path, state)
                log_line("PIPELINE COMPLETE")
            except BaseException as exc:
                state["status"] = "STOPPED"
                state["stopped_utc"] = utc()
                state["reason"] = f"{type(exc).__name__}: {exc}"
                if state.get("current_stage") in state["stages"]:
                    state["stages"][state["current_stage"]]["status"] = "STOPPED"
                write_json(status_path, state)
                log_line(f"PIPELINE STOPPED: {state['reason']}")
                raise
            finally:
                if assertion.poll() is None:
                    assertion.terminate()
                    assertion.wait(timeout=10)


if __name__ == "__main__":
    main()
