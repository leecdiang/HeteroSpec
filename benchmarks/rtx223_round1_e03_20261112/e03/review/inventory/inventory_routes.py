"""Read-only lexical CUDA route inventory. Counts are never dynamic coverage."""
from pathlib import Path
import collections
import datetime
import hashlib
import json
import re

SOURCE = Path("D:/rtx192-review-v2/native-v2/cores/packed/ggml/src/ggml-cuda")
OUT = Path(__file__).resolve().parent


def strip_literals(text):
    """Blank comments/literals, preserving offsets and newlines; no preprocessing."""
    result = list(text)
    n, i = len(text), 0
    def blank(a, b):
        for j in range(a, min(b, n)):
            if text[j] != "\n":
                result[j] = " "
    while i < n:
        if text.startswith("//", i):
            end = text.find("\n", i)
            end = n if end < 0 else end
            blank(i, end); i = end
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            end = n if end < 0 else end + 2
            blank(i, end); i = end
        elif text.startswith('R"', i):
            opening = text.find("(", i + 2)
            if opening < 0:
                i += 1; continue
            delimiter = text[i + 2:opening]
            end = text.find(")" + delimiter + '"', opening + 1)
            end = n if end < 0 else end + len(delimiter) + 2
            blank(i, end); i = end
        elif text[i] in ('"', "'"):
            quote, start = text[i], i
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                elif text[i] == quote:
                    i += 1; break
                else:
                    i += 1
            blank(start, i)
        else:
            i += 1
    return "".join(result)


RULES = {
    "raw_cuda_launch_syntax": re.compile(r"<<<"),
    "ggml_launch_wrapper_lexical_occurrences": re.compile(r"\bggml_cuda_kernel_launch\s*(?:<[^;{}]*?>)?\s*\("),
    "cuda_launch_api": re.compile(r"\b(?:cudaLaunch\w*|cuLaunch\w*)\s*\("),
    "cuda_graph_api": re.compile(r"\b(?:cudaGraph\w*|cudaStreamBeginCapture\w*|cudaStreamEndCapture\w*)\s*\("),
    "cublas_api": re.compile(r"\bcublas\w+\s*\("),
    "cub_host_device_algorithm": re.compile(r"\bcub::Device\w+::\w+\s*\("),
    "thrust_api": re.compile(r"\bthrust::\w+\s*\("),
    "nccl_api": re.compile(r"\bnccl\w+\s*\("),
    "other_gpu_library_api": re.compile(r"\b(?:cudnn\w+|cusparse\w+|cufft\w+|curand\w+|nvshmem\w*)\s*\("),
    "runtime_memset_api": re.compile(r"\bcudaMemset\w*\s*\("),
    "runtime_allocation_api": re.compile(r"\b(?:cudaMalloc\w*|cudaFree\w*|cuMem\w*)\s*\("),
}


def main():
    OUT.mkdir(exist_ok=True)
    sites, bound_files = [], []
    for p in sorted(SOURCE.rglob("*")):
        if not p.is_file() or p.suffix not in (".cu", ".cuh", ".cpp", ".hpp", ".h"):
            continue
        raw = p.read_bytes()
        text = raw.decode("utf8")
        code = strip_literals(text)
        relative = str(p.relative_to(SOURCE)).replace("\\", "/")
        matched = False
        for category, pattern in RULES.items():
            for m in pattern.finditer(code):
                line = code.count("\n", 0, m.start()) + 1
                snippet = text.splitlines()[line - 1].strip()
                sites.append({"category": category, "file": relative, "line": line, "token": m.group().strip(), "source_line": snippet[:420]})
                matched = True
        if matched:
            bound_files.append({"path": relative, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    counts = collections.Counter(s["category"] for s in sites)
    result = {
        "schema": "heterospec.e03.independent-cuda-route-inventory.v1",
        "observed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_root": str(SOURCE),
        "scope": "Pinned original source, lexical occurrences with comments and strings removed",
        "counts": dict(sorted(counts.items())),
        "source_file_bindings": bound_files,
        "sites": sorted(sites, key=lambda x: (x["file"], x["line"], x["category"])),
        "limits": [
            "No C++ preprocessing, template instantiation or runtime execution occurred",
            "Inactive HIP/MUSA/NCCL/graph branches and function declarations/definitions may remain in lexical counts",
            "A lexical wrapper occurrence is not one dynamic launch; loops and library calls can issue variable work",
            "Included CUDA toolkit/library headers are not instrumented by this inventory",
            "Runtime memory API occurrences do not establish whether or how many physical kernels execute internally",
            "Block-level cub::BlockScan inside an owned kernel is distinct from host cub::DeviceScan launch-producing APIs",
            "No static count here qualifies the complete 4096 physical-kernel budget"
        ],
        "model_requests": 0,
        "CUDA_calls": 0,
        "kernel_launches": 0,
        "dynamic_full_coverage": "NOT_ESTABLISHED"
    }
    (OUT / "CUDA_ROUTE_INVENTORY.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    print(json.dumps({"counts": result["counts"], "bound_files": len(bound_files), "dynamic_full_coverage": result["dynamic_full_coverage"]}, indent=2))


if __name__ == "__main__":
    main()
