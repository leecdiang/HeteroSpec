#!/usr/bin/env python3
"""Validation/tamper negatives, including optimizer modes. Never touches originals."""
import argparse,base64,copy,gzip,hashlib,importlib.util,json,pathlib,subprocess,sys,tempfile,unittest
import numpy as np

ROOT=pathlib.Path(__file__).resolve().parent
_inputs=argparse.ArgumentParser(add_help=False);_inputs.add_argument('--input-dir',type=pathlib.Path,default=ROOT)
INPUT_ROOT=_inputs.parse_known_args()[0].input_dir.resolve()
spec=importlib.util.spec_from_file_location('operand_probe',ROOT/'probe.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
DESC=json.loads(gzip.decompress((INPUT_ROOT/'operands.json.gz').read_bytes()))
SAMPLE=json.loads(gzip.decompress((INPUT_ROOT/'operand-sample.json.gz').read_bytes()))

class ValidationTests(unittest.TestCase):
 def rejected(self,fn,message):
  with self.assertRaisesRegex(probe.ValidationError,message):fn()
 def test_01_explicit_require(self):
  self.rejected(lambda:probe.require(False,'sentinel'),'sentinel')
 def test_02_rounding_mode(self):
  self.rejected(lambda:probe.require_rounding_mode(1024),'FE_TONEAREST')
 def test_03_unknown_evidence(self):
  self.rejected(lambda:probe.validate_compressed('unknown',b''),'Unknown evidence')
 def test_04_compressed_length(self):
  name='operands.json.gz';b=(INPUT_ROOT/name).read_bytes()
  self.rejected(lambda:probe.validate_compressed(name,b[:-1]),'compressed byte length')
 def test_05_compressed_digest_same_length(self):
  name='operands.json.gz';b=bytearray((INPUT_ROOT/name).read_bytes());b[4]^=1
  # Valid gzip, identical uncompressed JSON, but a different pinned artifact.
  self.assertEqual(gzip.decompress(b),gzip.decompress((INPUT_ROOT/name).read_bytes()))
  self.rejected(lambda:probe.validate_compressed(name,bytes(b)),'compressed SHA256')
 def test_06_git_blob_digest(self):
  name='operands.json.gz';b=(INPUT_ROOT/name).read_bytes();old=probe.EXPECTED[name]
  try:
   probe.EXPECTED[name]=(old[0],'0'*40,old[2])
   self.rejected(lambda:probe.validate_compressed(name,b),'Git blob SHA1')
  finally:probe.EXPECTED[name]=old
 def test_07_invalid_base64(self):
  self.rejected(lambda:probe.decode_blob('!!!!','0'*64,3,'fixture'),'invalid base64')
 def test_08_decoded_length(self):
  self.rejected(lambda:probe.decode_blob(base64.b64encode(b'abc'),probe.sha(b'abc'),4,'fixture'),'decoded byte length')
 def test_09_decoded_digest(self):
  self.rejected(lambda:probe.decode_blob(base64.b64encode(b'abd'),probe.sha(b'abc'),3,'fixture'),'decoded SHA256')
 def test_10_descriptor_type(self):
  d=copy.deepcopy(DESC[0]);d['descriptor']['weight']['type']=0
  self.rejected(lambda:probe.validate_descriptor(d),'tensor type')
 def test_11_descriptor_shape(self):
  d=copy.deepcopy(DESC[0]);d['descriptor']['output']['ne'][2]=2
  self.rejected(lambda:probe.validate_descriptor(d),'tensor shape')
 def test_12_descriptor_bytes(self):
  d=copy.deepcopy(DESC[0]);d['descriptor']['input']['bytes']+=4
  self.rejected(lambda:probe.validate_descriptor(d),'byte size')
 def test_13_descriptor_strides(self):
  d=copy.deepcopy(DESC[0]);d['descriptor']['weight']['nb'][1]+=2
  self.rejected(lambda:probe.validate_descriptor(d),'stride')
 def test_14_descriptor_dimensions(self):
  d=copy.deepcopy(DESC[0]);d['descriptor']['weight']['ne'][0]=31
  self.rejected(lambda:probe.validate_descriptor(d),'dimensions')
 def test_15_missing_record(self):
  self.rejected(lambda:probe.one([],'fixture'),'exactly one')
 def test_16_duplicate_record(self):
  self.rejected(lambda:probe.one([1,2],'fixture'),'exactly one')
 def test_17_compare_shape(self):
  self.rejected(lambda:probe.compare(np.ones(2,dtype='<f4'),np.ones(3,dtype='<f4'),1),'shape')
 def test_18_compare_nonfinite(self):
  self.rejected(lambda:probe.compare(np.array([np.nan],dtype='<f4'),np.ones(1,dtype='<f4'),1),'finite')
 def test_19_compare_dtype(self):
  self.rejected(lambda:probe.compare(np.ones(1,dtype='<f8'),np.ones(1,dtype='<f8'),1),'F32')
 def test_20_quantizer_zero_block(self):
  self.rejected(lambda:probe.nominal_quantizer(np.zeros(32,dtype='<f4'),32),'nonzero blocks')
 def test_21_quantizer_nonfinite(self):
  self.rejected(lambda:probe.nominal_quantizer(np.full(32,np.inf,dtype='<f4'),32),'finite input')
 def test_22_quantizer_shape(self):
  self.rejected(lambda:probe.nominal_quantizer(np.ones(32,dtype='<f4'),31),'shape')
 def test_23_positive_controls(self):
  for d in DESC:probe.validate_descriptor(d)
  raw=b'abc';self.assertEqual(probe.decode_blob(base64.b64encode(raw),probe.sha(raw),3,'fixture'),raw)
  self.assertEqual(probe.one([4],'fixture'),4);probe.require_rounding_mode(0)


def run_child_tests():
 result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(ValidationTests))
 return 0 if result.wasSuccessful() else 1

def run_matrix(output):
 records=[]
 originals={name:(INPUT_ROOT/name).read_bytes() for name in probe.EXPECTED}
 fingerprints={name:hashlib.sha256(b).hexdigest() for name,b in originals.items()}
 baseline=None
 for mode in [[],['-O'],['-OO']]:
  label='normal' if not mode else mode[0]
  p=subprocess.run([sys.executable,*mode,__file__,'--worker','--input-dir',str(INPUT_ROOT)],text=True,capture_output=True)
  if p.returncode:raise RuntimeError(f'{label} unit negative suite failed: {p.stdout}\n{p.stderr}')
  records.append(dict(mode=label,case='unit_suite',tests=23,returncode=p.returncode,stderr=p.stderr.strip()))
  with tempfile.TemporaryDirectory(prefix='operand-negative-') as td:
   tmp=pathlib.Path(td)
   for name,b in originals.items():(tmp/name).write_bytes(b)
   def cli(case,changed_name=None,changed_bytes=None,expected_message=None):
    if changed_name:(tmp/changed_name).write_bytes(changed_bytes)
    dest=tmp/f'{case}.json'
    p=subprocess.run([sys.executable,*mode,str(ROOT/'probe.py'),'--input-dir',str(tmp),'--output',str(dest)],text=True,capture_output=True)
    if changed_name:(tmp/changed_name).write_bytes(originals[changed_name])
    if expected_message:
     if p.returncode!=2 or dest.exists() or expected_message not in p.stderr:
      raise RuntimeError(f'{label} {case} did not reject safely: rc={p.returncode}, output={dest.exists()}, stderr={p.stderr}')
    else:
     if p.returncode!=0 or not dest.exists():raise RuntimeError(f'{label} {case} positive failed: {p.stderr}')
    records.append(dict(mode=label,case=case,returncode=p.returncode,output_written=dest.exists(),stderr=p.stderr.strip()))
    return dest.read_bytes() if dest.exists() else None
   clean=cli('valid_pinned_evidence')
   if baseline is None:baseline=clean
   elif clean!=baseline:raise RuntimeError(f'{label} valid result differs from normal Python')
   for name,b in originals.items():
    stem=name.split('.')[0]
    cli(stem+'_truncated',name,b[:-1],'compressed byte length mismatch')
    mutated=bytearray(b);mutated[4]^=1
    if gzip.decompress(mutated)!=gzip.decompress(b):raise RuntimeError('Header-only corruption fixture is not content-preserving')
    cli(stem+'_valid_gzip_header_tamper',name,bytes(mutated),'compressed SHA256 mismatch')
   # Genuine decoded sample byte alteration, reserialized into a valid gzip.
   sample=copy.deepcopy(SAMPLE);name=next(iter(sample));raw=bytearray(base64.b64decode(sample[name]['input']));raw[0]^=1
   sample[name]['input']=base64.b64encode(raw).decode()
   altered=gzip.compress(json.dumps(sample,separators=(',',':')).encode(),mtime=0)
   cli('actual_operand_byte_tamper','operand-sample.json.gz',altered,'mismatch')
 for name,h in fingerprints.items():
  if hashlib.sha256((INPUT_ROOT/name).read_bytes()).hexdigest()!=h:raise RuntimeError(f'Original input changed: {name}')
 out=dict(status='PASS',scope='Validation behavior only; no GPU execution or div.approx emulation',modes=['normal','-O','-OO'],unit_tests_per_mode=23,unit_test_executions=69,cli_positive_executions=3,cli_tamper_negative_executions=15,positive_output_files_byte_identical_across_modes=True,original_input_sha256=fingerprints,records=records)
 output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='records'},indent=2))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--worker',action='store_true');parser.add_argument('--input-dir',type=pathlib.Path,default=INPUT_ROOT);parser.add_argument('--output',type=pathlib.Path,default=ROOT/'validation_tests.json');args=parser.parse_args()
 if args.worker:sys.exit(run_child_tests())
 run_matrix(args.output)
