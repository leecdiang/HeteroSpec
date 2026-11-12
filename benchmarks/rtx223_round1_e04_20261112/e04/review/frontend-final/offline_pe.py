"""Offline MSVC disk inspection; never invokes target EXE or LoadLibrary."""
from pathlib import Path
import argparse
import datetime
import json
import re
import subprocess
from independent_common import need, sha, identity

DUMPBIN = Path('D:/rtx184-tools/msvc/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/dumpbin.exe')
HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('target', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--bytes', required=True, type=int)
    parser.add_argument('--native', action='store_true')
    args = parser.parse_args()
    need(args.output.resolve().is_relative_to(HERE), 'only own audit output directory allowed')
    need(not args.output.exists(), 'fresh PE output directory required')
    need(sha(args.target) == args.sha256 and args.target.stat().st_size == args.bytes, 'target identity differs')
    args.output.mkdir(parents=True)
    runs, texts = [], {}
    for switch in ('headers', 'imports', 'exports'):
        argv = [str(DUMPBIN), '/nologo', '/' + switch, str(args.target.resolve())]
        completed = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
        raw = args.output / (switch + '.txt')
        raw.write_bytes(completed.stdout)
        need(completed.returncode == 0, 'offline dumpbin failed: ' + switch)
        texts[switch] = completed.stdout.decode('utf8', errors='replace')
        runs.append({'argv': argv, 'returncode': completed.returncode, 'raw': identity(raw)})
    need(sha(args.target) == args.sha256 and args.target.stat().st_size == args.bytes, 'target changed during PE disk inspection')
    exports = re.findall(r'^\s*\d+\s+[0-9A-Fa-f]+\s+[0-9A-Fa-f]{8}\s+(\S+)', texts['exports'], re.M)
    imports = sorted(set(re.findall(r'^\s*([A-Za-z0-9_.-]+\.dll)\s*$', texts['imports'], re.I | re.M)), key=str.lower)
    need(re.search(r'8664 machine \(x64\)', texts['headers'], re.I), 'not AMD64 PE')
    is_dll = re.search(r'^\s*DLL\s*$', texts['headers'], re.M) is not None
    required = {'hs_e03_runtime_metadata', 'hs_e03_select_arm', 'hs_e03_selected_arm',
                'hs_e03_pair4_dispatches', 'hs_e03_packed_dispatches', 'hs_e03_loop4_dispatches',
                'hs_launch_budget_configure_v1', 'hs_launch_budget_try_v1', 'hs_launch_budget_before_launch_v1',
                'hs_launch_budget_deny_opaque_try_v1', 'hs_launch_budget_deny_opaque_v1',
                'hs_launch_budget_snapshot_v1', 'hs_launch_budget_metadata_v1'} if args.native else set()
    need(not (required - set(exports)), 'required runtime/budget export absent')
    need('hs_launch_budget_test_reentry_v1' not in exports, 'CPU-only reentry export in numeric target')
    if args.native:
        need(is_dll, 'native target is not PE DLL')
        need({'ggml-base.dll', 'cudart64_12.dll', 'cublas64_12.dll'} <= {x.lower() for x in imports}, 'expected numerical import absent')
    symbols = sorted(set(re.findall(r'\b(?:__cuda\w+|cuda\w+|cublas\w+)\b', texts['imports'])))
    result = {'schema': 'heterospec.e04.independent-offline-PE.v1', 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'verdict': 'PASS_PE_DISK_IDENTITY_ONLY_NATIVE_GATES_REMAIN_CLOSED', 'target': identity(args.target),
              'trusted_parser': identity(DUMPBIN), 'runs': runs, 'machine': 'AMD64', 'is_DLL': is_dll,
              'all_exports': exports, 'required_runtime_budget_exports_present': sorted(required), 'imported_DLLs': imports,
              'CUDA_library_import_symbols': symbols, 'scope': 'Only disk PE metadata parsed by dumpbin. Target entrypoint/CRT/TLS/fatbinary initialization was not run; exports not called; normal load remains unqualified.',
              'producer_verifier_imported': False, 'target_EXE_runs': 0, 'target_LoadLibrary_calls': 0, 'CUDA_calls': 0,
              'models': 0, 'GPU_launches': 0, 'numerical_qualification': False, 'physical_kernel_budget_qualification': False}
    receipt = args.output / 'PE_RECEIPT.json'
    receipt.write_text(json.dumps(result, indent=2), encoding='utf8')
    print(json.dumps({'target': result['target'], 'receipt': str(receipt), 'receipt_sha256': sha(receipt), 'DLLs': imports, 'exports': len(exports)}, indent=2))


if __name__ == '__main__':
    main()
