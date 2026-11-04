"""Exact-integer lattice model. Not a CUDA interpreter or deployed-binary proof."""
import json,random,struct,subprocess,ctypes,pathlib
if not __debug__: raise RuntimeError('Run without -O: assertions are verification checks')
HERE=pathlib.Path(__file__).resolve().parent
# Finite binary16 values represented in units of 2^-24, including signed zero as 0.
def half_units(h):
 e=(h>>10)&31;f=h&1023
 if e==31:raise ValueError('nonfinite')
 n=f if not e else (1024+f)<<(e-1)
 return -n if h&0x8000 else n
# Round integer units of 2^-48 to 24 significant bits, ties-to-even.
def rn_units(n):
 sign=-1 if n<0 else 1;n=abs(n);shift=max(0,n.bit_length()-24)
 if not shift:return sign*n
 q,r=divmod(n,1<<shift);half=1<<(shift-1)
 if r>half or (r==half and q&1):q+=1
 return sign*(q<<shift)

def main():
 finite=[h for h in range(65536)if h&0x7c00!=0x7c00]
 # Each half has <=11 significant bits; each product is exact in binary32.
 checks=0
 for h in finite:
  for other in (1,0x3c00,0x7bff,0x8001):
   s=half_units(h)*half_units(other)
   assert rn_units(s)==s;checks+=1
 rng=random.Random(181);updates=0
 for fused in (False,True):
  for case in range(2048):
   a=0
   for k in range(128):
    s=half_units(rng.choice(finite))*half_units(rng.choice(finite));d=rng.randrange(-131072,131073)
    a=rn_units(a+s*d)if fused else rn_units(a+rn_units(s*d))
    # Nonzero exact integer units imply magnitude >=2^-48, above 2^-126.
    assert a==0 or abs(a)>=1;assert abs(a).bit_length()-48<127;updates+=1
 # Domain-external FP32 examples, evaluated by a host helper with explicit FTZ model.
 cpp=HERE/'ftz_model.cpp';so=HERE/'ftz_model.so'
 subprocess.run(['g++','-shared','-fPIC','-O2','-ffp-contract=off',str(cpp),'-o',str(so)],check=True)
 lib=ctypes.CDLL(str(so));lib.case_bits.argtypes=[ctypes.c_int,ctypes.c_int];lib.case_bits.restype=ctypes.c_uint32
 negatives=[]
 for case in (0,1):
  normal=lib.case_bits(case,0);ftz=lib.case_bits(case,1);assert normal!=ftz
  negatives.append({'case':case,'nonftz':hex(normal),'modeled_ftz':hex(ftz),'in_candidate_finite_half_zero_acc_domain':False})
 lib.fma_witness.argtypes=[ctypes.c_int];lib.fma_witness.restype=ctypes.c_uint32
 fused,unfused=lib.fma_witness(1),lib.fma_witness(0);assert fused==0xc5bcb40b and unfused==0xc5bcb40c
 witness={'K':1056,'nonzero_blocks':[0,32],'dot8':[18897,-13817],'weight_half_bits':['0x3c00','0x3be9'],'activation_half_bits':['0x3c00','0x3f4d'],'fused_bits':hex(fused),'unfused_bits':hex(unfused),'within_finite_half_zero_acc_domain':True,'full_gpu_execution':'NOT_RUN'}
 result={'in_domain_fma_counterexample':witness,'status':'CPU_MODEL_ONLY','finite_half_encodings':len(finite),'exact_scale_checks':checks,'lattice_updates':updates,'domain_external_counterexamples':negatives,'quantizer':'NOT_MODELED','signed_zero':'integer lattice collapses signed zero; it proves absence of nonzero subnormals, not all zero-sign semantics','gpu_execution':'NOT_RUN'}
 (HERE/'DOMAIN_RESULTS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
