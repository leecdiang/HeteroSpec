"""Focused native transfer diagnostics using the PR162 Windows Job supervisor."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path("E:/rtx164")
PREVIOUS = Path("C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/pr160")
OLD = Path("E:/rtx160/research")
NEW = ROOT / "diagnostics04"


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4194304), b""):
            h.update(block)
    return h.hexdigest()


def save(path, data):
    with path.open("x", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def run(profile, library):
    old = OLD / profile
    bundle = NEW / profile
    bundle.mkdir()
    panel = read(old / "DEV.json")
    slots = read(old / "SLOTS.json")
    inputs = set()
    predictions = []
    for file in sorted((old / "units/regression/native").rglob("C_QB/native/heavy.json")):
        record = read(file)
        for cycle in record["cycles"]:
            head, rows = cycle["base"], cycle["caller_rows"]
            extents = [((head+i+256)//256)*256 for i in range(rows)]
            if len(set(extents)) > 1:
                inputs.add(record["input_id"])
                predictions.append(dict(input=record["input_id"],cycle=cycle["cycle"],head=head,extents=extents))
    if predictions:
        selected_boundary=predictions[0]["input"]
        inputs={selected_boundary}
        predictions=[x for x in predictions if x["input"]==selected_boundary]
    if profile == "qwen14b02":
        inputs.update(["GSM8K/test/111", "GSM8K/test/120"])
    inputs.add(panel["inputs"][0]["id"])
    for file in sorted((old / "units/regression/native").rglob("C_QB/native/heavy.json")):
        record=read(file)
        if record["input_id"] not in inputs:continue
        cycles=record["cycles"]
        crosses=[c["cycle"] for c in cycles if c["base"]//256!=(c["base"]+c["caller_rows"]-1)//256]
        near=next((c for c in cycles if c["caller_rows"]==4 and
                   (not crosses or c["cycle"]>max(crosses)) and
                   c["base"]//256==(c["base"]+3)//256),None)
        if near:
            predictions.append(dict(input=record["input_id"],cycle=near["cycle"],head=near["base"],
                             extents=[((near["base"]+256)//256)*256]*4))
    selected = [s for s in slots if s["input_id"] in inputs and s["arm"] in ("R","C_PQ","C_QB") and s["producer"]=="NATIVE" and s["observer"]=="heavy"]
    assert selected
    cfg=read(old/"CONFIG.json")
    build=ROOT/"active03/qwen_config01"
    worker=build/"bin/rtx-scope-transfer.exe"
    binding=read(old/"BINDING.json")
    identity=binding["families"]["Qwen"]
    original=read(old/"ORIGINAL_BINDING.json")
    save(bundle/"RUNTIME_SOURCE.json",{str(f):digest(f) for f in [build/"core/src/libllama.a",worker,build/"worker.cpp",build/"source/src/llama-graph.cpp",build/"source/ggml/src/repair_offload.hpp",build/"source/ggml/src/ggml-backend.cpp",build/"source/src/hs_reference_batching.hpp"]})
    for key in ("target","draft"):
        assert digest(Path(cfg[key]))==original["families"]["Qwen"]["models"][key]["sha256"]
    assert digest(Path(cfg["original_worker"]))==original["families"]["Qwen"]["executable_sha256"]
    for name,h in original["families"]["Qwen"]["numerical_modules"].items():
        assert digest(worker.parent/name)==h
    identity.update(build_receipt_sha256=digest(build/"BUILD.json"),core_sha256=digest(build/"core/src/libllama.a"),executable_sha256=digest(worker),worker_source_sha256=digest(build/"worker.cpp"))
    cfg.update(build_receipt=str(build/"BUILD.json"),worker=str(worker),research_root=str(NEW),request_limit=1200,development_limit=480)
    cfg["resources"].update(total_native_seconds=86400,worker_timeout_seconds=7200)
    for name,data in [("BINDING.json",binding),("ORIGINAL_BINDING.json",original),("PLAN.json",read(old/"PLAN.json")),("CONFIG.json",cfg),("PREDICTIONS.json",dict(boundaries=predictions,ordinary_input=panel["inputs"][0]["id"],normalization={
                "source":"Pinned CUDA MUL offload uses ggml_nrows >= 32; supervisor clears GGML environment overrides.",
                "prediction":("All target layers on GPU: no host-weight placement override." if profile=="qwen8b02" else
                    "On a host-resident layer, K has 8 heads: 8 scalar rows <32, 8*4 batch rows >=32, select scalar false. Q has 40 heads: 40 and 160 both >=32, select true."),
                "target_gpu_layers":binding["dense14b"]["target_gpu_layers"]}))]:
        save(bundle/name,data)
    seal={f.name:digest(f) for f in bundle.iterdir() if f.is_file()}
    save(bundle/"EPOCH.json",seal)
    def check(b):
        for name,h in seal.items():
            assert digest(b/name)==h
        assert digest(worker)==identity["executable_sha256"]
        return cfg
    library.check_epoch=check
    driver,_,source,_=library.driver(cfg["parent_snapshot"],binding)
    anchor="env['CUDA_VISIBLE_DEVICES']"
    assert source.count(anchor)==1
    source=source.replace(anchor,"env['HS_RTX164_TRACE']='1'\n        "+anchor)
    env=dict(driver.__globals__)
    exec(compile(source,"rtx164_focused_supervisor","exec"),env)
    env["run_unit"](bundle,"admission",panel,selected[:1],admit=True)
    env["run_unit"](bundle,"focused",panel,selected)


if __name__=="__main__":
    NEW.mkdir()
    import shutil
    shutil.copyfile(ROOT/"diagnostics03/LEDGER.jsonl",NEW/"LEDGER.jsonl")
    path=PREVIOUS/"benchmarks/rtx_llama_repair_v1/host_execution/qwen_regression.py"
    spec=importlib.util.spec_from_file_location("retained_driver",path)
    library=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(library)
    library.initialize(PREVIOUS)
    for profile in ("qwen8b02","qwen14b02"):
        run(profile,library)
