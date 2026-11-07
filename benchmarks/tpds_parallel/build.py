"""Build a separate llama core from PR166's sealed source and backend cohort."""
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = Path("E:/rtx164/active03/qwen_config01")
OUT = Path("E:/tpds167/build01")

def substitute(path, old, new):
    contents = path.read_text(encoding="utf8")
    if contents.count(old) != 1:
        raise RuntimeError(f"unexpected PR166 source at {path}: {old}")
    path.write_text(contents.replace(old, new), encoding="utf8")

def prepare():
    OUT.mkdir(parents=True, exist_ok=False)
    shutil.copytree(BASE/"source", OUT/"source")
    (OUT/"core").mkdir()
    (OUT/"bin").mkdir()
    for f in [*BASE.glob("*.hpp"), *BASE.glob("*.h"), BASE/"worker.cpp",
              *BASE.joinpath("bin").glob("*.dll"), *BASE.joinpath("core").glob("*.cmd")]:
        shutil.copy2(f, OUT/f.relative_to(BASE))
    src = OUT/"source"
    graph = src/"src/llama-graph.cpp"
    substitute(graph, "t->ne[2] > 4", "t->ne[2] > 32")
    substitute(src/"ggml/src/repair_offload.hpp", "tensor->ne[2] > 4", "tensor->ne[2] > 32")
    substitute(src/"src/hs_reference_batching.hpp", "rows <= 4", "rows <= 32")
    substitute(graph, "prefix.front()!=prefix.back() &&", "(prefix.front()!=prefix.back() || q->ne[2]>4) &&")
    substitute(graph, "for (const auto & planned : groups) {\n            const size_t begin=planned.begin;",
               """// Physical query tiles preserve the validated backend layout. Q, K, V,
        // projection and FFN still belong to the single caller graph.
        for (const auto & run : groups) {
          const size_t tile = hs_scope::layout95()==1 ? 1 : 4;
          for (size_t begin=run.begin; begin<run.end; begin+=tile) {
            auto planned=run; planned.begin=begin;
            planned.end=std::min(run.end,begin+tile);""")
    substitute(graph, "cur=cur?ggml_concat(ctx0,cur,group,1):group;\n        }",
               """if (std::getenv("HS_TPDS_TRACE") && il==0)
                std::fprintf(stderr,"TPDS_TILE base=%d begin=%zu width=%lld extent=%lld\\n",
                    int(ubatch.pos[0]),begin,(long long)width,(long long)extent);
            cur=cur?ggml_concat(ctx0,cur,group,1):group;
          }
        }""")
    substitute(src/"src/llama-kv-cache.h", "uint32_t get_size()     const;",
               "uint32_t get_size()     const;\n    uint32_t scalar_padding() const { return std::max(n_pad,256u); }")

    from wide_ops import apply
    apply(src)

def build(labels):
    commands = json.loads((BASE/"COMMANDS.json").read_bytes())
    for row in commands:
        label = row["label"]
        if label not in labels:
            continue
        args = [s.replace(str(BASE),str(OUT)).replace(BASE.as_posix(),OUT.as_posix()) for s in row["argv"]]
        if label in ("worker","link"):
            args = [s.replace("worker.cpp","probe.cpp").replace("worker.obj","probe.obj").replace("rtx-scope-transfer.exe","probe.exe") for s in args]
            if label=="worker":
                shutil.copy2(HERE/"probe.cpp",OUT/"probe.cpp")
        dest = OUT/f"{label}-{time.time_ns()}"
        with dest.with_suffix(".log").open("xb") as log:
            result=subprocess.run(args, stdout=log, stderr=subprocess.STDOUT,timeout=3600)
        dest.with_suffix(".json").write_text(json.dumps(dict(argv=args,exit_code=result.returncode),indent=2))
        result.check_returncode()

if __name__=="__main__":
    if "prepare" in sys.argv:
        prepare()
    build(sys.argv[1:])
