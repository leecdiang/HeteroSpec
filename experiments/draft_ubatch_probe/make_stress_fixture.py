#!/usr/bin/env python3
"""Derive a separate synthetic diagnostic model; never edit the input GGUF."""
import argparse,pathlib,hashlib,json,shutil
import gguf
p=argparse.ArgumentParser();p.add_argument('--input',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
raw=a.input.read_bytes();pin='5b9aeb4e2b843d0d3f70072fe2dd22131387a86a984332da5571e717844d063c'
if hashlib.sha256(raw).hexdigest()!=pin:raise ValueError('unexpected synthetic source model')
if a.output.exists():raise ValueError('fresh output required')
r=gguf.GGUFReader(str(a.input));ranges=[];modified=bytearray(raw)
for t in r.tensors:
 if t.name.endswith('norm.weight'):
  if int(t.tensor_type)!=0 or t.n_bytes!=t.n_elements*4:raise ValueError('not F32 norm')
  lo=int(t.data_offset);hi=lo+int(t.n_bytes)
  modified[lo:hi]=b'\x00\x00\x80\x3f'*int(t.n_elements)
  ranges.append({'tensor':t.name,'offset':lo,'bytes':int(t.n_bytes)})
if len(ranges)!=5:raise ValueError('expected five norm tensors')
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(modified)
a.output.with_suffix('.json').write_text(json.dumps({'source_sha256':pin,'output_sha256':hashlib.sha256(modified).hexdigest(),'change':'F32 synthetic RMS norm weights set to1; all other bytes unchanged','changed_ranges':ranges,'trained_model':False},indent=2)+'\n')
