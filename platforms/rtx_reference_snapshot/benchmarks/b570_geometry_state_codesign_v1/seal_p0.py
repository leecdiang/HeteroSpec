"""Freeze execution review inputs after all actual CPU gates; no native launch."""
from pathlib import Path
import json,platform,sys,zipfile,hashlib,subprocess
from protocol import *
import run_p1
ROOT=Path(__file__).resolve().parent
P0=ROOT/'p0'
def pin(p):return dict(path=str(p.relative_to(ROOT)).replace(chr(92),'/'),bytes=p.stat().st_size,sha256=file_sha(p))
def main():
 require(read_json(P0/'BUILD_EXECUTION_EXIT.json')['code']==0,'final build incomplete')
 plan=read_json(P0/'PLAN_P1.json');runtime=read_json(P0/'RUNTIME.json');validate_plan(plan)
 require(read_json(P0/'SERIALIZER_ADMISSION.json')['runtime_sha256']==digest(runtime),'serializer runtime stale')
 log=(P0/'CPU_FINAL.log').read_text(encoding='utf-8');require('Ran 104 tests' in log and log.rstrip().endswith('OK'),'final CPU tests incomplete')
 require('checks=49' in (P0/'CPU_GRAPH_FINAL.log').read_text(),'native CPU graph checks')
 require('PASS SYNTHETIC_CPU_ONLY' in (P0/'CPU_NUMERIC.log').read_text(),'synthetic CPU numeric checks')
 require(not (ROOT/'_host/run/LEDGER.jsonl').exists(),'P0 must not have a real model ledger')
 status=run_p1.busy_gate();status.update(phase='P0',model_process_attempts=0,model_request_starts=0,GPU_forward_starts=0,operator_starts=0,owned_model_seconds=0,scientific_raw_output_bytes=0)
 write_new(P0/'HOST_STATUS.json',status)
 write_new(P0/'UNSTARTED_P1.json',[{k:s[k] for k in ('slot','task','arm','session','mode','stage')} for s in plan['slots']])
 source=[pin(p) for p in sorted(ROOT.glob('*.py'))]+[pin(p) for p in sorted((ROOT/'native').glob('*')) if p.is_file()]+[pin(ROOT/n) for n in ('README.md','PROTOCOL.md','NATIVE_INTEGRATION.md','AGENT_HANDOFF.md','ARCHITECTURE.md','SOURCE_LOCK.json')]
 source+=runtime['isolated_llama_source_files']
 # New source/binary capsule excludes weights, credentials, old raw and external driver bodies.
 capsule_files=[ROOT/x['path'] for x in runtime['isolated_llama_source_files']]+[ROOT/'_host/build/Release'/n for n in ('llama-b570-memory.dll','llama-b570-memory.lib','b570-geometry-worker.exe','graph-contract-cpu.exe','graph-numeric-cpu.exe')]
 archive=P0/'NATIVE_P0_CAPSULE.zip';manifest=[pin(p) for p in capsule_files]
 with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  z.writestr('MANIFEST.json',encode(manifest))
  for p,x in zip(capsule_files,manifest):z.write(p,x['path'])
 # Fresh, independent reconstruction/hash of every archived member.
 destination=ROOT/'_host/capsule_restore';require(not destination.exists(),'fresh capsule restore required')
 with zipfile.ZipFile(archive) as z:
  require(set(z.namelist())=={'MANIFEST.json'}|{x['path'] for x in manifest},'capsule inventory')
  for x in manifest:
   data=z.read(x['path']);require(len(data)==x['bytes'] and hashlib.sha256(data).hexdigest()==x['sha256'],'capsule member hash');p=destination/x['path'];require(p.resolve().is_relative_to(destination.resolve()),'capsule escape');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 for x in manifest:require(file_sha(destination/x['path'])==x['sha256'],'fresh restored file hash')
 write_new(P0/'CAPSULE_RESTORE.json',dict(status='PASS_FRESH_LOCAL_RESTORE',archive=pin(archive),members=len(manifest),native_starts=0,external_dependencies='Original PR97 fixed CAS and exact model/driver files bound separately; no model weights included'))
 cache=(ROOT/'_host/build/CMakeCache.txt').read_text(encoding='utf-8')
 compiler=[line for line in cache.splitlines() if line.startswith(('CMAKE_CXX_COMPILER:','CMAKE_GENERATOR:','CMAKE_GENERATOR_TOOLSET:','CMAKE_VS_PLATFORM_TOOLSET_HOST_ARCHITECTURE:'))]
 build=dict(status='COMPILED_AND_CPU_CHECKED_NOT_GPU_EXECUTED',integration_rounds=1,integration_round_scope='PR97 transaction + PR101 final-only natural prefill semantics + graph/phase/serializer/evidence/accounting',maximum_integration_rounds=2,compiler_cache_fields=compiler,compiler_identification='MSVC 19.44.35228; toolset 14.44.35207; Windows SDK10.0.26100.0',build_configuration='x64 Release',Vulkan_SDK='1.4.357.0',numeric_GGML_backend_SHA256_unchanged=True,changed_native_source=['llama-context.cpp','llama-context.h','llama-graph.cpp','worker.cpp','local_attention.h','transaction_contract.h'],arithmetic_shader_changes=False,source_files=source,python=sys.version,platform=platform.platform(),CPU_suites=dict(original=70,new=34,total=104,graph_structure_and_terminal_checks=49,synthetic_numeric_element_comparisons=40960,synthetic_numeric_max_abs_difference=8.76584e-6),capsule=pin(archive))
 write_new(P0/'BUILD_MANIFEST.json',build)
 fields=dict(request='REQUEST.wire exact immutable admitted bytes + LAUNCH argv; native echo normalized108 only new runtime; originalR reconstructed against source-bound caller and actual_condition',endpoint='Exact unique native stdout RESULT ids/eog/length/terminal_id/stop_reason/cap',identity='External owned-PID EnumProcessModulesEx full loaded paths+SHA256; raw WEIGHT_MAP/context and native KV placement stderr',lifecycle='Durable pre-Popen PROCESS_ATTEMPT then PID, GetProcessTimes and exit; Popen failures remain charged',forward='New worker FORWARD_START/FORWARD_RETURN + result actual target/draft_decode_calls; old R success result counters; partial failed oldR forwards remain UNKNOWN',physical_work='Native successful micrograph integer counters, separate graph/row/width histograms; not shader dispatches',ordered_trace='Diagnostic-only per-context vector at successful native micrograph counter point; never expanded from histogram',VERIFY_witness='Diagnostic target trace phase VERIFY, caller rows, all requested absolute logits positions, real ordered micrograph widths and source/runtime hash',state='Diagnostic before/after sequence serialization bytes independently compared; full initial FP32 payload hash and greedy first decision; cross-original-R logical KV identity UNKNOWN',timer='Original and candidate native_request_ms from before reset through prefill/decode/reconciliation/end sync and safety stop; original R source audit retained; loading separate',unobserved=['backend dispatch','XMX utilization','DRAM bytes','cache hits','completed GPU kernel time','continuous physical residency','full arithmetic DAG'])
 write_new(P0/'RAW_FIELD_SOURCES.json',fields)
 f0=dict(schema=1,status='P0_COMPLETE_PENDING_AUTHOR_CONFIRMATION',design_commit='8d7b85d8aac6e546ca23e1f8a6ad353ea7ed2e02',phase='P1',authorization=False,author_confirmation_required=True,plan_sha256=digest(plan),runtime_sha256=digest(runtime),wires_sha256=file_sha(P0/'WIRES_P1.json'),budget=plan['budget'],limits=run_p1.LIMITS,source_files=source,build_manifest_sha256=file_sha(P0/'BUILD_MANIFEST.json'),raw_field_sources_sha256=file_sha(P0/'RAW_FIELD_SOURCES.json'),capsule_sha256=file_sha(archive),slots_total=80,execution_order=[['old_reference',8],['reference_shadow_counts',4],['reference_shadow_diagnostic',4],['candidate_counts',32],['candidate_diagnostic',32]],counts_observation=dict(heavy_capture=False,API_dump=False,GPU_timestamp_queries=False,added_observation_synchronization=False,successful_integer_work_counters=True,per_caller_forward_lifecycle_events=True),safety_sampling='Signed same-PID B570 dedicated budget/usage host-properties sample every100ms during requests + load/admission checkpoints. Host RAM/disk/time watcher100ms from process creation. Not GPU timestamp queries; sampled, not continuous residency.',diagnostic_capture='Only initial target/draft full FP32 logits; same-context before/after handoff sequence bytes for candidates; bounded caller/VERIFY/micrograph records; no operator payload dump, per-token logits, API dump or new GPU queries.',reference='Original restored PR92 executable e53fa399... + original llama and numeric DLLs, ordinary UB128/capacity1. R_SHADOW only rebuilt identity control.',effective_k_native_mapping='No-draft effective_k0 is sent to fixed legacy native argv k1; candidates effective_k1/argv1.',failure_policy='No retries, probes, implicit warmup, operator starts or automatic resume. Invalid controls/infrastructure stop; valid candidate/reference endpoint mismatches persist and safe planned arms continue; observer endpoint mismatch stops.',P0_actual=status,actual_GPU_geometry='NOT_OBSERVED_P0',new_native_results_qualified=False,performance_aggregate='WITHHELD',P2_authorization=False,P3_authorization=False,hardware_stage1='HOLD_MISSING_EVIDENCE',holdout_exposure='P2 not prepared; EXPOSURE_NOT_ESTABLISHED; four P1 sentinels explicitly exposed')
 write_new(P0/'F0_EXECUTION.json',f0)
 print(json.dumps(dict(F0_sha256=file_sha(P0/'F0_EXECUTION.json'),native_starts=0,capsule_bytes=archive.stat().st_size)))
if __name__=='__main__':main()
