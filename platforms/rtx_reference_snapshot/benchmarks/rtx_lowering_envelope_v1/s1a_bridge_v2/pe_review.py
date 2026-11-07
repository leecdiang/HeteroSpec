"""Read PE files without loading them. No OS loader, backend or device query."""
import struct
from pathlib import Path

class PE:
    def __init__(self,path):
        self.path=Path(path);self.data=self.path.read_bytes();self.u=lambda fmt,o:struct.unpack_from('<'+fmt,self.data,o)
        assert self.data[:2]==b'MZ';self.nt=self.u('I',0x3c)[0];assert self.data[self.nt:self.nt+4]==b'PE\0\0'
        self.machine=self.u('H',self.nt+4)[0];count=self.u('H',self.nt+6)[0];self.optional=self.nt+24
        assert self.u('H',self.optional)[0]==0x20b
        size=self.u('H',self.nt+20)[0];self.sections=[]
        for i in range(count):
            at=self.optional+size+40*i;vs,va,rs,rp=self.u('IIII',at+8);self.sections.append((va,max(vs,rs),rp))
    def offset(self,rva):
        for va,size,raw in self.sections:
            if va<=rva<va+size:return raw+rva-va
        raise ValueError(('bad RVA',hex(rva),str(self.path)))
    def string(self,rva):
        at=self.offset(rva);return self.data[at:self.data.index(b'\0',at)].decode('ascii')
    def exports(self):
        rva,size=self.u('II',self.optional+112)
        if not rva:return {}
        at=self.offset(rva);base,nfunc,nname,functions,names,ordinals=self.u('IIIIII',at+16);out={}
        for i in range(nname):
            name=self.string(self.u('I',self.offset(names)+4*i)[0]);ordinal=self.u('H',self.offset(ordinals)+2*i)[0]
            function=self.u('I',self.offset(functions)+4*ordinal)[0]
            out[name]=dict(RVA=function,forwarder=self.string(function) if rva<=function<rva+size else None)
        return out
    def imports(self):
        rva,size=self.u('II',self.optional+120);out={}
        if not rva:return out
        at=self.offset(rva)
        while True:
            original,stamp,chain,name,first=self.u('IIIII',at)
            if not any((original,stamp,chain,name,first)):break
            dll=self.string(name);thunk=self.offset(original or first);symbols=[]
            for i in range(10000):
                value=self.u('Q',thunk+8*i)[0]
                if not value:break
                symbols.append('#'+str(value&0xffff) if value>>63 else self.string(value+2))
            out[dll]=symbols;at+=20
        return out
    def delay_import_directory(self):return self.u('II',self.optional+112+8*13)
    def delay_imports(self):
        rva,size=self.delay_import_directory();out=[]
        if not rva:return out
        at=self.offset(rva)
        while True:
            values=self.u('IIIIIIII',at)
            if not any(values):break
            attributes,name,*_=values
            if not attributes&1:name-=self.u('Q',self.optional+24)[0]
            out.append(self.string(name));at+=32
        return out
