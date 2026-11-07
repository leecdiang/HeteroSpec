"""Recover the retained width-eight case and collect scalar Q operands in order."""
from host import *
def execute():
    old=FROZEN.parent/"probes/tilefix/0-8-QB-local"
    cfg=read(old/"input.json")["units"][0]
    assert cfg["base"]==0 and cfg["width"]==8 and cfg["tokens"]==[113+(i*173)%2309 for i in range(8)]
    for m in ("0.6B","8B"):
        launch("scalar-"+m,"witness02",dict(units=[unit("qrows","capture","S1",0,32),unit("width8","capture","native",0,8)]),m)
    comparisons=[]
    for m in ("0.6B","8B"):
        base=ROOT/("scalar-"+m);p=base/"qrows/blk.0.attn_q.weight"
        wide=ROOT/("witness-"+m)/"native/blk.0.attn_q.weight"
        scalar_input=b"".join((p/str(i)/"input.bin").read_bytes() for i in range(32))
        scalar_out=b"".join((p/str(i)/"output.bin").read_bytes() for i in range(32))
        replay=ROOT/("replay-"+m)/"blk.0.attn_q.weight"
        comparisons.append(dict(model=m,scalar_input_equals_live_wide=scalar_input==(wide/"input.bin").read_bytes(),
            scalar_live_equals_same_operand_scalar=scalar_out==(replay/"32-scalar.bin").read_bytes(),
            weight_equal=sha(p/"weight.bin")==sha(wide/"weight.bin"),first_q_diff=scalar_out!=(wide/"output.bin").read_bytes(),
            direct_width8_equals_replay=(base/"width8/blk.0.attn_q.weight/output.bin").read_bytes()==(replay/"8-wide.bin").read_bytes()))
    assert all(all(v for k,v in x.items() if k!="model") for x in comparisons)
    matches=[sha(ROOT/"scalar-0.6B/width8"/f"{i}.f32")==sha(old.parent/"0-8-native/row"/f"{i}.f32") for i in range(8)]
    put(ROOT/"first-divergence.json",dict(first=comparisons,retained_native_rows_equal=matches,
        retained_qb4_wide_projection_failure_rows=[i for i in range(8) if sha(old/"row"/f"{i}.f32")!=sha(old.parent/"0-8-oracle/row"/f"{i}.f32")]))
if __name__=="__main__":execute()

