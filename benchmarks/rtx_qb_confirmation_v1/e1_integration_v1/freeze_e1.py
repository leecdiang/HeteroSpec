"""Bind complete E1 source/toolchain/runtime/driver/inputs before native starts."""
from pathlib import Path
import shutil
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import experiment as e

ROOT=Path('D:/hs104-e1-v1');HERE=Path(__file__).parent
def main():
    e.require(not (ROOT/'RUN_STARTED.json').exists() and not (ROOT/'ledger').exists(),'E1 already started')
    e.require(e.read(ROOT/'CPU-tests/RESULT.json')['status']=='PASS','actual native selector CPU gate failed')
    for name in ('NATIVE_BUILD.json','PLAN.json','SOURCE_HASHES.json','PARENT_SOURCE_HASHES.json','configure-ATTEMPT.json','build-ATTEMPT.json'):
        shutil.copyfile(ROOT/name,HERE/name)
    shutil.copyfile(ROOT/'CPU-tests/RESULT.json',HERE/'CPU_NATIVE_SELECTOR_RESULT.json')
    e.require('Ran 10 tests' in (HERE/'CPU_TESTS_FINAL.log').read_text() and (HERE/'CPU_TESTS_FINAL.log').read_text().strip().endswith('OK'),'adapter/orchestration CPU tests failed')
    old=e.read(Path('D:/hs-qb-confirmation-v02/FREEZE.json'));paths={Path(x['path']) for x in old['files']}
    # Includes complete inherited Python/helper/model/driver identities, plus the
    # private generated full C++ source inventory and complete actual driver body.
    paths.update(p for p in (ROOT/'native/source').rglob('*') if p.is_file())
    paths.update(p for p in HERE.iterdir() if p.is_file())
    paths.update(ROOT/name for name in ('PLAN.json','NATIVE_BUILD.json','SOURCE_HASHES.json','PARENT_SOURCE_HASHES.json',
                                      'MODEL_CONTRACT.json','COUNTER_SEMANTICS.md','HOST.json','configure-ATTEMPT.json','build-ATTEMPT.json'))
    paths.update(p for p in (ROOT/'CPU-tests').iterdir() if p.is_file())
    paths.update(p for p in (ROOT/'generated').iterdir() if p.is_file())
    paths.update(ROOT/'native/build/bin'/name for name in e.read(ROOT/'NATIVE_BUILD.json')['numerical_DLL_sha256'])
    paths.update(ROOT/'native/build/bin'/name for name in ('llama-server.exe','querylayout-replay.exe'))
    paths.update(ROOT/'native/build'/name for name in ('CMakeCache.txt','build.ninja','compile_commands.json'))
    asset=Path('D:/HeteroSpec-PC')
    paths.update(asset/rel for rel in ('.venv-analysis/Lib/site-packages/ziglang/zig.exe','.venv-analysis/Lib/site-packages/cmake/data/bin/cmake.exe',
                                      '.venv-analysis/Scripts/ninja.exe','scripts/debug/cuda_divergence/zig-ar.cmd','scripts/debug/cuda_divergence/zig-ranlib.cmd'))
    paths.update(Path(sys.executable).parent/name for name in ('python312.dll','python3.dll'))
    paths.add(Path('D:/hs-qb-confirmation-v02/exact_restoration_20261015/E2_ANALYSIS.json'))
    for item in old['files']:
        path=Path(item['path']);e.require(e.sha(path)==item['sha256'] and path.stat().st_size==item['bytes'],'old fixed identity changed: '+str(path))
    result=dict(schema=1,status='PROSPECTIVE_NATIVE_E1_FREEZE',utc=e.utc(),baseline=e.BASELINE_COMMIT,
                E2_scientific_F0='49b992b2ed1cabd05fad6e234cad2d3418c2b65a',
                E2_restoration_registration='c51354bb19061ed3863cb457068dc727aa46d8ab',
                E2_completed=True,E2_time_and_output_gate='PASS',
                contexts=72,model_request_cap=216,standalone_operator_cap=432,native_worker_cap=72,combined_native_owned_seconds_cap=21600,
                all_model_requests_including_warmups_charged=True,scientific_retry=False,
                numerical_DLLs_same_as_E2=True,selectors_pass_real_sanitizer_serializer_and_native_CPU_test=True,
                kernel_identity='UNKNOWN',reduction_tree='UNKNOWN',
                files=[e.pin(p) for p in sorted(paths,key=str)])
    e.save(ROOT/'FREEZE.json',result)
    e.save(HERE.parent/'registration/E1_F0.json',result)
    print('E1 prospective freeze:',len(result['files']),'files; zero native E1 starts')
if __name__=='__main__':main()
