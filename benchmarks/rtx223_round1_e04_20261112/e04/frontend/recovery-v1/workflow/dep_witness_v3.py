"""Strict Clang dependency and resolved cc1 target witnesses."""
from pathlib import Path
import ctypes as C
import re

class DependencyRefusal(ValueError):pass
def need(ok,message):
    if not ok:raise DependencyRefusal(message)
def make_words(text):
    out=[];word=[];i=0
    while i<len(text):
        ch=text[i]
        if ch=='#':raise DependencyRefusal('comments are not dependency paths')
        if ch=='$':
            need(text[i:i+2]=='$$','make variables not admitted');word.append('$');i+=2;continue
        if ch=='\\' and i+1<len(text) and text[i+1] in ' \t#:$\\':word.append(text[i+1]);i+=2;continue
        if ch.isspace():
            if word:out.append(''.join(word));word=[]
        else:word.append(ch)
        i+=1
    if word:out.append(''.join(word))
    return out
def parse_dependency(path,expected_target,expected_source):
    text=Path(path).read_text(encoding='utf8')
    need(bool(text) and '\x00' not in text and text.endswith('\n'),'empty/binary/unterminated dependency recipe')
    need(re.search(r'\\[ \t]*(?:\r?\n)?\Z',text) is None,'truncated continuation')
    logical=re.sub(r'\\\r?\n',' ',text).strip();need('\n' not in logical and '\r' not in logical,'multiple dependency rules')
    separator=None;start=0;i=0
    while i<len(logical):
        ch=logical[i]
        if ch.isspace():start=i+1
        if ch=='\\' and i+1<len(logical) and logical[i+1] in ' \t#:$\\':i+=2;continue
        if ch==':':
            drive=i==start+1 and logical[start:i].isalpha() and i+1<len(logical) and logical[i+1] in '/\\'
            if not drive:separator=i;break
        i+=1
    need(separator is not None,'dependency target delimiter missing')
    targets=make_words(logical[:separator]);paths=make_words(logical[separator+1:])
    normalized=lambda p:str(Path(p).resolve()).casefold()
    need(len(targets)==1 and normalized(targets[0])==normalized(expected_target),'wrong dependency target')
    need(len(paths)>=2,'nonempty source and header closure required')
    need(sum(normalized(p)==normalized(expected_source) for p in paths)==1,'exact source must occur once')
    need(all(Path(p).is_absolute() and not any(c in p for c in '|;*?') for p in paths),'relative or ambiguous dependency')
    need(len({normalized(p) for p in paths})==len(paths),'duplicate dependency path')
    return sorted(str(Path(p).resolve()) for p in paths)
def command_line_words(line):
    shell=C.WinDLL('shell32',use_last_error=True);kernel=C.WinDLL('kernel32',use_last_error=True)
    shell.CommandLineToArgvW.argtypes=[C.c_wchar_p,C.POINTER(C.c_int)];shell.CommandLineToArgvW.restype=C.POINTER(C.c_wchar_p)
    kernel.LocalFree.argtypes=[C.c_void_p];kernel.LocalFree.restype=C.c_void_p
    count=C.c_int();words=shell.CommandLineToArgvW(line.strip(),C.byref(count));need(bool(words),'cannot parse cc1 argument line')
    try:return [words[i] for i in range(count.value)]
    finally:kernel.LocalFree(C.cast(words,C.c_void_p))
def resolved_cpu(text):
    lines=[command_line_words(line) for line in text.splitlines() if '-cc1' in line]
    # Clang -v also prints its version with a '-cc1' token; this exact diagnostic is not an invocation.
    lines=[line for line in lines if '-cc1' in line and not (len(line)>=3 and line[:3]==['clang','-cc1','version'])]
    need(len(lines)==1 and len(lines[0])>2 and lines[0][1]=='-cc1','one actual cc1 invocation required')
    words=lines[0];values=[]
    for i,word in enumerate(words):
        if word in ('-target-cpu','-target-feature'):
            need(i+1<len(words),'missing target option value');values.append((word[8:],words[i+1]))
    cpus=[v for k,v in values if k=='cpu'];features=[v for k,v in values if k=='feature']
    need(len(cpus)==1 and bool(re.fullmatch(r'[A-Za-z0-9_.-]+',cpus[0])),'exactly one nonempty target CPU required')
    need(bool(features) and all(re.fullmatch(r'[+-][A-Za-z0-9_.-]+',v) for v in features),'nonempty native target feature vector required')
    return [[k,v] for k,v in values]
