from host import *
def build_diagnostic():
    s=(HERE/'worker_service.cpp').read_text()
    s=s.replace('t=service_start;llama_memory_clear(llama_get_memory(c),true);','t=service_start;if(!u.value("continuous",false))llama_memory_clear(llama_get_memory(c),true);')
    s=s.replace('check(llama_state_seq_set_data(c,selected_state.data(),selected_state.size(),0)==selected_state.size(),"restore");','if(!u.value("continuous",false))check(llama_state_seq_set_data(c,selected_state.data(),selected_state.size(),0)==selected_state.size(),"restore");')
    old='service_decode(c,ids.data()+pos,int(w),pos,pos+int(w)==int(ids.size()));pos+=int(w);'
    new='service_decode(c,ids.data()+pos,int(w),pos,pos+int(w)==int(ids.size()),true);for(int row=0;row<int(w);row++)raw(dir/("append-"+std::to_string(pos+row)+".f32"),llama_get_logits_ith(c,row),size_t(llama_vocab_n_tokens(llama_model_get_vocab(m)))*4);pos+=int(w);'
    assert old in s;s=s.replace(old,new);(HERE/'diagnostic_worker.cpp').write_text(s)
    build('diag-reference',True,'diagnostic_worker.cpp');build('diag-candidate',source='diagnostic_worker.cpp')
def execute():
    ids=[113+(i*173)%2309 for i in range(320)]
    run('restore-diagnostic-reference','diag-reference',dict(mode='requests',capacity=4096,units=[dict(id=kind,arm='R',tokens=ids,head=253,cap=8,capture=True,continuous=kind=='continuous') for kind in ('continuous','restored')]),requests=2)
    run('restore-diagnostic-candidate','diag-candidate',dict(mode='requests',capacity=4096,units=[dict(id=a,arm=a,tokens=ids,head=253,cap=8,capture=True) for a in ('QB','WB-cut','WB-rechunk')]),requests=3)
    ref=ROOT/'restore-diagnostic-reference/continuous';v={p.name:sha(p) for p in ref.glob('*.f32')};proof=[]
    for p in [ROOT/'restore-diagnostic-reference/restored']+[ROOT/'restore-diagnostic-candidate'/a for a in ('QB','WB-cut','WB-rechunk')]:
        proof.append(dict(path=str(p),vectors_equal=v=={f.name:sha(f) for f in p.glob('*.f32')},state_equal=sha(ref/'final.bin')==sha(p/'final.bin'),vectors=len(v)))
    put(ROOT/'RESTORE_AND_APPEND_DIAGNOSTIC.json',dict(scope='separate all-known-append-output diagnostic; not a substitute for actual-service output flag qualification',proof=proof))
    assert all(x['vectors_equal'] and x['state_equal'] for x in proof)
if __name__=='__main__':globals()[sys.argv[1]]()
