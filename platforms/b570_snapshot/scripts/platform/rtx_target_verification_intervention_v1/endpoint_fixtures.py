"""Exercise the actual native capture parser and independent parser on raw fixtures."""
import importlib.util
from prepare import *

def main():
    directory=OUT/'endpoint-fixtures';directory.mkdir(exist_ok=True)
    spec=importlib.util.spec_from_file_location('original_parser',ROOT/'scripts/platform/rtx_trajectory_cost_v4/native.py');original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
    spec=importlib.util.spec_from_file_location('independent_parser',HERE/'independent_verify.py');independent=importlib.util.module_from_spec(spec);spec.loader.exec_module(independent)
    header='0.00.000.001 I load_tensors: offloaded 37/37 layers to GPU\n0.00.000.002 I llama_prepare_model_devices: using device CUDA0 (NVIDIA GeForce RTX 5070 Ti Laptop GPU)\n0.00.000.003 I llama_context: n_ubatch = 1\n0.00.000.004 I cached n_tokens = 0, memory_seq_rm [0, end)\n0.00.000.005 I slot operator(): id 0 | task 0 | new prompt, task.n_tokens = 1\n0.00.000.006 D ubatch_print: 0: id = 151644 (\'x\'), pos = 0, n_seq_id = 1, seq_id = [0], output = 1\n'
    rows=[f"0.00.001.001 D slot process_toke: id 0 | task 0 | n_gen = {i}, n_remaining = {128-i}, next token: {151645 if i==128 else 1} 'x'\n" for i in range(1,129)]
    footer='0.00.002.001 I slot process_toke: id 0 | task 0 | stopped by limit\n0.00.002.002 I slot process_toke: id 0 | task 0 | stopped by EOS\n0.00.002.003 I slot print_timing: id 0 | task 0 | eval time = 12.0 ms / 128 tokens\n'
    legal=directory/'legal-token128-eog-cap.native.log';legal.write_text(header+''.join(rows)+footer,encoding='utf-8',newline='\n')
    a=original.parse_capture(legal,'TARGET_REFERENCE');b=independent.parse_native(legal)
    assert a['generated_ids']==b['ids']==[1]*127+[151645] and a['native_stop_observations']==b['stop_markers']==['limit','EOS']
    tests={'actual_two_parsers_accept_token128_eog_cap':{'pass':True,'synthetic':True,'raw':str(legal.relative_to(ROOT)).replace('\\','/'),'sha256':sha(legal)}}
    fixtures={'missing_id':header+''.join(rows[:-1])+footer,'duplicate_id':header+''.join(rows[:-1])+rows[-2]+footer,'reordered_ids':header+rows[1]+rows[0]+''.join(rows[2:])+footer,'missing_EOS':header+''.join(rows)+footer.replace('0.00.002.002 I slot process_toke: id 0 | task 0 | stopped by EOS\n',''),'reversed_markers':header+''.join(rows)+footer.replace('stopped by limit','stopped by TEMP').replace('stopped by EOS','stopped by limit').replace('stopped by TEMP','stopped by EOS'),'unfinished_capture':header+''.join(rows[:64])}
    for name,text in fixtures.items():
        p=directory/(name+'.native.log');p.write_text(text,encoding='utf-8',newline='\n');errors=[]
        for fn in [lambda:original.parse_capture(p,'TARGET_REFERENCE'),lambda:independent.parse_native(p)]:
            try:fn()
            except Exception as exc:errors.append(type(exc).__name__)
            else:raise AssertionError(name+' unexpectedly accepted')
        tests['actual_two_parsers_reject_'+name]={'pass':True,'synthetic':True,'errors':errors,'raw':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':sha(p)}
    receipt=read(DOC/'FIXTURE_RECEIPT.json');receipt['tests'].update(tests);receipt['test_count']=len(receipt['tests']);receipt['raw_endpoint_fixture_scope']='synthetic raw logs executed through both actual parsers; not GPU outputs';save(DOC/'FIXTURE_RECEIPT.json',receipt)
    print(json.dumps({'endpoint_tests':len(tests),'total_tests':receipt['test_count']}),flush=True)

if __name__=='__main__':main()
