from common import *
exe=R/'build/Release/b570-memory-worker.exe';q6='Meta-Llama-3.1-8B-Instruct-Q6_K.gguf';q8='Meta-Llama-3.1-8B-Instruct-Q8_0.gguf';d4='Llama-3.2-1B-Instruct-Q4_K_M.gguf';d8='Llama-3.2-1B-Instruct-Q8_0.gguf'
base=['STANDARD_Q6',q6,d4,'32','native_greedy','3',str(R/'guard-unreachable'),'probe']
mutations=[(0,'UNKNOWN_PROFILE'),(1,q8),(2,'Qwen3-0.6B-Q4_K_M.gguf'),(3,'1'),(4,'unknown_mode'),(5,'4'),(5,'0'),(7,'unknown_action')]
rows=[]
for i,value in mutations:
 args=base.copy();args[i]=value;p=subprocess.run([str(exe),*args],capture_output=True,cwd=exe.parent);x=[json.loads(s) for s in p.stdout.splitlines()];assert p.returncode==21 and x[-1]['event']=='ERROR' and not any(y['event']=='MEMORY' for y in x);rows.append(dict(mutation=[i,value],status='REJECTED_BEFORE_GPU_LOAD',output=x))
for args in [['TIGHT_Q8',q6,d4,'32','native_greedy','3',str(R/'guard-unreachable'),'probe'],['TIGHT_Q8',q8,d8,'32','native_greedy','3',str(R/'guard-unreachable'),'probe'],['TIGHT_Q8',q8,d4,'128','native_greedy','3',str(R/'guard-unreachable'),'probe'],['STANDARD_Q6',q6,d4,'32','ordinary','1',str(R/'guard-unreachable'),'probe']]:
 p=subprocess.run([str(exe),*args],capture_output=True,cwd=exe.parent);x=[json.loads(s) for s in p.stdout.splitlines()];assert p.returncode==21 and not any(y['event']=='MEMORY' for y in x);rows.append(dict(arguments=args,status='REJECTED_BEFORE_GPU_LOAD',output=x))
save(R/'NATIVE_NEGATIVE_GUARDS.json',dict(status='PASS',negative_cases=len(rows),cases=rows,model_loads=0,forward_calls=0));print('12 actual native negative guards PASS')
