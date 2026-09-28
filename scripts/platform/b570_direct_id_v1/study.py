"""Freeze preparation, formal execution, and primary direct-ID analysis."""
import argparse, difflib, json, os, random, subprocess, threading, time
from pathlib import Path
from common import *

PROTOCOL_DIR=Path('benchmarks/b570_direct_id_v1')

def powershell(code):
    return json.loads(subprocess.check_output(['powershell.exe','-NoProfile','-Command',code],text=True,encoding='utf-8-sig'))
def environment():
    return powershell("[ordered]@{os=(Get-CimInstance Win32_OperatingSystem|Select-Object Caption,Version,BuildNumber);cpu=(Get-CimInstance Win32_Processor|Select-Object Name,NumberOfCores,NumberOfLogicalProcessors);ram_bytes=(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory;gpu=@(Get-CimInstance Win32_VideoController|Select-Object Name,DriverVersion,PNPDeviceID);todesk_processes=@(Get-Process -Name '*ToDesk*' -ErrorAction SilentlyContinue|Select-Object ProcessName,Id);observed_at=(Get-Date).ToString('o')}|ConvertTo-Json -Depth 6")
def build_flags(cache):
    return {line.split('=',1)[0]:line.split('=',1)[1] for line in cache.read_text(encoding='utf-8').splitlines()
            if '=' in line and not line.startswith('//') and (line.startswith(('GGML_','LLAMA_','CMAKE_C_FLAGS:','CMAKE_CXX_FLAGS:','CMAKE_C_FLAGS_RELEASE:','CMAKE_CXX_FLAGS_RELEASE:')))
            and ':INTERNAL=' not in line}
def make_patch(repo):
    upstream=repo/'work/b570_direct_id_v1/upstream'/('llama.cpp-'+UPSTREAM)
    modified=Path('C:/hs/b570-direct-id-v1-src')
    chunks=[]
    paths=['common/heterospec-direct-id.h','tools/completion/completion.cpp','examples/speculative/speculative.cpp']
    for rel in paths:
        original=(upstream/rel).read_text(encoding='utf-8').splitlines(True) if (upstream/rel).exists() else []
        new=(modified/rel).read_text(encoding='utf-8').splitlines(True)
        chunks.extend(difflib.unified_diff(original,new,fromfile='a/'+rel if original else '/dev/null',tofile='b/'+rel))
    patch=PROTOCOL_DIR/'instrumentation.patch';patch.write_text(''.join(chunks),encoding='utf-8',newline='\n')
    return patch
def prepare(repo,r0root):
    r0=json.loads((r0root/'R0.json').read_text(encoding='utf-8'))
    if r0['status']!='PASS':raise RuntimeError('R0 has not qualified')
    if len(r0['pairs'])!=18 or {(x['task_id'],x['condition']) for x in r0['pairs']}!={(t,c) for t in SANITY for c in CONDITIONS}:
        raise RuntimeError('R0 coverage is incomplete')
    for pair in r0['pairs']:
        a,b=pair['original'],pair['instrumented']
        if not a['execution_valid'] or not b['execution_valid'] or a['stdout_sha256']!=b['stdout_sha256']:
            raise RuntimeError('R0 equivalence/placement failed')
        if b['semantic_output_length']!=128 and not b['eos']:
            raise RuntimeError('R0 semantic cap is incomplete')
    if len(r0['state_reset'])!=3 or not all(x['exact_to_first'] and x['run']['execution_valid'] for x in r0['state_reset']):
        raise RuntimeError('R0 reset failed')
    if len(r0['eos_tests'])!=3 or not all(x['pass'] for x in r0['eos_tests']):
        raise RuntimeError('R0 EOG failed')
    target,draft=assets(repo);dataset(repo);patch=make_patch(repo)
    schedule=[];rng=random.Random(SEED)
    for rep in range(1,4):
        for task in TASKS:
            order=CONDITIONS.copy();rng.shuffle(order)
            schedule.append({'task_id':task,'repetition':rep,'conditions':order})
    bins={x.name:sha(x) for x in INSTRUMENTED.iterdir() if x.suffix.lower() in ('.dll','.exe')}
    original_bins={x.name:sha(x) for x in ORIGINAL.iterdir() if x.suffix.lower() in ('.dll','.exe') and (x.suffix.lower()=='.dll' or x.name in ('llama-completion.exe','llama-speculative.exe'))}
    commands={c:command(Path('{BINARY_DIR}'),Path('{TARGET}'),Path('{DRAFT}'),Path('{PROMPT_FILE}'),c) for c in CONDITIONS}
    differences=[i for i,(a,b) in enumerate(zip(commands['B570_FAST_K2'],commands['B570_SERIALIZED_K2'])) if a!=b]
    if len(differences)!=1 or commands['B570_FAST_K2'][differences[0]-1]!='--ubatch-size':
        raise RuntimeError('Candidate paths differ by more than ubatch')
    original_cache=Path('C:/hs/b/CMakeCache.txt');instrumented_cache=Path('C:/hs/b570-direct-id-v1-build/CMakeCache.txt')
    flags=build_flags(instrumented_cache)
    if flags!=build_flags(original_cache):raise RuntimeError('Compile flags differ from frozen original build')
    protocol={'schema':'heterospec.b570.direct_id.protocol.v1','study':'prospectively frozen direct-ID replication',
      'starting_main':START,'preparation_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'upstream_commit':UPSTREAM,'build':10839,'historical_known_outcomes':{'fast_retokenized_text_pairs':45,'serialized_retokenized_text_pairs':60,'denominator':90},
      'historical_material_policy':'Closed, unchanged; new direct-ID replication is additive.',
      'task_ids':TASKS,'repetitions':3,'conditions':CONDITIONS,'expected_executions':270,'expected_pairs_per_candidate':90,
      'schedule_seed':SEED,'schedule':schedule,'command_templates':commands,
      'target':{'filename':target.name,'sha256':TARGET_HASH,'offload':'37/37','device':'Vulkan0'},
      'draft':{'filename':draft.name,'sha256':DRAFT_HASH,'offload':'29/29','device':'Vulkan0'},
      'dataset':{'path':'datasets/humaneval/HumanEval.jsonl.gz','sha256':DATA_HASH},
      'instrumentation':{'patch':'instrumentation.patch','sha256':sha(patch),'interface':'HETEROSPEC_DIRECT_ID_PATH JSON sidecar',
        'boundary':'completion sampled/accepted generated ID; speculative final accepted/replacement target ID, before output',
        'no_semantic_changes':'No logits, sampler, verification, KV, batch, placement, or stopping changes.'},
      'binary_hashes':bins,'original_binary_hashes':original_bins,'environment':environment(),
      'direct_id_contract':{'raw':'Archive every committed ID and matching runtime EOG flag; no text extraction or retokenization.',
        'comparison':'Direct committed-ID prefix up to and including first EOG or the first 128 IDs, whichever occurs first.',
        'raw_cli_overshoot':'Original b10839 speculative may finish its verification block past the budget. Preserve all overshoot IDs, but compare only the already-frozen maximum 128 semantic generated tokens. This is selection of actual IDs, not retokenization.',
        'cli_n_predict':{'TARGET_REFERENCE':128,'B570_FAST_K2':127,'B570_SERIALIZED_K2':127},
        'prompt_ids':'Excluded by source instrumentation location, not by text matching.',
        'array_sha256':'SHA256 of compact ASCII JSON integer array with no spaces.'},
      'r0':{'path':str(r0root.relative_to(repo)).replace('\\','/'),'sha256':sha(r0root/'R0.json'),'status':'PASS',
        'original_instrumented_stdout_equal_pairs':len(r0['pairs']),'semantic_lengths':r0['semantic_lengths'],'raw_lengths':r0['raw_lengths']},
      'qualification_rule':'90/90 direct-ID pairs -> QUALIFIED; any lower count -> BLOCKED',
      'failure_policy':'Continue true token mismatches. Operational/parser/offload/hash failure makes the attempt INVALID; retain all records, no selective rerun. Semantic repairs require protocol v2.',
      'formal_execution':'Fresh process per execution. No energy collector. Operational timings are descriptive, not historical timing replication.',
      'remote_session_policy':'ToDesk may remain connected for this direct-ID correctness endpoint; no authoritative timing or power inference is made. Task Scheduler owns the unattended process and does not require interactive shell survival.',
      'analysis_outputs':['FORMAL_ANALYSIS.json','FORMAL_REPORT.md','INDEPENDENT_VALIDATION.json','CLOSEOUT.md'],
      'manuscript_edits':False,'parameter_changes_after_data_start':False}
    save(PROTOCOL_DIR/'protocol_v1.json',protocol)
    save(PROTOCOL_DIR/'BUILD_ENVIRONMENT.json',{'upstream_archive_sha256':sha(repo/'work/b570_direct_id_v1/upstream-0cae43063.zip'),
      'compile_flags':'Same GGML/LLAMA and release compiler flags as the original build; MSVC19.44, Vulkan SDK1.4.357.',
      'cmake_flags':flags,'original_cmake_cache_sha256':sha(original_cache),'instrumented_cmake_cache_sha256':sha(instrumented_cache),
      'historical_source_comparison':{'upstream_files_compared':3531,'differences':0,'scope':'Every upstream archive file matched the retained historical source before observational patching.'},
      'configure_command':'cmake -S SOURCE -B BUILD -G "Visual Studio 17 2022" -A x64 -DGGML_VULKAN=ON -DCMAKE_BUILD_TYPE=Release -DLLAMA_BUILD_NUMBER=10839 -DLLAMA_BUILD_COMMIT=0cae43063 -DLLAMA_BUILD_SERVER=ON -DLLAMA_BUILD_TESTS=OFF',
      'build_command':'cmake --build BUILD --config Release --target llama-completion llama-speculative -j 10',
      'binaries':bins,'environment':protocol['environment']})
    files=[*Path('scripts/platform/b570_direct_id_v1').glob('*.py'),*Path('scripts/platform/b570_direct_id_v1').glob('*.ps1'),*PROTOCOL_DIR.glob('*')]
    files=[p for p in files if p.is_file() and p.name!='FREEZE_MANIFEST.json']
    freeze={'schema':'heterospec.b570.direct_id.freeze.v1','created_at':utc(),'starting_main':START,
      'files':{str(p).replace('\\','/'):sha(p) for p in files},'binary_hashes':bins,
      'protocol_sha256':sha(PROTOCOL_DIR/'protocol_v1.json'),'after_commit_rule':'All files and binaries remain immutable after formal start; actual execution study HEAD recorded in each run.'}
    save(PROTOCOL_DIR/'FREEZE_MANIFEST.json',freeze)

def compare(ref,candidate):
    r=ref['generated_ids'];c=candidate['generated_ids'];index=None
    for i in range(min(len(r),len(c))):
        if r[i]!=c[i]:index=i;break
    if index is None and len(r)!=len(c):index=min(len(r),len(c))
    return {'task_id':candidate['task_id'],'repetition':candidate['repetition'],'candidate':candidate['condition'],
      'exact':index is None,'first_divergent_output_token_index':index,
      'reference_token_id':r[index] if index is not None and index<len(r) else None,
      'candidate_token_id':c[index] if index is not None and index<len(c) else None,
      'reference_length':len(r),'candidate_length':len(c)}

def analyze(root):
    executions=json.loads((root/'executions.json').read_text(encoding='utf-8'))['executions'];pairs=[];by={}
    for row in executions:by[(row['task_id'],row['repetition'],row['condition'])]=row
    for task in TASKS:
        for rep in range(1,4):
            ref=by[(task,rep,'TARGET_REFERENCE')]
            for c in CONDITIONS[1:]:pairs.append(compare(ref,by[(task,rep,c)]))
    result={'schema':'heterospec.b570.direct_id.analysis.v1','executions':len(executions),'comparisons':pairs,'paths':{}}
    for c in CONDITIONS[1:]:
        cp=[p for p in pairs if p['candidate']==c];n=sum(x['exact'] for x in cp)
        good=[task for task in TASKS if all(x['exact'] for x in cp if x['task_id']==task)]
        result['paths'][c]={'exact_pairs':n,'total_pairs':90,'wholly_exact_prompts':len(good),'total_prompts':30,
          'qualification':'QUALIFIED' if n==90 else 'BLOCKED','exact_prompt_ids':good,
          'mismatches':[x for x in cp if not x['exact']]}
    result['historical_comparator']={'definition':'prompt-stripped/count-normalized re-tokenized text; not direct-ID certificates','fast':45,'serialized':60,'pairs':90}
    save(PROTOCOL_DIR/'FORMAL_ANALYSIS.json',result);save(root/'FORMAL_ANALYSIS.json',result)
    text='# B570 direct-generated-ID qualification replication\n\n'
    text+='Prospectively frozen replication with known historical outcomes. '+str(len(executions))+'/270 executions completed; no energy campaign.\n\n'
    for c,x in result['paths'].items():text+=f"- {c}: **{x['qualification']}**, {x['exact_pairs']}/90 exact direct-ID pairs; {x['wholly_exact_prompts']}/30 wholly exact prompts.\n"
    text+='\nHistorical fast 45/90 and serialized 60/90 are re-tokenized-text agreement counts and remain unchanged. They are not direct generated-ID certificates.\n\n'
    fast=result['paths']['B570_FAST_K2'];serial=result['paths']['B570_SERIALIZED_K2']
    if serial['qualification']=='QUALIFIED':text+='Serialization restores direct-ID qualification on this tested B570 path. This does not imply a general correctness guarantee.\n'
    elif serial['exact_pairs']>fast['exact_pairs']:text+='Serialization improves agreement but does not establish qualification.\n'
    else:text+='Serialization does not establish qualification on this tested path.\n'
    text+='\nNo Vulkan-wide or hardware-wide causal claim is made. No manuscript/figure edits or result-driven parameter search. All generated-ID comparisons and first-divergence evidence are in FORMAL_ANALYSIS.json.\n'
    (PROTOCOL_DIR/'FORMAL_REPORT.md').write_text(text,encoding='utf-8')
    return result

def run(repo,root):
    freeze=json.loads((PROTOCOL_DIR/'FREEZE_MANIFEST.json').read_text(encoding='utf-8'))
    proto=json.loads((PROTOCOL_DIR/'protocol_v1.json').read_text(encoding='utf-8'))
    for path,want in freeze['files'].items():
        if sha(repo/path)!=want:raise RuntimeError('Frozen file changed: '+path)
    for name,want in freeze['binary_hashes'].items():
        if sha(INSTRUMENTED/name)!=want:raise RuntimeError('Frozen binary changed: '+name)
    current=environment();driver=next(x['DriverVersion'] for x in current['gpu'] if x['Name']=='Intel(R) Arc(TM) B570 Graphics')
    expected=next(x['DriverVersion'] for x in proto['environment']['gpu'] if x['Name']=='Intel(R) Arc(TM) B570 Graphics')
    if driver!=expected:raise RuntimeError('Frozen Arc driver changed')
    target,draft=assets(repo);problems=dataset(repo);head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    for path in freeze['files']:
        committed=subprocess.check_output(['git','show',head+':'+path])
        if __import__('hashlib').sha256(committed).hexdigest()!=freeze['files'][path]:
            raise RuntimeError('Frozen file not committed byte-for-byte: '+path)
    if subprocess.check_output(['git','branch','--show-current'],text=True).strip()!='experiment/b570-direct-id-qualification-v1':
        raise RuntimeError('Wrong study branch')
    root.mkdir(parents=True,exist_ok=False)
    evidence={'schema':'heterospec.b570.direct_id.executions.v1','study_head':head,'protocol_sha256':sha(PROTOCOL_DIR/'protocol_v1.json'),
      'started':utc(),'status':'RUNNING','executions':[]}
    status={'state':'RUNNING','completed':0,'total':270};lock=threading.Lock();stop=threading.Event()
    def tick():
        while not stop.wait(15):
            with lock:status['heartbeat_at']=utc();save(root/'status.json',status)
    threading.Thread(target=tick,daemon=True).start()
    try:
        for block in proto['schedule']:
            task=block['task_id'];rep=block['repetition'];prompt=root/'prompts'/(task.replace('/','_')+'.txt')
            prompt.parent.mkdir(parents=True,exist_ok=True)
            prompt.write_text(PREFIX+problems[task]['prompt'],encoding='utf-8',newline='\n')
            for c in block['conditions']:
                with lock:status.update(task_id=task,repetition=rep,condition=c,completed=len(evidence['executions']))
                cmd=command(INSTRUMENTED,target,draft,prompt,c);stem=task.replace('/','_')+f'-r{rep}-'+c
                row=execute(root,stem,cmd)
                row.update(task_id=task,repetition=rep,condition=c,study_head=head,source_commit=UPSTREAM,
                  binary_sha256=sha(Path(cmd[0])),binary_name=Path(cmd[0]).name,target_sha256=TARGET_HASH,
                  draft_sha256=DRAFT_HASH if c!='TARGET_REFERENCE' else None,dataset_sha256=DATA_HASH,
                  protocol_sha256=evidence['protocol_sha256'],device='Vulkan0 / Intel Arc B570',prompt_sha256=sha(prompt))
                # Portable command and artifacts: machine-local asset paths become explicit placeholders.
                replacements={str(INSTRUMENTED):'{BINARY_DIR}',str(target):'{TARGET}',str(draft):'{DRAFT}',str(root):'{RUN_ROOT}'}
                portable=[]
                for item in row['command']:
                    for prefix,replacement in replacements.items():item=item.replace(prefix,replacement)
                    portable.append(item.replace('\\','/'))
                row['command']=portable
                evidence['executions'].append(row);save(root/'executions.json',evidence)
                print(f"{len(evidence['executions'])}/270 {stem} ids={row.get('semantic_output_length')} valid={row['execution_valid']}",flush=True)
                if not row['execution_valid']:raise RuntimeError('Operational/offload failure; retained without rerun')
        if subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()!=head:
            raise RuntimeError('Study HEAD changed during formal execution')
        for path,want in freeze['files'].items():
            if sha(repo/path)!=want:raise RuntimeError('Frozen source changed during execution: '+path)
        for name,want in freeze['binary_hashes'].items():
            if sha(INSTRUMENTED/name)!=want:raise RuntimeError('Frozen binary changed during execution: '+name)
        final_driver=next(x['DriverVersion'] for x in environment()['gpu'] if x['Name']=='Intel(R) Arc(TM) B570 Graphics')
        if final_driver!=expected:raise RuntimeError('Driver changed during formal execution')
        assets(repo);dataset(repo)
        evidence['status']='COMPLETE';evidence['ended']=utc();save(root/'executions.json',evidence)
        result=analyze(root)
        status.update(state='MEASUREMENTS_COMPLETE',completed=270,paths=result['paths'])
    except Exception as e:
        evidence.update(status='INVALID_OPERATIONAL',error=str(e),ended=utc());save(root/'executions.json',evidence)
        status.update(state='INVALID_OPERATIONAL',error=str(e));raise
    finally:
        stop.set();status['heartbeat_at']=utc();save(root/'status.json',status)

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','run','analyze']);p.add_argument('--root',type=Path,required=True)
    a=p.parse_args();repo=Path.cwd();root=a.root.resolve()
    if a.mode=='prepare':prepare(repo,root)
    elif a.mode=='run':run(repo,root)
    else:analyze(root)

if __name__=='__main__':main()
