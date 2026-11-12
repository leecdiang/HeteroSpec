"""Additive dynamic-schedule source preparation; no compiler/model/GPU calls.

This deliberately does not claim full request qualification. Historical host
bindings do not authorize the new per-cycle policy. Draft snapshots, owner
poison and timing hooks remain integration gates; see PROTOCOL.md.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

PARENT_SHA = "0bf9920d135fab66d15c5c2d81d25fcbdb90d525b281ef20b8beea384f181096"


def once(s, old, new):
    if s.count(old) != 1:
        raise ValueError("source anchor not unique: " + old[:80])
    return s.replace(old, new, 1)


def transform(s):
    s = once(s, "    const auto& arm=spec.name;int k=spec.k;", """    const auto& arm=spec.name;int k=spec.k;
    // A frozen per-cycle schedule is a path-qualification control, not an
    // adaptive policy. No k is selected from an observed acceptance outcome.
    const auto cycle_k=input.value("cycle_k",std::vector<int>{});
    int max_k=k;
    for(int candidate_k:cycle_k){need(candidate_k==3||candidate_k==7,"unsupported cycle k");max_k=std::max(max_k,candidate_k);}
    need(cycle_k.empty()||phase_target_reserve>=max_k+1,"dynamic schedule output reserve");""")
    s = once(s, "input.at(\"cap\").get<int>())+size_t(k+1)<=llama_n_ctx", "input.at(\"cap\").get<int>())+size_t(max_k+1)<=llama_n_ctx")
    s = once(s, "    while(!done){", """    while(!done){
        if(!cycle_k.empty()){need(size_t(cycle)<cycle_k.size(),"frozen cycle schedule exhausted");k=cycle_k.at(size_t(cycle));}""")
    s = once(s, "{{\"cycle\",cycle},{\"base\",base}", "{{\"cycle\",cycle},{\"k\",k},{\"base\",base}")
    return s


def prepare(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError("fresh source output required")
    old = (source / "worker.cpp").read_bytes()
    if hashlib.sha256(old).hexdigest() != PARENT_SHA:
        raise ValueError("qualified Windows frontend-v2 source SHA changed")
    new = transform(old.decode("utf8"))
    shutil.copytree(source, output)
    (output / "worker.cpp").write_text(new, encoding="utf8", newline="\n")
    record = {"status": "SOURCE_PREPARED_NOT_BUILT_NOT_QUALIFIED", "parent_worker_sha256": PARENT_SHA,
              "parent": str(source), "output": str(output),
              "files": {str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in output.iterdir() if p.is_file()},
              "model_requests": 0, "native_GPU_launches": 0,
              "unresolved": ["new entry admission and exact frozen schedule identity",
                             "complete target and draft untrimmed/trimmed snapshots",
                             "native placement/dispatch and graph guards",
                             "transaction-wide owner poison",
                             "same-request host cost integration", "independent scalar R bridge"]}
    (output.parent / (output.name + "_PREPARATION.json")).write_text(json.dumps(record, indent=2), encoding="utf8")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("output")
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.output), indent=2))
