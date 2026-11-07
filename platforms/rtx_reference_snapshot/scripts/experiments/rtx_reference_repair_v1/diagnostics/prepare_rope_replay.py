import pathlib,sys,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from common import read,save,need,file_hash
from tensors import compare,load_capture
bundle=pathlib.Path(sys.argv[1]);unit=bundle/'units/rope_operands02';out=pathlib.Path(sys.argv[2]);need(not out.exists(),'fresh operand directory');receipt=read(unit/'RECEIPT.json');need(receipt['success'] and receipt['active_processes_after_wait']==0,'operand capture incomplete');out.mkdir(parents=True)
root=unit/'native/rope_operands/i02';items=[];controls=[];captures={}
def vectors(p):return {str(f.relative_to(p)):file_hash(f) for f in (p/'target').glob('*.f32')}
for arm in ['R','C_QB']:
    pa=root/arm/'off';pb=root/arm/'tensors';a=read(root/arm/'off.json');b=read(root/arm/'tensors.json');keys=['endpoint','cycles','target_state','target_final_kv','draft_final_kv']+(['draft_state'] if b['draft_enabled'] else [])
    same=all(a[k]==b[k] for k in keys) and vectors(pa)==vectors(pb)
    if b['draft_enabled']:
        same=same and {f.name:file_hash(f) for f in (pa/'draft').glob('*.f32')}=={f.name:file_hash(f) for f in (pb/'draft').glob('*.f32')}
    need(same,'operand observer contaminated');controls.append({'arm':arm,'vectors_endpoint_transactions_states_equal':same})
    rows=[json.loads(l) for l in (pb/'trace/INDEX.jsonl').read_text().splitlines()]
    inputs=[r for r in rows if r['name']=='Kcur_normed-10' and r['op']=='MUL'];outputs=[r for r in rows if r['name']=='Kcur-10' and r['op']=='ROPE'];need(len(inputs)==len(outputs)==1,'unique real RoPE operand/output')
    inp=inputs[0];res=outputs[0];payload=load_capture(pb,inp);expected=load_capture(pb,res);ne=inp['ne'];need(ne==[128,8,len(res['rope_positions_i32']),1] and inp['nb']==[4,512,4096,4096*ne[2]],'contiguous source row map')
    (out/(arm+'_input.f32')).write_bytes(payload);(out/(arm+'_expected.f32')).write_bytes(expected);save(out/(arm+'_capture.json'),{'input':inp,'output':res,'record_sha256':file_hash(root/arm/'tensors.json')})
    items.append({'name':arm,'shape':ne,'input_file':str((out/(arm+'_input.f32')).resolve()),'input_sha256':file_hash(out/(arm+'_input.f32')),'expected_file':str((out/(arm+'_expected.f32')).resolve()),'expected_sha256':file_hash(out/(arm+'_expected.f32')),'op_params_i32':res['op_params_i32'],'positions_i32':res['rope_positions_i32'],'captured_backend':res['scheduler_backend']})
    captures[arm]=(payload,inp,b)
need(items[0]['op_params_i32']==items[1]['op_params_i32'],'operator parameters differ')
need(items[0]['positions_i32'][0]==items[1]['positions_i32'][0]==92,'absolute position differs')
left,ma,ra=captures['R'];right,mb,rb=captures['C_QB'];c=compare(left,ma,right,mb,left_row=0,right_row=0,axis=2);need(c['bitwise_equal'],'normalized K operands differ')
need(ra['boundary']['boundary_state_sha256']==rb['boundary']['boundary_state_sha256'] and ra['ids'][0]==rb['ids'][0],'initial state/seed differs')
save(out/'MANIFEST.json',{'operands':items,'controls':controls,'first_token_operands_bitwise_equal':c,'same_boundary_state_and_seed':True,'native_operator_replays_planned':8,'model_requests_planned':0,'budget_policy':'Charge all8 operator replays conservatively against shared development and total ceilings.'},exclusive=True)
print('Authenticated native operands ready; no replay executed')
