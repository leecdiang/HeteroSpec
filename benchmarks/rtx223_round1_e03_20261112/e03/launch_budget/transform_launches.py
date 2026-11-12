"""Instrument a NEW private CUDA source copy; old sources are read-only.

The catalog counts source sites, not dynamic launches or physical kernels.
Native arming remains blocked even after every visible site is transformed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

HERE = Path(__file__).resolve().parent


class CoverageError(ValueError):
    pass


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def code_mask(source):
    """Keep positions/newlines, hide comments, chars and ordinary/raw strings."""
    chars=list(source)
    i=0
    while i<len(source):
        end=None
        if source.startswith("//",i):
            end=source.find("\n",i)
            if end<0: end=len(source)
        elif source.startswith("/*",i):
            end=source.find("*/",i+2)
            if end<0: raise CoverageError("Unterminated comment")
            end+=2
        elif source.startswith('R"',i):
            paren=source.find("(",i+2)
            if paren<0 or paren-i>20: raise CoverageError("Unsupported raw string")
            delimiter=source[i+2:paren]
            token=")"+delimiter+'"'
            end=source.find(token,paren+1)
            if end<0: raise CoverageError("Unterminated raw string")
            end+=len(token)
        elif source[i] in ('"', "'"):
            quote=source[i]; j=i+1
            while j<len(source):
                if source[j]=="\\": j+=2; continue
                if source[j]==quote: break
                j+=1
            if j==len(source): raise CoverageError("Unterminated literal")
            end=j+1
        if end is not None:
            for n in range(i,end):
                if chars[n]!="\n": chars[n]=" "
            i=end
        else: i+=1
    return "".join(chars)


def first_grid_comma(mask, start):
    stack=[]
    for i in range(start,len(mask)):
        c=mask[i]
        if c in "([{": stack.append(c)
        elif c in ")]}":
            if not stack: raise CoverageError("Unbalanced launch config")
            stack.pop()
        elif c=="," and not stack:
            return i
        elif c in "<>" and not stack:
            raise CoverageError("Ambiguous template/comparison in first grid expression; manual qualification needed")
    raise CoverageError("Launch config has no first comma")


def call_end(mask, open_paren):
    depth=0
    for i in range(open_paren,len(mask)):
        if mask[i]=="(": depth+=1
        if mask[i]==")":
            depth-=1
            if depth==0: return i+1
    raise CoverageError("Unbalanced call")


LAUNCH_APIS={"cudaLaunchKernel", "cudaLaunchKernelEx", "cudaLaunchKernelExC"}
CALLS=re.compile(r"\b(?:cuda[A-Z][A-Za-z0-9_]*|cu[A-Z][A-Za-z0-9_]*|cublas[A-Z][A-Za-z0-9_]*|nccl[A-Za-z0-9_]+|cub::Device[A-Za-z0-9_:]+)\s*\(")


def classify(name):
    if name in LAUNCH_APIS: return "prelaunch-api"
    if name.startswith(("cudaGraph", "cudaStreamBeginCapture", "cudaStreamEndCapture", "cudaLaunch", "cudaStreamAddCallback", "cublas", "nccl", "cub::Device", "cu")):
        # The final 'cu' includes runtime calls too. Selected memory APIs are
        # denied explicitly; all other CUDA runtime activity remains unknown.
        if name.startswith(("cuLaunch", "cuGraph", "cublas", "nccl", "cub::Device", "cudaGraph", "cudaStreamBeginCapture", "cudaStreamEndCapture", "cudaLaunch", "cudaStreamAddCallback", "cudaMemset", "cudaMemcpy")):
            return "deny-opaque"
        if name.startswith("cu") and not name.startswith("cuda"):
            return "deny-opaque-driver"
    return "runtime-call-unqualified"


def transform_text(source, relative):
    mask=code_mask(source); edits=[]; rows=[]
    for match in re.finditer(r"<<<",mask):
        comma=first_grid_comma(mask,match.end())
        line=source.count("\n",0,match.start())+1
        site=f"{relative}:{line}:raw"
        edits.append((match.end(), '(hs_launch_budget_before_launch_v1('+json.dumps(site)+'), '))
        edits.append((comma, ")"))
        rows.append({"kind":"prelaunch-raw", "line":line,"site":site,"grid_expression":source[match.end():comma]})
    for match in CALLS.finditer(mask):
        name=mask[match.start():match.end()].split("(")[0].strip()
        kind=classify(name)
        line=source.count("\n",0,match.start())+1
        site=f"{relative}:{line}:{name}"
        rows.append({"kind":kind,"line":line,"api":name,"site":site})
        if kind=="runtime-call-unqualified": continue
        end=call_end(mask,mask.find("(",match.start(),match.end()))
        guard="hs_launch_budget_before_launch_v1" if kind=="prelaunch-api" else "hs_launch_budget_deny_opaque_v1"
        edits.append((match.start(), "("+guard+"("+json.dumps(site)+"), "))
        edits.append((end,")"))
    for position, insertion in sorted(edits, key=lambda x:x[0], reverse=True):
        source=source[:position]+insertion+source[position:]
    if edits:
        source='#include "hs_launch_budget.hpp"\n'+source
    return source, rows


def transform_tree(root, output):
    root=Path(root).resolve(); output=Path(output).resolve()
    if not root.is_dir() or not (root/"ggml-cuda.cu").is_file():
        raise CoverageError("Actual new CUDA source directory missing")
    if not root.is_relative_to(HERE.parents[1]):
        raise CoverageError("Refuse modification outside this new e03 workspace")
    if output.exists(): raise FileExistsError(output)
    files=[p for p in root.rglob("*") if p.suffix in (".cu",".cuh",".h",".hpp",".cpp") and p.name not in ("hs_launch_budget.cu","hs_launch_budget.hpp")]
    catalog=[]; pending=[]
    for p in sorted(files):
        raw=p.read_bytes(); relative=p.relative_to(root).as_posix()
        if "hs_launch_budget_before_launch_v1" in raw.decode("utf8"):
            raise CoverageError("Already instrumented source; no second transform")
        text, rows=transform_text(raw.decode("utf8"),relative)
        if rows:
            catalog.append({"path":relative,"before_sha256":digest(raw),"after_sha256":digest(text.encode()),"sites":rows})
        if text.encode()!=raw: pending.append((p,text.encode()))
    # Validate whole tree before any mutation; failure leaves original new copy unchanged.
    for p,data in pending: p.write_bytes(data)
    shutil.copy2(HERE/"hs_launch_budget.hpp",root/"hs_launch_budget.hpp")
    shutil.copy2(HERE/"hs_launch_budget.cpp",root/"hs_launch_budget.cu")
    summary={kind:sum(s["kind"]==kind for f in catalog for s in f["sites"]) for kind in ("prelaunch-raw","prelaunch-api","deny-opaque","deny-opaque-driver","runtime-call-unqualified")}
    result={"schema":"heterospec.launch-source-catalog.v1","root":str(root),"files":catalog,"counts_of_source_sites_only":summary,
            "native_armed":False,"all_physical_kernels_qualified":False,"dynamic_launches_measured":0,
            "opaque_runtime_work":"UNKNOWN; numeric backend admission remains blocked",
            "same_policy_required_for":["A","B","C","draft","reference"],
            "required_build_options":{"GGML_CUDA_GRAPHS":"OFF","GGML_CUDA_NCCL":"OFF","GGML_CUDA_NO_VMM":"ON"}}
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(result,indent=2),encoding="utf8")
    return result


if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--new-cuda-source",type=Path,required=True); ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args(); result=transform_tree(a.new_cuda_source,a.out)
    print(json.dumps({"catalog":str(a.out),"counts":result["counts_of_source_sites_only"],"native_armed":False}))
