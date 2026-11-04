"""Host F32 RN counterfactual only; not a GPU div.approx emulator.

Requires only the Python standard library. Original inputs are read-only.
"""
import argparse,base64,gzip,json,math,struct
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input-dir',type=Path,default=Path(__file__).parents[1],help='Directory containing authorized operand-sample.json.gz')
parser.add_argument('--output',type=Path,default=Path(__file__).with_name('division-counterfactual.json'),help='Destination JSON; defaults beside this script')
args=parser.parse_args()
P=args.input_dir
f32=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
round_away=lambda x:int(math.copysign(math.floor(abs(x)+0.5),x))
results={}
for name,blobs in json.load(gzip.open(P/'operand-sample.json.gz')).items():
 raw=base64.b64decode(blobs['input'],validate=True);xs=struct.unpack('<'+'f'*(len(raw)//4),raw);diff=[];ncol=4096 if 'attn_' in name else 12288
 for start in range(0,len(xs),32):
  amax=max(map(abs,xs[start:start+32]));d=f32(amax/127.0); inv=f32(1.0/d)
  for offset,x in enumerate(xs[start:start+32]):
   direct=f32(x/d);recip=f32(x*inv); qd=round_away(direct);qr=round_away(recip)
   if qd!=qr:diff.append({'linear_index':start+offset,'token':(start+offset)//ncol,'k':(start+offset)%ncol,'x':x,'amax':amax,'d':d,'inverse_d':inv,'direct_ratio':direct,'reciprocal_ratio':recip,'direct_q':qd,'reciprocal_q':qr})
 results[name]={'scope':'Host float32 RN counterfactual only; no claim about CUDA div.approx behavior','values':len(xs),'byte_differences':len(diff),'examples':diff}
print(json.dumps({k:{**v,'examples':v['examples'][:2]} for k,v in results.items()},indent=2))
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(results,indent=2)+'\n')
