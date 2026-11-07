"""Small read-only provenance helpers; no backend/model imports."""
import ctypes, hashlib, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()

def load(path):
    return json.loads(pathlib.Path(path).read_text(encoding='utf-8-sig'))

def save(path, data):
    path = pathlib.Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, allow_nan=False); f.write('\n')

def modules():
    if sys.platform != 'win32':
        raise RuntimeError('This receipt requires Windows module enumeration')
    k = ctypes.WinDLL('kernel32', use_last_error=True)
    k.GetCurrentProcess.restype = ctypes.c_void_p
    k.K32EnumProcessModules.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p]
    k.K32GetModuleFileNameExW.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_ulong]
    handles = (ctypes.c_void_p * 2048)(); needed = ctypes.c_ulong()
    proc = k.GetCurrentProcess()
    if not k.K32EnumProcessModules(proc, handles, ctypes.sizeof(handles), ctypes.byref(needed)):
        raise ctypes.WinError(ctypes.get_last_error())
    assert needed.value <= ctypes.sizeof(handles)
    result = []
    for h in handles[:needed.value // ctypes.sizeof(ctypes.c_void_p)]:
        buf = ctypes.create_unicode_buffer(32768)
        if not k.K32GetModuleFileNameExW(proc, h, buf, len(buf)): raise ctypes.WinError()
        result.append(dict(path=buf.value, sha256=sha(buf.value)))
    forbidden = ('vulkan', 'cuda', 'cublas', 'cudnn', 'ggml-', 'llama', 'igvk', 'nvoglv')
    assert not any(any(s in pathlib.Path(x['path']).name.lower() for s in forbidden) for x in result)
    return result
