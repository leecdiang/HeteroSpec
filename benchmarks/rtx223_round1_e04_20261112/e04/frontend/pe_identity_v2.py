"""Read PE imports/exports from disk without mapping/loading a DLL."""
from pathlib import Path
import argparse,hashlib,json,struct

class PERefusal(ValueError):pass
def inspect(path):
    path=Path(path).resolve();raw=path.read_bytes()
    def need(ok,message):
        if not ok:raise PERefusal(message)
    def unpack(fmt,offset):
        size=struct.calcsize('<'+fmt);need(0<=offset<=len(raw)-size,'PE structure outside file');return struct.unpack_from('<'+fmt,raw,offset)
    need(raw[:2]==b'MZ','MZ missing');pe=unpack('I',0x3c)[0];need(raw[pe:pe+4]==b'PE\0\0','PE signature missing')
    machine,sections,_,_,_,opt_size,characteristics=unpack('HHIIIHH',pe+4);op=pe+24
    need(machine==0x8664 and unpack('H',op)[0]==0x20b,'only AMD64 PE32+ admitted')
    need(0<sections<128 and opt_size>=112+16*8,'unbounded section table')
    headers=unpack('I',op+60)[0];table=[]
    for i in range(sections):
        off=op+opt_size+i*40;name=raw[off:off+8].rstrip(b'\0').decode('ascii',errors='replace');vsize,va,size,fo=unpack('IIII',off+8);table.append({'name':name,'rva':va,'virtual_bytes':vsize,'file_bytes':size,'file_offset':fo})
    def rva(address,size=1):
        if address<headers:need(address+size<=len(raw),'header RVA bounds');return address
        for s in table:
            if s['rva']<=address<s['rva']+max(s['virtual_bytes'],s['file_bytes']):
                delta=address-s['rva'];need(delta+size<=s['file_bytes'],'unbacked virtual RVA');offset=s['file_offset']+delta;need(offset+size<=len(raw),'RVA file bounds');return offset
        raise PERefusal('RVA has no section')
    def string(address):
        offset=rva(address);end=raw.find(b'\0',offset,min(offset+32768,len(raw)));need(end>=offset,'unbounded PE string');return raw[offset:end].decode('ascii')
    def directory(index):return unpack('II',op+112+index*8)
    imports=[];import_symbols={};start,length=directory(1)
    if start:
        need(length>=20,'import directory truncated')
        for i in range(min(length//20+1,4096)):
            fields=unpack('IIIII',rva(start+i*20,20))
            if fields==(0,0,0,0,0):break
            library=string(fields[3]);imports.append(library);symbols=[];thunk=fields[0] or fields[4]
            for j in range(100000):
                value=unpack('Q',rva(thunk+j*8,8))[0]
                if not value:break
                symbols.append({'ordinal':value&0xffff} if value&(1<<63) else string(value+2))
            else:raise PERefusal('unterminated import thunk')
            import_symbols[library]=symbols
        else:raise PERefusal('unterminated import directory')
    exports={};start,length=directory(0)
    if start:
        values=unpack('IIHHIIIIIII',rva(start,40));base,nfunc,nnames,funcs,names,ords=values[5:]
        need(nfunc<=100000 and nnames<=nfunc,'export count bounds')
        for i in range(nnames):
            name=string(unpack('I',rva(names+i*4,4))[0]);ordinal=unpack('H',rva(ords+i*2,2))[0];need(ordinal<nfunc,'export ordinal bounds');address=unpack('I',rva(funcs+ordinal*4,4))[0]
            exports[name]={'ordinal':base+ordinal,'rva':address,'forwarder':string(address) if start<=address<start+length else None}
    tls_rva,tls_bytes=directory(9)
    delay_imports=[];delay_symbols={};start,length=directory(13)
    if start:
        need(length>=32,'delay import directory truncated')
        for i in range(min(length//32+1,4096)):
            fields=unpack('IIIIIIII',rva(start+i*32,32))
            if not any(fields):break
            need(fields[0]==1,'unsupported delay import VA descriptor')
            library=string(fields[1]);delay_imports.append(library);symbols=[];thunk=fields[4] or fields[3]
            for j in range(100000):
                value=unpack('Q',rva(thunk+j*8,8))[0]
                if not value:break
                symbols.append({'ordinal':value&0xffff} if value&(1<<63) else string(value+2))
            else:raise PERefusal('unterminated delay import thunk')
            delay_symbols[library]=symbols
        else:raise PERefusal('unterminated delay import directory')
    return {'schema':'heterospec.offline-pe-identity.v1','path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'machine':'AMD64','is_dll':bool(characteristics&0x2000),'imports':imports,'import_symbols':import_symbols,'delay_imports':delay_imports,'delay_import_symbols':delay_symbols,'exports':exports,'sections':table,'TLS_directory_present':bool(tls_rva),'DLL_loads':0,'CUDA_calls':0,'qualification':'NOT_RUN','scope':'DISK_ONLY; imports/CRT/fatbinary initialization not executed'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('dll');p.add_argument('--out');a=p.parse_args();record=inspect(a.dll);text=json.dumps(record,indent=2)
    if a.out:Path(a.out).write_text(text,encoding='utf8')
    else:print(text)
