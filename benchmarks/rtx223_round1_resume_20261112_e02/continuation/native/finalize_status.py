from pathlib import Path
import hashlib,json

HERE=Path(__file__).resolve().parent
def read(p):return json.loads((HERE/p).read_bytes())
checks={'capture_header':read('capture-build-v1/BUILD.json'),
        'MMVQ_TU':read('backend-build-v1/BUILD.json'),
        'operator_v3':read('operator-v3/build-v1/BUILD.json'),
        'CPU_launch_accounting':read('host-accounting-v1/RECEIPT.json')}
receipt={'schema':'heterospec.e02.native-preparation-status.v1','status':'PREPARATION_COMPLETE_NATIVE_BLOCKED',
    'decision':'INCONCLUSIVE','model_requests':0,'target_rows':0,'draft_rows':0,'CUDA_contexts':0,'kernel_launches':0,
    'native_qualification_cells':66,'all_native_results':'NOT_RUN','actual_q8_operand':'NOT_RUN',
    'A_B_C_original_path_bytes':'NOT_RUN','paired_operator_timing':'NOT_RUN','actual_occupancy':'unknown','DRAM_L2':'unknown',
    'host_compile_results':{k:v.get('returncode',v.get('run_returncode')) for k,v in checks.items()},
    'CPU_native_accounting_cases':checks['CPU_launch_accounting']['result']['cases'],
    'no_new_numerical_DLL_link_or_load':True,'original_source_and_DLLs_unchanged':True,
    'launch_accounting_scope':'standalone explicit quantizer/MMVQ sites only; not full model',
    'full_model_kernel_cap':'NOT_IMPLEMENTED',
    'remaining_gates':['authoritative no-overlap evidence','all-model-kernel prelaunch cap','backend hook link/binary binding/native qualification','actual q8 capture and all 66 native obligations'],
    'receipt_files':{p:hashlib.sha256((HERE/p).read_bytes()).hexdigest() for p in [
        'capture-build-v1/BUILD.json','backend-build-v1/BUILD.json','operator-v3/build-v1/BUILD.json','host-accounting-v1/RECEIPT.json','NATIVE_MATRIX.json']}}
(HERE/'STATUS.json').write_text(json.dumps(receipt,indent=2),encoding='utf8');print(json.dumps(receipt))
