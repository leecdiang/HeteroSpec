"""Versioned POSIX/host adapter for the authenticated PR195 frontend.

Preserves stage-01. No numerical core or projection arithmetic is edited.
"""
from pathlib import Path
import argparse, difflib, json, shutil
from common import inventory, need, read, save, sha

def once(s, old, new):
    need(s.count(old)==1, 'Unexpected source anchor: '+old[:100])
    return s.replace(old,new,1)

def adapt(source, destination):
    source=Path(source).resolve(); destination=Path(destination).resolve()
    need(not destination.exists(), 'Keep each adaptation epoch separate')
    shutil.copytree(source,destination)
    front=destination/'frontend'; p=front/'worker.cpp'; old=p.read_text(); s=old
    # The final entry includes request/context code from this file, but not the
    # historical Windows executable's standalone identity-binding command line.
    s=once(s,'int main(int argc,char**argv){','#ifdef _WIN32\nint main(int argc,char**argv){')+'\n#endif\n'
    s=once(s,'#include <bcrypt.h>','extern "C" {\n#include "hash/sha256/sha256.h"\n}\n#include <ctime>\n#include <cerrno>\n#include <unistd.h>\n#include <fcntl.h>')
    start=s.index('struct Sha256 {'); end=s.index('\nstatic std::string hash_text',start)
    s=s[:start]+'''struct Sha256 {
    sha256_t state;
    Sha256(){sha256_init(&state);}
    void update(const char* data,size_t size){sha256_update(&state,reinterpret_cast<const unsigned char*>(data),size);}
    std::string finish(){unsigned char bytes[32];sha256_final(&state,bytes);const char* hex="0123456789abcdef";std::string out;for(auto b:bytes){out+=hex[b>>4];out+=hex[b&15];}return out;}
};'''+s[end:]
    start=s.index('static std::string utc_now(){'); end=s.index('\nstruct Sha256',start)
    s=s[:start]+'''static std::string utc_now(){
    const auto now=std::chrono::system_clock::now();
    const auto stamp=std::chrono::system_clock::to_time_t(now);
    std::tm t{};need(gmtime_r(&stamp,&t)!=nullptr,"UTC conversion");
    char value[48];const auto ms=std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()).count()%1000;
    snprintf(value,sizeof(value),"%04d-%02d-%02dT%02d:%02d:%02d.%03lldZ",t.tm_year+1900,t.tm_mon+1,t.tm_mday,t.tm_hour,t.tm_min,t.tm_sec,static_cast<long long>(ms));return value;
}'''+s[end:]
    start=s.index('static void dump('); end=s.index('\nstatic json load',start)
    s=s[:start]+'''static void dump(const fs::path&p,const json&j){
    auto tmp=p;tmp+=".tmp";
    {std::ofstream f(tmp);f<<j.dump(2)<<'\\n';f.flush();need(bool(f),"write JSON");}
    int fd=::open(tmp.c_str(),O_RDONLY);need(fd>=0,"open JSON for sync");
    const int synced=::fsync(fd);const int closed=::close(fd);need(synced==0&&closed==0,"sync JSON");
    need(::rename(tmp.c_str(),p.c_str())==0,"atomic JSON replace");
    fd=::open(p.parent_path().c_str(),O_RDONLY|O_DIRECTORY);need(fd>=0,"open output directory");
    const int synced_dir=::fsync(fd);const int closed_dir=::close(fd);need(synced_dir==0&&closed_dir==0,"sync output directory");
}'''+s[end:]
    s=once(s,'inline bool phase_observe=false;','inline bool phase_observe=false;\ninline int phase_threads=2;')
    s=once(s,'p.n_threads=24;p.n_threads_batch=24;','p.n_threads=phase_threads;p.n_threads_batch=phase_threads;')
    s=once(s,'if(!d||std::string(ggml_backend_dev_description(d)).find("5070") == std::string::npos)o.bad=true;',
           'if(!d||ggml_backend_dev_type(d)!=GGML_BACKEND_DEVICE_TYPE_GPU)o.bad=true;')
    s=once(s,'if (!capture || !target || (key!="initial" && key!="commit-0")) return;',
           'if (!capture || !target) return;')
    p.write_text(s)
    p=front/'entry.cpp'; old_entry=p.read_text(); entry=once(old_entry,
        'const auto bin=linux_transfer::executable().parent_path();',
        'phase_threads=job.at("threads").get<int>();need(phase_threads>0 && phase_threads<=2,"allocated CPU thread budget");\n        const auto bin=linux_transfer::executable().parent_path();')
    p.write_text(entry)
    changes=''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='stage-01/frontend/worker.cpp',tofile='stage-02/frontend/worker.cpp'))
    changes+=''.join(difflib.unified_diff(old_entry.splitlines(True),entry.splitlines(True),fromfile='stage-01/frontend/entry.cpp',tofile='stage-02/frontend/entry.cpp'))
    (destination/'POSIX_HOST.patch').write_text(changes)
    lock=read(destination/'SOURCE_LOCK.json')
    (destination/'SOURCE_LOCK.json').rename(destination/'SOURCE_LOCK.input.json')
    (destination/'PORT.json').rename(destination/'PORT.input.json')
    lock.update(frontend=inventory(front),status='SOURCE_PORTED_NOT_BUILT',adaptation={
        'source_lock_before_sha256':sha(source/'SOURCE_LOCK.json'),
        'script_sha256':sha(Path(__file__)), 'patch_sha256':sha(destination/'POSIX_HOST.patch'),
        'categories':['portability','host-placement observation','explicit runtime thread configuration','offline heavy capture of all committed boundaries'],
        'numerical_core_edits':False,'historical_cli':'preserved but Windows-only; final native entry remains active',
        'threads':2,'target_output_reservation':4,'reference_output_reservation':1,
        'reservation_difference_requires_qualification':True})
    save(destination/'SOURCE_LOCK.json',lock)
    save(destination/'PORT.json',{'status':'SOURCE_PORTED_NOT_BUILT','native_profile_supported':False,
         'historical_windows_cli_excluded':True,'numerical_core_edits':False,
         'native_build':'NOT_RUN','GPU_qualification':'NOT_RUN'})
    print(destination)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();adapt(a.source,a.out)
