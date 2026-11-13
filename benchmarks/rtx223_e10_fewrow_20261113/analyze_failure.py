"""CPU-only preservation and complete logical differences; never loads CUDA."""
from pathlib import Path
import json,hashlib,shutil,csv,struct,math,datetime
p=Path(__file__).resolve().parent
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
def write(q,v):
 with q.open('x',encoding='utf8') as f:json.dump(v,f,indent=2)
stage=json.loads((p/'STAGING.json').read_bytes());profile=Path(stage['profile'])
files=[]
for q in sorted(profile.parent.rglob('*')):
 if q.is_file():
  dest=p/'evidence/profile'/q.relative_to(profile.parent);dest.parent.mkdir(exist_ok=True,parents=True);shutil.copy2(q,dest)
  assert sha(q)==sha(dest)
  files.append(dict(original=str(q),preserved=str(dest),sha256=sha(q),bytes=q.stat().st_size))
write(p/'PROFILE_DATA_PRESERVED.json',dict(files=files,utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
receipt=Path('D:/HeteroSpec-PC/rtx223-e10-fewrow')
for dirname in ('cpu-001','qualification-001'):
 for q in (receipt/dirname).iterdir():
  if q.is_file():
   dest=p/'evidence'/dirname/q.name;dest.parent.mkdir(exist_ok=True,parents=True);shutil.copy2(q,dest)
   assert sha(q)==sha(dest)
qual=p/'evidence/profile/AC/Temp/e10-qualification-001'
q=(qual/'U-r0-activation.bin').read_bytes();y=(qual/'U-r0-output.bin').read_bytes()
s=Path(stage['stage']);x=(s/'activation.f32').read_bytes();oldq=(s/'activation_q8_1.bin').read_bytes();oldy=(s/'backend-output.f32').read_bytes()
f=lambda data,i:struct.unpack_from('<f',data,i)[0]
bits=lambda a:struct.unpack('<I',struct.pack('<f',a))[0]
rn=lambda a:struct.unpack('<f',struct.pack('<f',a))[0]
qdiff=[];scales=[];near=0
for c in range(8):
 for b in range(128):
  amax=max(abs(f(x,(c*4096+b*32+k)*4)) for k in range(32));inv=rn(127/amax)
  dy=f(q,((b//8)*144+128+4*(c//2)+(b%8)//2)*16+(2*(b%2)+c%2)*4)
  legacyd=struct.unpack_from('<e',oldq,(c*128+b)*36)[0]
  scales.append(dict(column=c,block=b,U_scale=dy,legacy_half_scale=legacyd,CPU_RN_scale=rn(1/inv)))
  for k in range(32):
   off=((b//8)*144+(b%8//2)*32+4*c+(k%16)//4)*16+(2*(b%2)+k//16)*4+k%4
   got=struct.unpack_from('b',q,off)[0];value=f(x,(c*4096+b*32+k)*4);product=rn(value*inv)
   expected=int(math.copysign(math.floor(abs(product)+.5),product));old=struct.unpack_from('b',oldq,(c*128+b)*36+4+k)[0]
   if got!=expected or got!=old:
    dist=abs(abs(product)-(math.floor(abs(product))+.5));near+=got!=expected and dist<=2**-16
    qdiff.append(dict(column=c,block=b,k=k,activation=value,amax=amax,CPU_RN_inverse=inv,CPU_RN_product=product,CPU_expected=expected,U=got,legacy=old,CPU_mismatch=got!=expected,legacy_mismatch=got!=old,distance_to_half=dist))
odiff=[]
for i in range(32768):
 a=f(y,i*4);b=f(oldy,i*4)
 if bits(a)!=bits(b):odiff.append(dict(column=i//4096,row=i%4096,U=a,legacy=b,U_bits=hex(bits(a)),legacy_bits=hex(bits(b)),absolute_difference=abs(a-b)))
for name,rows in [('QUANT_DIFFERENCES.csv',qdiff),('SCALE_DIFFERENCES.csv',scales),('OUTPUT_DIFFERENCES.csv',odiff)]:
 with (p/name).open('x',newline='',encoding='utf8') as fp:
  w=csv.DictWriter(fp,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
cpuwrong=[r for r in qdiff if r['CPU_mismatch']]
assert len(cpuwrong)==10 and len(odiff)==32766
for repeat in (0,1):
 assert (qual/('B-r'+str(repeat)+'-activation.bin')).read_bytes()==oldq
 assert (qual/('B-r'+str(repeat)+'-output.bin')).read_bytes()==oldy
write(p/'DIFFERENCES.json',dict(CPU_wrong_quant=10,legacy_wrong_quant=sum(r['legacy_mismatch'] for r in qdiff),legacy_wrong_scales=1024,legacy_wrong_output_bits=len(odiff),CPU_wrong_at_half_threshold=near,CPU_max_quant_error=max(abs(r['U']-r['CPU_expected']) for r in cpuwrong),CPU_complete_B_replays=2,raw_U_repeat_NOT_RUN=True,diagnosis='All10 CPU mismatches are at/near rounding half thresholds, each differs by1. Source uses GPU division under -use_fast_math; CPU RN division is not guaranteed identical. This supports a quantization-oracle/fast-divide compatibility issue, not proof of an upstream arithmetic bug. No contract loosening or further GPU work.',timing='NOT_RUN'))
print(json.dumps(dict(preserved_files=len(files),CPU_quant_differences=len(cpuwrong),near_half=near,output_differences=len(odiff))))
