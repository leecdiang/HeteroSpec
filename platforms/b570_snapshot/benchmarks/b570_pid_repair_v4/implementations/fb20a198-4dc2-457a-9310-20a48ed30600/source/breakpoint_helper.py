"""Native negative fixture: a post-loader breakpoint must reach application handling."""
import ctypes,sys
if sys.platform!='win32':raise RuntimeError('Windows-only fixture')
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.SetErrorMode(0x0001|0x0002)
print('APPLICATION_BREAKPOINT_BEGIN',flush=True)
k.DebugBreak()
print('APPLICATION_BREAKPOINT_SWALLOWED',flush=True)
