"""Independent hardware-free evidence and direct-ID validator; no common imports."""
import argparse,hashlib,json,re
from pathlib import Path

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while True:
            block=f.read(1024*1024)
            if not block:break
            h.update(block)
    return h.hexdigest()
def array_digest(a):return hashlib.sha256(json.dumps(a,separators=(',',':')).encode('ascii')).hexdigest()
def validate(root,protocol_path,analysis_path):
    protocol=json.loads(protocol_path.read_text(encoding='utf-8'))
    original=json.loads(analysis_path.read_text(encoding='utf-8'))
    data=json.loads((root/'executions.json').read_text(encoding='utf-8'));rows=data['executions'];errors=[]
    if data.get('status')!='COMPLETE':errors.append('Formal attempt not complete')
    if data.get('protocol_sha256')!=digest(protocol_path):errors.append('Execution manifest protocol hash invalid')
    expected={(t,r,c) for t in protocol['task_ids'] for r in range(1,4) for c in protocol['conditions']}
    actual=[(x['task_id'],x['repetition'],x['condition']) for x in rows]
    if len(rows)!=270 or len(set(actual))!=270 or set(actual)!=expected:errors.append('Execution coverage not exactly 270')
    by={key:row for key,row in zip(actual,rows)};sequences={}
    for key,row in by.items():
        if not row['execution_valid'] or row['exit_code']!=0:errors.append(f'Execution invalid {key}')
        if row['source_commit']!=protocol['upstream_commit'] or row['target_sha256']!=protocol['target']['sha256'] or row['dataset_sha256']!=protocol['dataset']['sha256']:errors.append(f'Provenance invalid {key}')
        if row['binary_sha256']!=protocol['binary_hashes'][row['binary_name']]:errors.append(f'Binary hash invalid {key}')
        if row['protocol_sha256']!=digest(protocol_path):errors.append(f'Protocol hash invalid {key}')
        if key[2]!='TARGET_REFERENCE' and row['draft_sha256']!=protocol['draft']['sha256']:errors.append(f'Draft hash invalid {key}')
        if row['device']!='Vulkan0 / Intel Arc B570':errors.append(f'Device invalid {key}')
        required=[['37','37']] if key[2]=='TARGET_REFERENCE' else [['37','37'],['29','29']]
        if row['offloads']!=required:errors.append(f'Offload invalid {key}')
        if row['study_head']!=data['study_head']:errors.append(f'HEAD inconsistent {key}')
        expected_command=[s.replace('\\','/').replace('{PROMPT_FILE}','{RUN_ROOT}/prompts/'+key[0].replace('/','_')+'.txt') for s in protocol['command_templates'][key[2]]]
        if row['command']!=expected_command:errors.append(f'Frozen command invalid {key}')
        for name,hash_key in [('stdout','stdout_sha256'),('stderr','stderr_sha256'),('sidecar','sidecar_sha256')]:
            if digest(root/row[name])!=row[hash_key]:errors.append(f'Raw payload invalid {key} {name}')
        stderr=(root/row['stderr']).read_text(encoding='utf-8',errors='replace')
        if 'using device Vulkan0 (Intel(R) Arc(TM) B570 Graphics)' not in stderr:errors.append(f'Raw device evidence absent {key}')
        raw_offloads=[list(x) for x in re.findall(r'offloaded\s+(\d+)/(\d+) layers to GPU',stderr)]
        if raw_offloads!=required:errors.append(f'Raw offload evidence invalid {key}')
        side=json.loads((root/row['sidecar']).read_text(encoding='utf-8'))
        ids=side['ids'];flags=side['eog']
        if not ids or any(type(x)!=int or x<0 for x in ids) or any(type(x)!=bool for x in flags):errors.append(f'Invalid sidecar types {key}')
        if ids!=row['raw_committed_ids'] or flags!=row['raw_eog_flags'] or len(ids)!=len(flags):errors.append(f'Raw IDs inconsistent {key}')
        end=len(ids)
        for i in range(len(flags)):
            if flags[i]:end=i+1;break
        selected=ids[:min(128,end)];sequences[key]=selected
        if row['eos']!=any(flags[:len(selected)]) or row['cap_reached']!=(len(selected)==128) or row['raw_cli_overshoot_ids']!=len(ids)-len(selected):errors.append(f'EOS/cap evidence invalid {key}')
        if selected!=row['generated_ids'] or array_digest(selected)!=row['generated_ids_sha256']:errors.append(f'Semantic ID array invalid {key}')
        if len(selected)!=row['semantic_output_length'] or array_digest(ids)!=row['raw_ids_sha256']:errors.append(f'Length/hash invalid {key}')
        if not row['eos'] and len(selected)!=128:errors.append(f'Incomplete semantic cap {key}')
        prompt=root/'prompts'/(key[0].replace('/','_')+'.txt')
        if digest(prompt)!=row['prompt_sha256']:errors.append(f'Prompt file invalid {key}')
    freeze_path=protocol_path.parent/'FREEZE_MANIFEST.json'
    if not freeze_path.exists():errors.append('Freeze manifest missing')
    else:
        freeze=json.loads(freeze_path.read_text(encoding='utf-8'))
        for rel,want in freeze['files'].items():
            name=Path(rel).name
            if rel.startswith('benchmarks/b570_direct_id_v1/'):
                file=protocol_path.parent/name
            else:
                bundled=protocol_path.parent.parent/'runner'/name
                file=bundled if bundled.exists() else Path(rel)
            if not file.exists() or digest(file)!=want:errors.append(f'Frozen source hash invalid {rel}')
    comparisons=[];paths={}
    for candidate in protocol['conditions'][1:]:
        exact=0;wholly=0
        for task in protocol['task_ids']:
            good=True
            for rep in range(1,4):
                a=sequences.get((task,rep,'TARGET_REFERENCE'),[]);b=sequences.get((task,rep,candidate),[])
                same=a==b;exact+=int(same);good=good and same
                divergence=None
                if not same:
                    divergence=next((i for i in range(min(len(a),len(b))) if a[i]!=b[i]),min(len(a),len(b)))
                comparisons.append({'task_id':task,'repetition':rep,'candidate':candidate,'exact':same,
                  'first_divergent_output_token_index':divergence,
                  'reference_token_id':a[divergence] if divergence is not None and divergence<len(a) else None,
                  'candidate_token_id':b[divergence] if divergence is not None and divergence<len(b) else None,
                  'reference_length':len(a),'candidate_length':len(b)})
            wholly+=int(good)
        paths[candidate]={'exact_pairs':exact,'wholly_exact_prompts':wholly,'qualification':'QUALIFIED' if exact==90 else 'BLOCKED'}
    for candidate,summary in paths.items():
        for k,value in summary.items():
            if original['paths'][candidate][k]!=value:errors.append(f'Primary summary disagrees {candidate} {k}')
    primary={(x['task_id'],x['repetition'],x['candidate']):x for x in original['comparisons']}
    for x in comparisons:
        if x!=primary.get((x['task_id'],x['repetition'],x['candidate'])):errors.append('Primary first-divergence mismatch '+str(x))
    return {'schema':'heterospec.b570.direct_id.independent_validation.v1','status':'PASS' if not errors else 'FAIL',
            'executions':len(rows),'comparisons':len(comparisons),'paths':paths,'errors':errors,
            'method':'Independent implementation reads sidecars and recomputes selection, hashes, pair counts and first divergence without importing primary comparison code.'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--protocol',type=Path,required=True);ap.add_argument('--analysis',type=Path,required=True);ap.add_argument('--output',type=Path);ap.add_argument('--manifest',type=Path)
    a=ap.parse_args();root=a.root.resolve();result=validate(root,a.protocol,a.analysis)
    if a.manifest:
        m=json.loads(a.manifest.read_text(encoding='utf-8'))
        errors=[]
        for entry in m['files']:
            p=a.manifest.parent/entry['path']
            if not p.exists() or p.stat().st_size!=entry['size'] or digest(p)!=entry['sha256']:errors.append(entry['path'])
        result['archive_file_count']=len(m['files']);result['archive_errors']=errors
        if errors:result['status']='FAIL'
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
    if result['status']!='PASS':raise SystemExit(1)

if __name__=='__main__':main()
