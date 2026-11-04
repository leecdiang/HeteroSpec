#!/usr/bin/env python3
"""Review existing CUDA artifacts and run host-only arithmetic checks.

Requires Python 3.11+, a GCC-compatible C++ compiler, and the system math library.
Does not compile CUDA, load the frozen DLL, or execute a GPU kernel.
All verification uses explicit exceptions, so python -O does not disable checks.
--output names a NEW JSON file; existing files are never overwritten.
"""
import argparse, ctypes, ctypes.util, hashlib, json, os, pathlib, re, shlex
import struct, subprocess, tempfile
from collections import Counter
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--audit',type=pathlib.Path,required=True,help='FTZ audit source directory')
parser.add_argument('--validation',type=pathlib.Path,required=True,help='Generated directory containing RECIPE_RESULTS.json and every recorded artifact')
parser.add_argument('--frozen-entries',type=pathlib.Path,required=True,help='Directory containing pinned long-name or short-name PTX entries')
parser.add_argument('--original-source',type=pathlib.Path,help='Optional original kernels.cu to compare with the audit copy')
parser.add_argument('--output',type=pathlib.Path,required=True,help='New review JSON file, not an output directory')
parser.add_argument('--cxx',default=os.environ.get('CXX','g++'),help='GCC-compatible host C++ command (default: CXX or g++)')
args=parser.parse_args()
AUDIT=args.audit.resolve();V=args.validation.resolve();OUTPUT=args.output.resolve()
if OUTPUT.exists(): raise RuntimeError('Refusing to overwrite existing output: '+str(OUTPUT))
EXPECTED_KERNEL='a8a465ac224ba8aa9613946edbe5cf7291a063f1a4c171f366a143aa82586bb9'
EXPECTED_DLL='8df3d5d6363dab0b221f143992e816d1366be4b076b47ce6b1612a148c0bc09c'
EXPECTED_HOST='43e7bae2c69e367d09985d40d78248e7ba3be08149e00bd4b4d35fc75f69a316'
EXPECTED_ENTRIES={
 'q1':('q8_mmvq_q1.sm90.ptx','ptx228_sm_90_*mul_mat_vec_qIL9ggml_type8ELi1ELb0ELb0ELb0*.ptx','f117281b6439072168d6b42cec93ce19b27ce089b64bd77effe8d3d3c7f1999e'),
 'q4':('q8_mmvq_q4.sm90.ptx','ptx228_sm_90_*mul_mat_vec_qIL9ggml_type8ELi4ELb0ELb0ELb0*.ptx','7d371052dce8d80f36801245b8c39ef04f40ed84d9781554c93f1c9ab684b7cb'),
 'quantizer':('quantize_q8_1.sm90.ptx','ptx288_sm_90_*quantize_q8_1*.ptx','6be2f3cf00f5feeeffb1d886c1c2d6e2d5bc9b3f629811f79ab6ae8d1559e2b1')}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def require(c,m):
 if not c: raise RuntimeError(m)
recipe=json.loads((V/'RECIPE_RESULTS.json').read_text())
require(recipe['candidate_kernel_sha256']==EXPECTED_KERNEL,'unpinned candidate hash')
require(recipe['frozen_dll_sha256']==EXPECTED_DLL,'unpinned DLL identity')
require(set(recipe['frozen_entries'])==set(EXPECTED_ENTRIES),'unexpected frozen entry set')
for name,h in recipe['artifact_sha256'].items():
 require(pathlib.Path(name).name==name,'artifact name must be a basename')
 require(sha(V/name)==h,'artifact hash '+name)
require({'sass.log','false.ptx','true.ptx','ftz.o'}.issubset(recipe['artifact_sha256']), 'missing key artifact hashes')
resolved_entries={}
for name,e in recipe['frozen_entries'].items():
 short,pattern,expected=EXPECTED_ENTRIES[name]
 require(e['sha256']==expected,'unpinned frozen entry hash '+name)
 matches=list(args.frozen_entries.glob(pattern))
 if (args.frozen_entries/short).is_file(): matches.append(args.frozen_entries/short)
 require(bool(matches),'missing frozen entry '+name)
 for f in matches: require(sha(f)==expected,'wrong frozen entry '+str(f))
 resolved_entries[name]=sorted(f.name for f in matches)
require(sha(AUDIT/'kernels-original.cu')==EXPECTED_KERNEL,'source hash')
if args.original_source:
 require(sha(args.original_source)==EXPECTED_KERNEL,'original source hash')
actual_ptx_counts={}
for mode in ('false','true'):
 ops=Counter(re.findall(r'\b(?:fma|add|mul)\.[\w.]*f32\b',(V/(mode+'.ptx')).read_text()))
 require(bool(ops),'missing FP PTX operations')
 require(all(('.ftz.' in op)==(mode=='true') for op in ops),'wrong PTX FTZ attribute')
 require(dict(ops)==recipe['ptx_opcode_counts'][mode],'PTX count mismatch')
 actual_ptx_counts[mode]=dict(ops)
sass=Counter(re.findall(r'\*/\s*(?:@!?P\d+\s+)?((?:FADD|FMUL|FFMA)(?:\.[A-Z0-9]+)*)\s', (V/'sass.log').read_text()))
require(sass and all('.FTZ' in x for x in sass), 'non-FTZ scalar SASS')
# Independently execute host-only fused/unfused witness, contracting disabled.
require(sha(AUDIT/'ftz_model.cpp')==EXPECTED_HOST,'unpinned host helper source')
HOST_TMP=tempfile.TemporaryDirectory(prefix='ftz-independent-review-')
so=pathlib.Path(HOST_TMP.name)/'ftz_host_independent.so'
subprocess.run(shlex.split(args.cxx)+['-shared','-fPIC','-O2','-ffp-contract=off',str(AUDIT/'ftz_model.cpp'),'-o',str(so)],check=True)
lib=ctypes.CDLL(str(so));lib.fma_witness.argtypes=[ctypes.c_int];lib.fma_witness.restype=ctypes.c_uint32
fb,ub=lib.fma_witness(1),lib.fma_witness(0)
require((fb,ub)==(0xc5bcb40b,0xc5bcb40c), 'FMA witness')
f32=lambda x: struct.unpack('<f',struct.pack('<f',x))[0]
bits=lambda x: struct.unpack('<I',struct.pack('<f',x))[0]
half=lambda h: struct.unpack('<e',struct.pack('<H',h))[0]
# Different implementation from the integer lattice model: actual half decode,
# double products (exact for <=22-bit significands), and FP32 roundtrip.
checks=0
for h in range(65536):
 if h&0x7c00==0x7c00: continue
 for k in (1,0x3c00,0x7bff,0x8001):
  p=half(h)*half(k)
  require(f32(p)==p, 'inexact half scale product')
  require((p*2**48).is_integer(), 'scale off lattice')
  checks+=1
w0=[127,127,101,0,0,0,0,0];y0=[127,21,1,0,0,0,0,0]
w1=[-127,-101,0,0,0,0,0,0];y1=[108,1,0,0,0,0,0,0]
d0=sum(a*b for a,b in zip(w0,y0));d1=sum(a*b for a,b in zip(w1,y1))
require((d0,d1)==(18897,-13817), 'signed-byte dots')
x=struct.unpack('<f',struct.pack('<I',0x007fffff))[0]
d=f32(x/127);ratio=f32(x/d)
# Independent external-domain witness: all normal inputs, subnormal result.
math_library=ctypes.util.find_library('m')
require(bool(math_library),'system math library not found')
libm=ctypes.CDLL(math_library);libm.fmaf.argtypes=[ctypes.c_float]*3;libm.fmaf.restype=ctypes.c_float
frombits=lambda b: struct.unpack('<f',struct.pack('<I',b))[0]
fma_external=bits(libm.fmaf(frombits(0x00800000),1.0,frombits(0x80800001)))
require(fma_external==0x80000001,'normal-input cancellation witness')
report={
 'status':'INDEPENDENT_STATIC_AND_CPU_REVIEW_ONLY_NOT_FROZEN_R_EQUIVALENCE',
 'reviewed_candidate_sha256':recipe['candidate_kernel_sha256'],
 'review_script_sha256':sha(pathlib.Path(__file__)),
 'reviewed_audit_input_sha256':{name:sha(AUDIT/name) for name in ('kernels-original.cu','ftz_model.cpp','test_fma_witness.cu','audit_recipe.py','check_domain.py')},
 'resolved_frozen_entry_filenames':resolved_entries,
 'actual_ptx_opcode_counts':actual_ptx_counts,
 'recorded_gpu_execution':recipe.get('gpu_execution','UNSPECIFIED'),
 'verification_checks_use_assert':False,
 'reviewed_recipe_sha256':sha(V/'RECIPE_RESULTS.json'),
 'reviewed_domain_results_sha256':sha(AUDIT/'DOMAIN_RESULTS.json'),
 'reviewed_readme_sha256':sha(AUDIT/'README.md'),
 'checks':{'all_recorded_artifact_hashes_verified':True,'extracted_frozen_entry_hashes_verified':True,'dll_itself_rehashed_in_this_review':False,'source_matches_original':True if args.original_source else None,'scalar_sass_opcode_counts':dict(sass),'non_ftz_scalar_sass_ops':0,'independent_actual_half_exact_scale_checks':checks,'signed_byte_dot8':[d0,d1],'host_fused_bits':hex(fb),'host_unfused_bits':hex(ub)},
 'findings':[
  'Original PR181 build is non-FTZ; actual frozen q1/q4 entries are scale-first fused FTZ. The separate -ftz=true build aligns scalar operation flags only.',
  'Only fused=true is a candidate for the observed update recipe. K=1056 with nonzero blocks0/32 gives a reachable prequantized fused/unfused difference, confirmed on the host helper, not a GPU.',
  'Within actual finite-half scales, exact integer dot8, RN operations, +0 initial state, no bias/external accumulator, and the positive int K bound, all finite arithmetic stays on the 2^-48 lattice and cannot reach a nonzero FP32 subnormal. FTZ alone is dormant in this restricted domain.',
  'The no-overflow bound uses each term <2^49, at most2^21 terms per lane chain, RN unit roundoff2^-24, chain magnitude <2^71, and conservative reduction bound <2^79.',
  'The integer lattice model collapses signed zero. Absence of nonzero subnormals plus sign-preserving FTZ explains why FTZ itself cannot change zero signs here; other compiler/dataflow zero-sign equivalence is not proved.',
  'Finite F32 quantizer input is insufficient for the finite-half premise: amax=2^24 yields d about132104 and half +Inf. Quantizer div.approx.ftz is outside this projection proof.',
  'The 253952 scale checks cover all finite half encodings against four partners, not all possible pairs. The 524288 lattice updates are model tests, not a CUDA interpreter or device execution.',
  'The real q4 merge may reverse add operand order relative to q1. Finite add commutativity does not establish NaN payload preservation.'
 ],
 'domain_external_examples':{
  'all_normal_fma_inputs':{'scale':'0x00800000','dot':'0x3f800000','acc':'0x80800001','host_rn_result':hex(fma_external),'ptx_ftz_result_inferred_not_device_tested':'0x80000000','not_reachable_from_finite_half_projection':True},
  'quantizer_subnormal_input':{'x':'0x007fffff','host_rn_d_bits':hex(bits(d)),'host_rn_ratio':ratio,'host_nonftz_q':127,'frozen_ftz_abs_amax_zero_implies_q':0,'both_saved_half_scales':0,'byte_mismatch_not_projection_output_mismatch':True}
 },
 'limits':['No GPU execution by this review. Any witness execution status is only the selected external receipt, reported separately.','No frozen-R numerical equivalence, lane/address proof from the binary, driver-JIT equivalence, nonfinite/NaN-payload proof, quantizer qualification, runtime enablement, or performance result.','The sm89/sm120a experiment uses CUDA13.2.2, not the original compiler or deployed sm120 JIT.'],
 'primary_spec':'https://docs.nvidia.com/cuda/parallel-thread-execution/',
 'verified_artifact_sha256':recipe['artifact_sha256'],
 'verified_frozen_entry_sha256':{k:v['sha256'] for k,v in recipe['frozen_entries'].items()}
}
OUTPUT.parent.mkdir(parents=True,exist_ok=True)
with OUTPUT.open('x') as f: f.write(json.dumps(report,indent=2)+'\n')
print(str(OUTPUT));print(sha(OUTPUT));print(json.dumps(report['checks'],indent=2))
HOST_TMP.cleanup()
