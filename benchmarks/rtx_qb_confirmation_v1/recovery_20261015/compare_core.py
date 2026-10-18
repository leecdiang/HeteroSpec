"""Compare authenticated old Python core with current core, including PE sections.

This is a CPU byte audit; it never executes the archived interpreter or a model.
"""
import hashlib,json,struct,tarfile
from pathlib import Path
ROOT=Path(__file__).parent
CURRENT=Path('C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/python')
def sha(b):return hashlib.sha256(b).hexdigest()
def pe(b):
    p=struct.unpack_from('<I',b,60)[0];assert b[p:p+4]==b'PE\0\0'
    count=struct.unpack_from('<H',b,p+6)[0];optional=struct.unpack_from('<H',b,p+20)[0]
    result=[]
    for i in range(count):
        off=p+24+optional+40*i;name=b[off:off+8].rstrip(b'\0').decode('ascii')
        size,pos=struct.unpack_from('<II',b,off+16)
        result.append(dict(name=name,size=size,sha256=sha(b[pos:pos+size])))
    # Compare complete headers too, allowing only PE checksum and certificate entry.
    end=p+24+optional+40*count;header=bytearray(b[:end]);header[p+24+64:p+24+68]=b'\0'*4
    magic=struct.unpack_from('<H',b,p+24)[0];directory=p+24+(112 if magic==0x20b else 96)
    header[directory+32:directory+40]=b'\0'*8
    return dict(sections=result,normalized_header_sha256=sha(header))
def main():
    rows=[];prefix='codex-primary-runtime/dependencies/python/'
    with tarfile.open(ROOT/'runtime-26.1011.11113.tar.gz') as tar:
        for member in tar:
            if not member.isfile() or not member.name.startswith(prefix):continue
            rel=member.name[len(prefix):]
            if rel.startswith(('Lib/site-packages/','Scripts/')) or '__pycache__' in rel:continue
            old=tar.extractfile(member).read();current=CURRENT/rel
            row=dict(path=rel,old_sha256=sha(old),bytes=len(old),current_exists=current.is_file())
            if current.is_file():
                new=current.read_bytes();row['current_sha256']=sha(new);row['byte_equal']=old==new
                if old!=new and rel.endswith(('.exe','.dll','.pyd')):
                    row['old_PE']=pe(old);row['current_PE']=pe(new);row['PE_code_and_headers_equal_excluding_authenticode_fields']=row['old_PE']==row['current_PE']
            rows.append(row)
    result=dict(core_files=len(rows),byte_differences=[r for r in rows if not r.get('byte_equal')],
                unsupported_differences=[r['path'] for r in rows if not r.get('byte_equal') and not r.get('PE_code_and_headers_equal_excluding_authenticode_fields')],
                files=rows)
    with (ROOT/'CORE_COMPARISON.json').open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(dict(core_files=len(rows),byte_differences=len(result['byte_differences']),unsupported_differences=result['unsupported_differences'])))
if __name__=='__main__':main()
