"""Synthetic-only validator regression; no model/dataset execution or observations."""
import json, tempfile
from pathlib import Path
import common, study, verify

def main():
    assert common.semantic({'ids':list(range(129)),'eog':[False]*129})==(list(range(128)),False,1)
    assert common.semantic({'ids':[10,11,12],'eog':[False,True,False]})==([10,11],True,1)
    with tempfile.TemporaryDirectory(prefix='heterospec-direct-id-mock-') as temporary:
        folder=Path(temporary);root=folder/'formal';protocol=folder/'protocol'
        root.mkdir();protocol.mkdir()
        templates={c:common.command(Path('{BINARY_DIR}'),Path('{TARGET}'),Path('{DRAFT}'),Path('{PROMPT_FILE}'),c) for c in common.CONDITIONS}
        p={'task_ids':common.TASKS,'conditions':common.CONDITIONS,'command_templates':templates,
           'upstream_commit':'mock-source','target':{'sha256':'mock-target'},'draft':{'sha256':'mock-draft'},
           'dataset':{'sha256':'mock-dataset'},'binary_hashes':{'llama-completion.exe':'mock-baseline','llama-speculative.exe':'mock-spec'}}
        common.save(protocol/'protocol_v1.json',p);common.save(protocol/'FREEZE_MANIFEST.json',{'files':{}})
        rows=[]
        for task in common.TASKS:
            prompt=root/'prompts'/(task.replace('/','_')+'.txt');prompt.parent.mkdir(exist_ok=True);prompt.write_text('SYNTHETIC ONLY',encoding='utf-8')
            for rep in range(1,4):
                for condition in common.CONDITIONS:
                    ids=[17]*128;flags=[False]*128
                    if task==common.TASKS[0] and rep==1:ids=[17,18,19];flags=[False,False,True]
                    if task==common.TASKS[0] and rep==2 and condition=='B570_FAST_K2':ids[9]=18
                    stem=task.replace('/','_')+str(rep)+condition
                    side=root/(stem+'.json');stdout=root/(stem+'.stdout');stderr=root/(stem+'.stderr')
                    common.save(side,{'ids':ids,'eog':flags});stdout.write_bytes(b'SYNTHETIC ONLY')
                    off=[['37','37']] if condition=='TARGET_REFERENCE' else [['37','37'],['29','29']]
                    stderr.write_text('using device Vulkan0 (Intel(R) Arc(TM) B570 Graphics)\n'+''.join(f'offloaded {a}/{b} layers to GPU\n' for a,b in off),encoding='utf-8')
                    exe='llama-completion.exe' if condition=='TARGET_REFERENCE' else 'llama-speculative.exe'
                    row={'task_id':task,'repetition':rep,'condition':condition,'execution_valid':True,'exit_code':0,
                         'source_commit':'mock-source','target_sha256':'mock-target','draft_sha256':None if condition=='TARGET_REFERENCE' else 'mock-draft',
                         'dataset_sha256':'mock-dataset','binary_name':exe,'binary_sha256':p['binary_hashes'][exe],
                         'protocol_sha256':common.sha(protocol/'protocol_v1.json'),'device':'Vulkan0 / Intel Arc B570','offloads':off,
                         'study_head':'mock-head','command':[s.replace('\\','/').replace('{PROMPT_FILE}','{RUN_ROOT}/prompts/'+task.replace('/','_')+'.txt') for s in templates[condition]],
                         'raw_committed_ids':ids,'raw_eog_flags':flags,'generated_ids':ids,'generated_ids_sha256':common.arraysha(ids),
                         'raw_ids_sha256':common.arraysha(ids),'semantic_output_length':len(ids),'eos':any(flags),'cap_reached':len(ids)==128,
                         'raw_cli_overshoot_ids':0,'prompt_sha256':common.sha(prompt)}
                    for name,path in [('stdout',stdout),('stderr',stderr),('sidecar',side)]:row[name]=path.name;row[name+'_sha256']=common.sha(path)
                    rows.append(row)
        data={'status':'COMPLETE','executions':rows,'study_head':'mock-head','protocol_sha256':common.sha(protocol/'protocol_v1.json')}
        common.save(root/'executions.json',data)
        by={(r['task_id'],r['repetition'],r['condition']):r for r in rows};pairs=[]
        for task in common.TASKS:
            for rep in range(1,4):
                for candidate in common.CONDITIONS[1:]:pairs.append(study.compare(by[task,rep,'TARGET_REFERENCE'],by[task,rep,candidate]))
        analysis={'comparisons':pairs,'paths':{'B570_FAST_K2':{'exact_pairs':89,'wholly_exact_prompts':29,'qualification':'BLOCKED'},
                  'B570_SERIALIZED_K2':{'exact_pairs':90,'wholly_exact_prompts':30,'qualification':'QUALIFIED'}}}
        common.save(protocol/'FORMAL_ANALYSIS.json',analysis)
        check=lambda:verify.validate(root,protocol/'protocol_v1.json',protocol/'FORMAL_ANALYSIS.json')
        result=check();assert result['status']=='PASS',result
        analysis['comparisons'][0]['first_divergent_output_token_index']=99
        common.save(protocol/'FORMAL_ANALYSIS.json',analysis);assert check()['status']=='FAIL'
        analysis['comparisons'][0]['first_divergent_output_token_index']=None
        common.save(protocol/'FORMAL_ANALYSIS.json',analysis)
        rows[0]['eos']=not rows[0]['eos'];common.save(root/'executions.json',data);assert check()['status']=='FAIL'
        rows[0]['eos']=not rows[0]['eos'];common.save(root/'executions.json',data)
        rows.pop();common.save(root/'executions.json',data);assert check()['status']=='FAIL'
        print(json.dumps({'status':'PASS','synthetic_only':True,'tests':['direct-ID prefix/cap and overshoot','270 coverage/180 comparisons','EOG and cap','known mismatch and first divergence','tampered first-divergence rejected','tampered EOS rejected','missing execution rejected']}))

if __name__=='__main__':main()
