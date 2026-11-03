"""Bind the built worker and original DLL cohort before any diagnostic output."""
import json
from pathlib import Path
from focused import ROOT, digest, read, save


def main():
    for cohort in ("config06","qwen_config01"):
        build=ROOT/"active03"/cohort
        original=Path("E:/rtx160")/cohort/"build"
        modules=read(original/"BUILD.json")["numerical_modules"]
        assert all(digest(build/"bin"/name)==h for name,h in modules.items())
        commands=read(build/"COMMANDS.json")
        assert [c["label"] for c in commands]==["configure","core","worker","link"]
        assert all(c["exit_code"]==0 for c in commands)
        source=read(build/"source/SHARED_PLANNER_SOURCE.json")
        assert source["backend"]=="cuda"
        for name,pin in source["files"].items():
            assert digest(build/"source"/name)==pin["after_sha256"]
        save(build/"BUILD.json",dict(cohort=cohort,commands=commands,numerical_modules=modules,
             executable_sha256=digest(build/"bin/rtx-scope-transfer.exe"),worker_source_sha256=digest(build/"worker.cpp"),
             core_sha256=digest(build/"core/src/libllama.a"),source=source))


if __name__=="__main__":
    main()
