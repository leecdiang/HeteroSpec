"""Publish bounded exception metadata, not arbitrary process memory."""
import argparse,base64,hashlib,json,struct
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--dump',required=True);p.add_argument('--diagnosis',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    d=Path(a.dump).read_bytes();u=lambda fmt,o:struct.unpack_from('<'+fmt,d,o)
    assert d[:4]==b'MDMP';count,directory=u('II',8);streams={}
    for i in range(count):
        kind,size,rva=u('III',directory+12*i);streams[kind]=(size,rva)
    size,rva=streams[6];context_size,context_rva=u('II',rva+160)
    report=json.loads(Path(a.diagnosis).read_bytes());assert hashlib.sha256(d).hexdigest()==report['dump']['sha256']
    # Selected context contains only thread register state (not stack/heap/env).
    ranges=[]
    if 9 in streams:
        _,at=streams[9];n,offset=u('QQ',at)
        for i in range(n):
            base,length=u('QQ',at+16+16*i);ranges.append((base,length,offset));offset+=length
    if 5 in streams:
        _,at=streams[5];n=u('I',at)[0]
        for i in range(n):
            base,length,offset=u('QII',at+4+16*i);ranges.append((base,length,offset))
    def memory(address,length):
        for base,size,offset in ranges:
            if base<=address and address+length<=base+size:return d[offset+address-base:offset+address-base+length]
        raise ValueError('requested bounded metadata not in dump')
    context=report['instruction_context'];code=bytes.fromhex(context['dump_hex']);start=int(context['start_RVA'],16)
    # Windows x64 MOV RCX,[RIP+disp32], followed by IDIV RCX in ggml_time_us.
    k=code.index(b'\x48\x8b\x0d');displacement=struct.unpack_from('<i',code,k+3)[0]
    global_rva=start+k+7+displacement
    module=next(m for m in report['loaded_module_metadata'] if m['path']==report['exception']['module'])
    frequency=memory(module['base']+global_rva,8)
    capsule=dict(source_dump_sha256=report['dump']['sha256'],source_dump_path=a.dump,
                 exception_stream_rva=rva,exception_stream_b64=base64.b64encode(d[rva:rva+size]).decode(),
                 context_rva=context_rva,thread_context_b64=base64.b64encode(d[context_rva:context_rva+context_size]).decode(),
                 fault_module=module,code_context_start_RVA=start,code_context_b64=base64.b64encode(code).decode(),
                 frequency_global_RVA=global_rva,frequency_bytes_b64=base64.b64encode(frequency).decode(),
                 disk_code_equal=report['instruction_context']['dump_disk_bytes_equal'],
                 retention='Complete original crash dump remains local read-only. Capsule exports bounded exception/register/code/frequency data only; no arbitrary memory or environment.')
    with Path(a.output).open('x',encoding='utf-8',newline='\n') as f:json.dump(capsule,f,indent=2);f.write('\n')
    print(json.dumps(dict(exception_code=hex(u('I',rva+8)[0]),frequency_global_RVA=hex(global_rva),frequency_value=struct.unpack('<q',frequency)[0],context_bytes=context_size)))
if __name__=='__main__':main()
