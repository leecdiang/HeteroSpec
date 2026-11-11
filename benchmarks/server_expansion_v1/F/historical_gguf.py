"""Read complete GGUF metadata without weights or model forwards."""
import struct
from pathlib import Path
class Reader:
    def __init__(self,p):self.f=Path(p).open('rb')
    def number(self,fmt):return struct.unpack('<'+fmt,self.f.read(struct.calcsize('<'+fmt)))[0]
    def string(self):return self.f.read(self.number('Q')).decode('utf-8')
    def value(self,t):
        if t==8:return self.string()
        if t==9:
            subtype=self.number('I');n=self.number('Q');return [self.value(subtype) for _ in range(n)]
        formats={0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'?',10:'Q',11:'q',12:'d'}
        return self.number(formats[t])
    def metadata(self):
        assert self.f.read(4)==b'GGUF';version=self.number('I');assert version==3
        n_tensor=self.number('Q');n_metadata=self.number('Q');meta={}
        for _ in range(n_metadata):key=self.string();meta[key]=self.value(self.number('I'))
        tensors=[]
        for _ in range(n_tensor):
            name=self.string();dims=[self.number('Q') for _ in range(self.number('I'))];kind=self.number('I');offset=self.number('Q');tensors.append({'name':name,'shape':dims,'type':kind,'offset':offset})
        self.f.close();return meta,tensors

