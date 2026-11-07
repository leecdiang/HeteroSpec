"""Diagnostic exception location; original numeric runtime stays unchanged."""
from operator_host import *
def build():
    original=OP/'graph_tiles-driver-v3';out=OP/'graph-abi-debug-v2';out.mkdir();(out/'bin').mkdir()
    (out/'driver-wrapped.inc').write_text((original/'driver.cpp').read_text().replace('int main(int argc,char**argv){','int original_driver_main(int argc,char**argv){'),encoding='utf8')
    for name in ('operator_replay.inc','profiler.inc'):shutil.copy2(original/name,out/name)
    source='''#define NOMINMAX
#include "driver-wrapped.inc"
static void where184(void* p){HMODULE h=nullptr;char file[32768]={0};GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,(LPCSTR)p,&h);if(h)GetModuleFileNameA(h,file,sizeof(file));std::cerr<<file<<" +0x"<<std::hex<<(uintptr_t(p)-uintptr_t(h))<<" address 0x"<<uintptr_t(p)<<"\\n";}
static LONG CALLBACK exception184(EXCEPTION_POINTERS*p){
if(p->ExceptionRecord->ExceptionCode==0xc0000094 || p->ExceptionRecord->ExceptionCode==0xc0000005){
auto*c=p->ContextRecord;std::cerr<<"NATIVE_EXCEPTION 0x"<<std::hex<<p->ExceptionRecord->ExceptionCode<<"\\n";where184(p->ExceptionRecord->ExceptionAddress);
std::cerr<<"rax="<<c->Rax<<" rbx="<<c->Rbx<<" rcx="<<c->Rcx<<" rdx="<<c->Rdx<<" rsi="<<c->Rsi<<" rdi="<<c->Rdi<<" r8="<<c->R8<<" r9="<<c->R9<<" r10="<<c->R10<<" r11="<<c->R11<<" r12="<<c->R12<<" r13="<<c->R13<<" r14="<<c->R14<<" r15="<<c->R15<<"\\n";
void*frames[32];USHORT n=CaptureStackBackTrace(0,32,frames,nullptr);for(USHORT i=0;i<n;i++)where184(frames[i]);std::cerr.flush();}
return EXCEPTION_CONTINUE_SEARCH;}
int main(int argc,char**argv){AddVectoredExceptionHandler(1,exception184);return original_driver_main(argc,argv);}
'''
    (out/'debug.cpp').write_text(source,encoding='utf8');records=[]
    for phase in ('worker','link'):
        cmd=json.loads((original/(phase+'.json')).read_bytes())['argv'];cmd=[x.replace(str(original/'driver.cpp'),str(out/'debug.cpp')).replace(str(original/'driver.obj'),str(out/'debug.obj')).replace(str(original/'bin/driver.exe'),str(out/'bin/driver.exe')) for x in cmd]
        with (out/(phase+'.log')).open('xb') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=600)
        put(out/(phase+'.json'),dict(argv=cmd,code=r.returncode));r.check_returncode()
    b=json.loads((original/'RUNTIME_BINDING.json').read_bytes())
    for name,h in b['modules'].items():os.link(original/'bin'/name,out/'bin'/name)
    b['exe']=sha(out/'bin/driver.exe');put(out/'RUNTIME_BINDING.json',b)
if __name__=='__main__':build()
