import pathlib,sys,struct,hashlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from common import read,save,need,file_hash
root=pathlib.Path(sys.argv[1]);manifest=read(sys.argv[2]);out=pathlib.Path(sys.argv[3]);result=read(root/'native/RESULT.json');receipt=read(root/'RECEIPT.json');need(receipt['success'] and receipt['active_processes_after_wait']==0,'replay cleanup')
rows={};inventory=[]
for x in result['results']:
    p=root/'native'/x['output'];b=p.read_bytes();need(len(b)==x['bytes'],'output size');rows[x['operand'],x['backend'],x['repetition']]=b;inventory.append(dict(x,sha256=file_hash(p)))
need(len(rows)==8,'all eight runs retained')
repeat=all(rows[o,b,0]==rows[o,b,1] for o in ['R','C_QB'] for b in ['CPU','CUDA0'])
expected={x['name']:pathlib.Path(x['expected_file']).read_bytes() for x in manifest['operands']}
own_cpu=rows['R','CPU',0]==expected['R'];own_cuda=rows['C_QB','CUDA0',0]==expected['C_QB'];n=128*8*4
cross_cpu=rows['C_QB','CPU',0][:n]==expected['R'];cross_cuda=rows['R','CUDA0',0]==expected['C_QB'][:n]
cpu=struct.unpack('<1024f',rows['R','CPU',0]);gpu=struct.unpack('<1024f',rows['R','CUDA0',0]);difference=sum(a!=b for a,b in zip(cpu,gpu));maximum=max(abs(a-b) for a,b in zip(cpu,gpu))
passed=repeat and own_cpu and own_cuda and cross_cpu and cross_cuda and difference>0
report={'status':'SAME_OPERAND_BACKEND_DIVERGENCE_REPRODUCED' if passed else 'REPLAY_NOT_ESTABLISHED','repeatable':repeat,'native_R_CPU_full_output_reproduced':own_cpu,'native_C_CUDA_full_output_reproduced':own_cuda,'same_four_row_operand_CPU_row0_equals_R':cross_cpu,'same_one_row_operand_CUDA_equals_C_row0':cross_cuda,'different_float_elements_of_1024':difference,'max_absolute_difference':maximum,'inventory':inventory,'manifest_sha256':file_hash(sys.argv[2]),'result_sha256':file_hash(root/'native/RESULT.json'),'model_requests':0,'operator_replays':8,'reserved_budget_charge':8,'scope':'Pinned native CPU and CUDA RoPE on identical captured normalized K and position; full own-path replay established before counterfactual backend comparison. No whole-model repair success inferred.'}
save(out,report,exclusive=True);print(report['status'],difference,maximum)
