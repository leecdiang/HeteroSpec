"""Offline PE/minidump exception metadata only; no execution or GPU query.

Never export arbitrary memory, environment, the complete dump or WER attachments.
The original OS-created dump remains read-only locally with a hash reference.
"""
import argparse, hashlib, json, struct
from pathlib import Path

def inspect(dump, dll):
    data=Path(dump).read_bytes(); u=lambda fmt,o:struct.unpack_from('<'+fmt,data,o)
    assert data[:4]==b'MDMP'
    count,directory=u('II',8);streams={}
    for i in range(count):
        kind,size,rva=u('III',directory+12*i);streams[kind]=(size,rva)
    def string(rva):
        length=u('I',rva)[0];return data[rva+4:rva+4+length].decode('utf-16-le')
    size,rva=streams[4];n=u('I',rva)[0];modules=[]
    for i in range(n):
        at=rva+4+108*i;base,length,checksum,timestamp,name=u('QIIII',at)
        modules.append(dict(path=string(name),base=base,image_size=length,timestamp=timestamp))
    size,rva=streams[6];thread=u('I',rva)[0];code,flags,record,address,parameters=u('IIQQI',rva+8)
    context_size,context_rva=u('II',rva+160)
    registers={name:u('Q',context_rva+off)[0] for name,off in zip(('RAX','RCX','RDX','RBX','RSP','RBP','RSI','RDI','R8','R9','R10','R11','R12','R13','R14','R15','RIP'),range(120,256,8))}
    fault=next(m for m in modules if m['base']<=address<m['base']+m['image_size'])
    pe=Path(dll).read_bytes();v=lambda fmt,o:struct.unpack_from('<'+fmt,pe,o)
    nt=v('I',0x3c)[0];assert pe[nt:nt+4]==b'PE\0\0'
    section_count=v('H',nt+6)[0];optional_size=v('H',nt+20)[0];optional=nt+24;assert v('H',optional)[0]==0x20b
    sections=[]
    for i in range(section_count):
        p=optional+optional_size+40*i
        virtual_size,virtual_address,raw_size,raw_pointer=v('IIII',p+8)
        sections.append((virtual_address,max(virtual_size,raw_size),raw_pointer))
    def file_offset(rva):
        for va,sz,raw in sections:
            if va<=rva<va+sz:return raw+rva-va
        raise ValueError('RVA outside section')
    export_rva=v('I',optional+112)[0];e=file_offset(export_rva)
    ordinal_base,num_functions,num_names,functions,names,ordinals=v('IIIIII',e+16)
    exports=[]
    for i in range(num_names):
        name_rva=v('I',file_offset(names)+4*i)[0];p=file_offset(name_rva);name=pe[p:pe.index(b'\0',p)].decode()
        ordinal=v('H',file_offset(ordinals)+2*i)[0];func=v('I',file_offset(functions)+4*ordinal)[0];exports.append((func,name))
    relative=address-fault['base'];near=sorted((r,name) for r,name in exports if r<=relative)[-8:]
    ranges=[]
    if 9 in streams:
        _,rva=streams[9];n,offset=u('QQ',rva)
        for i in range(n):
            base,length=u('QQ',rva+16+16*i);ranges.append((base,length,offset));offset+=length
    if 5 in streams:
        _,rva=streams[5];n=u('I',rva)[0]
        for i in range(n):
            base,length,offset=u('QII',rva+4+16*i);ranges.append((base,length,offset))
    def memory(address,size):
        for base,length,offset in ranges:
            if base<=address and address+size<=base+length:return data[offset+address-base:offset+address-base+size]
        return None
    start=max(relative-24,0);code_bytes=memory(fault['base']+start,64);disk_bytes=pe[file_offset(start):file_offset(start)+64]
    # Filter potential return addresses to loaded executable image ranges;
    # no unfiltered stack words or local values are exported.
    stack=memory(registers['RSP'],512);returns=[]
    if stack:
        for offset in range(0,len(stack),8):
            ptr=struct.unpack_from('<Q',stack,offset)[0]
            m=next((m for m in modules if m['base']<=ptr<m['base']+m['image_size']),None)
            if m:returns.append(dict(stack_offset=offset,module=m['path'],RVA=hex(ptr-m['base'])))
    return dict(scope='Offline existing OS crash artifact, no new native start, compute or GPU query',
                dump=dict(path=str(dump),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),retention='Original OS file retained locally; full process memory not published because it may contain environment/private data'),
                exception=dict(code=hex(code),flags=flags,thread_id=thread,module=fault['path'],RVA=hex(relative),address=hex(address)),
                registers={n:hex(x) for n,x in registers.items()},nearest_preceding_export_symbols=[dict(RVA=hex(r),name=n) for r,n in near],
                instruction_context=dict(start_RVA=hex(start),disk_hex=disk_bytes.hex(),dump_hex=code_bytes.hex() if code_bytes else None,dump_disk_bytes_equal=code_bytes==disk_bytes if code_bytes else None),
                filtered_stack_image_addresses=returns,loaded_module_metadata=modules,
                fault_module_disk_sha256=hashlib.sha256(pe).hexdigest(),complete_runtime_identity='No successful native RECORD.json; module metadata/code context do not prove every loaded module byte or continuous residency')

def main():
    p=argparse.ArgumentParser();p.add_argument('--dump',required=True);p.add_argument('--dll',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    report=inspect(a.dump,a.dll)
    with Path(a.output).open('x',encoding='utf-8',newline='\n') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps({k:report[k] for k in ('exception','nearest_preceding_export_symbols','instruction_context','filtered_stack_image_addresses')}))
if __name__=='__main__':main()
