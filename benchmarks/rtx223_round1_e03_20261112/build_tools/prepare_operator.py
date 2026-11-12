"""Prepare a disabled replay job and compile-resource report without CUDA calls."""
from pathlib import Path
import argparse
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def put(path, value):
    path=Path(path)
    with path.open("x",encoding="utf-8") as output:
        json.dump(value,output,indent=2)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--build",default="build_tools/build-v5")
    args=parser.parse_args()
    build=ROOT/args.build
    receipt=json.loads((build/"BUILD.json").read_text())
    if receipt["returncode"]!=0 or receipt.get("execution_enabled") is not False:
        raise RuntimeError("only an execution-disabled successful preparation build can be admitted here")
    fixture=ROOT/"audit/recovered_operand"
    weight=fixture/"weight.bin"
    activation=fixture/"input_q8_from_q32.bin"
    reference=fixture/"backend_loop4_historical_q8_output.bin"
    packed=fixture/"packed_historical_q8_output.bin"
    expected_sizes=((weight,17825792),(activation,131072),(reference,131072),(packed,131072))
    for path,size in expected_sizes:
        if path.stat().st_size!=size:
            raise RuntimeError(f"fixture length: {path}")
    if reference.read_bytes()!=packed.read_bytes():
        raise RuntimeError("historical A/B replay outputs differ")
    plan={"schema":"heterospec-rtx221-operator-v1","gpu_admitted":False,
        "status":"PREPARATION_ONLY_NOT_RUN","blocked_reasons":["ORIGINAL_THREAD_UNVERIFIED",
            "ACTUAL_CURRENT_Q8_CAPTURE_MISSING","GPU_LEDGER_AND_LOCK_RUNNER_NOT_INTEGRATED"],
        "executable":str(build/"operator_probe.exe"),"executable_sha256":receipt["executable_sha256"],
        "execution_enabled":False,"input_provenance":"DERIVED_REAL_Q32_PREFIX_NOT_CAPTURED_Q8",
        "weight_type":"Q8_0","input_type":"F32","q":8,"g":2,"k":4096,"m":4096,
        "padded_k":4096,"ids":False,"fusion":False,"graph_policy":"disabled",
        "input_stride_bytes":16384,"output_stride_bytes":16384,
        "logical_device":0,"device_uuid":"GPU-6dd57db3-9aac-ccc8-bd69-225a5ea2c4dd",
        "weight_path":str(weight),"weight_sha256":sha(weight),
        "input_path":str(activation),"input_sha256":sha(activation),
        "backend_output_path":str(reference),"backend_output_sha256":sha(reference),
        "historical_packed_output_path":str(packed),"historical_packed_output_sha256":sha(packed),
        "output_dir":str(ROOT/"native/future-run-not-created"),
        "warmups":3,"timing_blocks":6,
        "prospective_only_counts":{"correctness_operator_calls":6,"warmup_operator_calls":9,
            "timed_operator_calls":36,"quantizer_launches":51,"projection_launches":68,
            "total_kernel_launches":119,"capture_bytes":1007616,"model_requests":0,
            "target_rows":0,"draft_rows":0},
        "actual_counts":{"kernel_launches":0,"capture_bytes":0,"model_requests":0,"target_rows":0,"draft_rows":0}}
    put(ROOT/"native/OPERATOR_PREPARATION.json",plan)
    log=(build/"build.log").read_text(errors="replace")
    resources=[]
    pattern=r"Function properties for ([^\n]+)\n\s*(\d+) bytes stack frame, (\d+) bytes spill stores, (\d+) bytes spill loads\nptxas info\s*: Used (\d+) registers, used (\d+) barriers(?:, (\d+) bytes smem)?"
    for match in re.finditer(pattern,log):
        name,stack,stores,loads,registers,barriers,smem=match.groups()
        resources.append({"symbol":name,"stack_frame_bytes":int(stack),"spill_store_bytes":int(stores),
            "spill_load_bytes":int(loads),"registers_per_thread":int(registers),"barriers":int(barriers),
            "static_shared_bytes":int(smem or 0)})
    if len(resources)!=3:
        raise RuntimeError("expected three compiler-resource records")
    report={"status":"COMPILE_ONLY","native_execution":"NOT_RUN","build_receipt_sha256":sha(build/"BUILD.json"),
        "build_log_sha256":sha(build/"build.log"),"target_arch":"sm_120","resources":resources,
        "occupancy":"unknown","achieved_occupancy":"unknown","dram":"unknown","l2":"unknown",
        "A_to_B":"same case4 specialization; launch consolidation and group-grid concurrency; no current timing",
        "B_to_C":"two independent case4 accumulator groups share explicitly loaded weight fragments; resource increase compiled, no memory-traffic or latency measurement",
        "A_B_C_raw_pairs":"NOT_RUN","activation_bytes_comparison":"NOT_RUN","full_output_comparison":"NOT_RUN",
        "complete_service_cost":"NOT_RUN","round2_admission":False}
    put(ROOT/"native/BUILD_RESOURCE_FINDINGS.json",report)
    print(json.dumps({"prepared":True,"resources":resources,"gpu_execution":False},indent=2))

if __name__=="__main__":
    main()
