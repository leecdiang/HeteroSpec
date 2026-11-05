"""CPU-only cross-part transport/restore check, unrelated to GPU qualification."""
import hashlib,json,os,shutil,tempfile,zipfile,zlib
from pathlib import Path
import deliver_host as delivery
from restore_delivered_host import restore
from build_host import ROOT,put

def main():
    with tempfile.TemporaryDirectory(prefix='rtx184-delivery-check-',dir='D:/') as t:
        base=Path(t);delivery.OUT=base/'staging';delivery.OUT.mkdir();remote=base/'remote';remote.mkdir()
        def uploaded(p):
            shutil.copyfile(p,remote/p.name)
            return dict(name=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        delivery.upload=uploaded;writer=delivery.PartsWriter();writer.limit=1024*1024
        raw=os.urandom(2*1024*1024+193);chunks=[raw[i:i+1024*1024] for i in range(0,len(raw),1024*1024)];hashes=[hashlib.sha256(c).hexdigest() for c in chunks]
        row=dict(path='D:/selected/nested/state.bin',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),chunks=hashes)
        with zipfile.ZipFile(writer,'w') as z:
            for h,c in zip(hashes,chunks):z.writestr('chunks/'+h[:2]+'/'+h,zlib.compress(c,1))
            z.writestr('FILES.json',json.dumps(dict(files=[row,dict(row,path='D:/selected/same.bin')])) )
        writer.finish_part();index=remote/'raw-evidence.zip.parts.json';index.write_text(json.dumps(dict(parts=writer.parts)))
        restore(index,'D:/selected',base/'restored')
        assert (base/'restored/nested/state.bin').read_bytes()==raw and (base/'restored/same.bin').read_bytes()==raw
        put(ROOT/'ARTIFACT_TOOL_VALIDATION.json',dict(cpu_transport_only=True,cross_part_seek_zip=True,all_part_chunk_file_hashes_verified=True,duplicate_payload_hardlink_restore=True,parts=len(writer.parts),bytes=len(raw),gpu_qualification_claim=False))

if __name__=='__main__':main()
