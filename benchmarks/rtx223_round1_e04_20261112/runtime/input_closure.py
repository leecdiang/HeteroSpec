"""Strict dependency parsing and owned-input read locks; no CUDA APIs."""
from pathlib import Path
import ctypes,json,re

def make_words(text):
    words=[];word=[];i=0
    while i<len(text):
        c=text[i]
        if c=='#':raise ValueError('comments are not accepted in dependency paths')
        if c=='$':
            if text[i:i+2]!='$$':raise ValueError('make variables are not accepted')
            word.append('$');i+=2;continue
        if c=='\\' and i+1<len(text) and text[i+1] in ' \t#:$\\':word.append(text[i+1]);i+=2;continue
        if c.isspace():
            if word:words.append(''.join(word));word=[]
        else:word.append(c)
        i+=1
    if word:words.append(''.join(word))
    return words

def parse_nvcc_dep(text,expected_target,expected_source):
    if not text or '\x00' in text or not text.endswith('\n'):raise ValueError('empty, binary or unterminated dependency recipe')
    if re.search(r'\\[ \t]*(?:\r?\n)?\Z',text):raise ValueError('truncated continuation')
    logical=re.sub(r'\\\r?\n',' ',text).strip()
    if '\n' in logical or '\r' in logical:raise ValueError('multiple dependency rules are not admitted')
    separator=None;i=0;tokenstart=0
    while i<len(logical):
        c=logical[i]
        if c.isspace():tokenstart=i+1
        if c=='\\' and i+1<len(logical) and logical[i+1] in ' \t#:$\\':i+=2;continue
        if c==':':
            drive=i==tokenstart+1 and logical[tokenstart:i].isalpha() and i+1<len(logical) and logical[i+1] in '/\\'
            if not drive:separator=i;break
        i+=1
    if separator is None:raise ValueError('dependency rule lacks target delimiter')
    targets=make_words(logical[:separator]);dependencies=make_words(logical[separator+1:])
    norm=lambda p:str(Path(p).resolve()).casefold()
    if len(targets)!=1 or norm(targets[0])!=norm(expected_target):raise ValueError('unexpected dependency target')
    if len(dependencies)<2:raise ValueError('CUDA dependency rule lacks header inputs')
    if sum(norm(p)==norm(expected_source) for p in dependencies)!=1:raise ValueError('exact source must occur once')
    if any(not Path(p).is_absolute() or any(x in p for x in ('|',';','*','?')) for p in dependencies):raise ValueError('ambiguous or relative dependency path')
    return dependencies

class ReadFreeze:
    def __init__(self):
        self.kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        self.create=self.kernel.CreateFileW;self.create.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p];self.create.restype=ctypes.c_void_p
        self.close=self.kernel.CloseHandle;self.close.argtypes=[ctypes.c_void_p];self.close.restype=ctypes.c_int
        self.handles=[]
    def add(self,path):
        p=str(Path(path).resolve())
        if not p.startswith('\\\\?\\'):p='\\\\?\\'+p
        handle=self.create(p,0x80000000,1,None,3,0x80,None)
        if handle==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
        self.handles.append(handle)
    def release(self):
        for handle in self.handles:self.close(handle)
        self.handles=[]
