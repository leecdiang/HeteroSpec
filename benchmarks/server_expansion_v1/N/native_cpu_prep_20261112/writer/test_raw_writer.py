import json
import os
import struct
import tempfile
import unittest
from pathlib import Path
from raw_writer import CaptureWriter, OwnedTensor, CaptureError

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
    def tearDown(self):
        self.tmp.cleanup()
    def writer(self, name='capture', **kwargs):
        return CaptureWriter(self.root, name, run_id='r', operation_id='o', context_id='c',
                             source_sha256='a'*64, executable_sha256='b'*64, **kwargs)
    def tensor(self):
        return OwnedTensor(struct.pack('<ff', 1., -0.), 'F32LE', [1,2], ['row','vocabulary'])
    def test_roundtrip_and_explicit_synthetic(self):
        with self.writer() as w:
            d=w.tensor('vectors',self.tensor()); receipt=w.commit()
        self.assertEqual((self.root/d['file']).read_bytes(), self.tensor().raw)
        self.assertEqual(json.loads((self.root/'capture/COMPLETE.json').read_text()), receipt)
        self.assertEqual(receipt['schema'],'hs.N1a.synthetic-capture.v1')
        self.assertFalse(receipt['native_qualified'])
    def test_ownership(self):
        source=bytearray(struct.pack('<f',1.)); owned=OwnedTensor(source,'F32LE',[1],['v'])
        source[:]=struct.pack('<f',2.)
        self.assertEqual(owned.raw,struct.pack('<f',1.))
    def test_overwrite(self):
        with self.writer() as w: w.tensor('vectors',self.tensor()); w.commit()
        with self.assertRaises(FileExistsError): self.writer()
    def test_duplicate(self):
        with self.writer() as w:
            w.tensor('v',self.tensor())
            with self.assertRaises(CaptureError): w.tensor('v',self.tensor())
    def test_symlink(self):
        (self.root/'link').symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(CaptureError):
            CaptureWriter(self.root/'link','x',run_id='r',operation_id='o',context_id='c',source_sha256='a'*64,executable_sha256='b'*64)
    def test_destination_symlink(self):
        with self.writer() as w:
            (self.root/'capture/v.bin').symlink_to(self.root/'external')
            with self.assertRaises(FileExistsError): w.tensor('v',self.tensor())
            with self.assertRaises(CaptureError): w.commit()
        self.assertFalse((self.root/'external').exists())
    def test_short_writes_supported(self):
        def short(fd,data): return os.write(fd,data[:1])
        with self.writer(write=short) as w: w.tensor('v',self.tensor()); w.commit()
        self.assertTrue((self.root/'capture/COMPLETE.json').exists())
    def test_zero_write_fails_closed(self):
        with self.writer(write=lambda fd,data:0) as w:
            with self.assertRaises(CaptureError): w.tensor('v',self.tensor())
            with self.assertRaises(CaptureError): w.commit()
        self.assertFalse((self.root/'capture/COMPLETE.json').exists())
    def test_partial_write_failure_preserved(self):
        calls=[0]
        def fault(fd,data):
            calls[0]+=1
            if calls[0]>1: raise OSError('injected disk failure')
            return os.write(fd,data[:1])
        with self.writer(write=fault) as w:
            with self.assertRaises(OSError): w.tensor('v',self.tensor())
        self.assertEqual((self.root/'capture/v.bin').stat().st_size,1)
        self.assertFalse((self.root/'capture/COMPLETE.json').exists())
    def test_nonfinite_f32(self):
        for v in [float('nan'),float('inf'),-float('inf')]:
            with self.assertRaises(CaptureError): OwnedTensor(struct.pack('<f',v),'F32LE',[1],['v'])
    def test_nonfinite_f16(self):
        for bits in [0x7c00,0xfc00,0x7e00]:
            with self.assertRaises(CaptureError): OwnedTensor(struct.pack('<H',bits),'F16LE',[1],['v'])
    def test_wrong_shape(self):
        for shape in [[True],[2],[-1],[1.0]]:
            with self.assertRaises(CaptureError): OwnedTensor(b'\0'*4,'F32LE',shape,['v'])
    def test_unsafe_name(self):
        for name in ['../x','a/b','','.','a\\b']:
            with self.assertRaises(CaptureError): self.writer(name)
    def test_empty_tensor_permitted_for_reset(self):
        with self.writer() as w:
            d=w.tensor('active_k',OwnedTensor(b'','F16LE',[36,8,0,128],['layer','kv_head','position','dimension']));w.commit()
        self.assertEqual(d['bytes'],0)
    def test_constructor_fsync_failure_closes_both_fds(self):
        from unittest.mock import patch
        opened=[]
        real_open=os.open
        def tracked_open(*args,**kwargs):
            fd=real_open(*args,**kwargs);opened.append(fd);return fd
        with patch('raw_writer.os.open',side_effect=tracked_open), patch('raw_writer.os.fsync',side_effect=OSError('injected fsync failure')):
            with self.assertRaises(OSError): self.writer()
        self.assertEqual(len(opened),2)
        for fd in opened:
            with self.assertRaises(OSError): os.fstat(fd)
        self.assertTrue((self.root/'capture').is_dir())
        self.assertFalse((self.root/'capture/COMPLETE.json').exists())
    def test_owned_immutable(self):
        from dataclasses import FrozenInstanceError
        t=self.tensor()
        with self.assertRaises(FrozenInstanceError): t.dtype='F16LE'
    def test_descriptor_isolated(self):
        with self.writer() as w:
            d=w.tensor('v',self.tensor()); d['shape'][0]=999
            receipt=w.commit()
        self.assertEqual(receipt['tensors']['v']['shape'],[1,2])
    def test_manifest_failure_not_completed(self):
        with self.writer() as w:
            w.tensor('v',self.tensor())
            w._write=lambda fd,data:0
            with self.assertRaises(CaptureError): w.commit()
        self.assertFalse((self.root/'capture/COMPLETE.json').exists())
    def test_closed_writer(self):
        with self.writer() as w: w.tensor('v',self.tensor());w.commit()
        with self.assertRaises(CaptureError): w.tensor('q',self.tensor())

if __name__=='__main__': unittest.main(verbosity=2)
