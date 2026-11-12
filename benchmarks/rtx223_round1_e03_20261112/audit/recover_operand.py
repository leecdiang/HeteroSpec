"""Recover one prior q8 replay operand, explicitly derived from a q32 witness."""
from pathlib import Path
import datetime,hashlib,json,shutil

HERE=Path(__file__).resolve().parent
SRC=Path('E:/rtx170/witness-8B/native')
NAME='blk.0.attn_q.weight'

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()

def entry(p):return dict(path=str(p),bytes=Path(p).stat().st_size,sha256=sha(p))

def main():
    out=HERE/'recovered_operand';out.mkdir(exist_ok=False)
    receipt=json.loads((SRC/'receipt.json').read_bytes())
    ops=[op for op in receipt['nodes'] if op['weight']['name']==NAME]
    if len(ops)!=1:raise ValueError('unique descriptor required')
    op=ops[0]
    if op['input']['ne']!=[4096,32,1,1] or op['weight']['ne']!=[4096,4096,1,1]:
        raise ValueError('unexpected descriptor')
    original=SRC/NAME
    if (original/'input.bin').stat().st_size!=op['input']['bytes']:
        raise ValueError('input truncated')
    if (original/'weight.bin').stat().st_size!=op['weight']['bytes']:
        raise ValueError('weight truncated')
    with (original/'input.bin').open('rb') as f:raw=f.read(8*4096*4)
    (out/'input_q8_from_q32.bin').write_bytes(raw)
    shutil.copyfile(original/'weight.bin',out/'weight.bin')
    shutil.copyfile(SRC/'receipt.json',out/'original_q32_receipt.json')
    references=[]
    for arm in ('backend_loop4','packed'):
        folder=Path('D:/rtx184-runs')/('O-replay-v5-8B-'+arm+'-clean')
        source=folder/NAME/'8.bin'
        if source.stat().st_size!=8*4096*4:raise ValueError('reference output truncated')
        dest=out/(arm+'_historical_q8_output.bin');shutil.copyfile(source,dest)
        timing=json.loads((folder/NAME/'8.json').read_bytes())
        inp=json.loads((folder/'input.json').read_bytes())
        if inp['replay']!='E:/rtx170/witness-8B/native' or inp['route']!=arm:
            raise ValueError('reference source binding mismatch')
        references.append(dict(arm=arm,source=entry(source),copy=entry(dest),
            launch_input=entry(folder/'input.json'),operator_record=entry(folder/NAME/'8.json'),
            width=timing['width'],timings_reused_as_round1=False))
    if references[0]['copy']['sha256']!=references[1]['copy']['sha256']:
        raise ValueError('historical A/B q8 outputs differ')
    manifest=dict(schema='heterospec.round1.derived-real-operand.v1',
        utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        status='DERIVED_Q8_REPLAY_NOT_ACTUAL_Q8_MODEL_CAPTURE',
        original_capture_width=32,derived_replay_width=8,
        derivation='First eight contiguous F32 columns from a real q32 projection input; same complete Q8_0 weight.',
        original_descriptor=op,original_receipt=entry(SRC/'receipt.json'),
        original_files=[entry(original/x) for x in ('input.bin','weight.bin','output.bin')],
        recovered_files=[entry(out/x) for x in ('input_q8_from_q32.bin','weight.bin','original_q32_receipt.json')],
        historical_q8_references=references,
        model_requests=0,kernel_launches=0,used_as_round1_performance=False,
        actual_q8_model_capture_requirement_satisfied=False,
        instruction='Do not publish weight.bin or claim this derived prefix is a natural q8 capture. Fresh admitted real-q8 capture remains required.')
    (out/'PROVENANCE.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print(json.dumps(dict(status=manifest['status'],directory=str(out),A_B_old_q8_equal=True)))

if __name__=='__main__':main()
