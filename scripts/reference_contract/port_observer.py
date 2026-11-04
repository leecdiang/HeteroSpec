"""Portable module enumeration only; does not change numerical operators."""
from pathlib import Path

def port(text):
    old='#include <windows.h>\n#include <psapi.h>'
    new='#ifdef _WIN32\n#include <windows.h>\n#include <psapi.h>\n#else\n#include <link.h>\n#endif'
    if text.count(old)!=1: raise ValueError('observer include anchor mismatch')
    text=text.replace(old,new)
    start=text.index('inline j modules(){')
    end=text.index('\ninline int decode',start)
    original=text[start:end]
    return text[:start]+'#ifdef _WIN32\n'+original+'''\n#else
inline j modules(){
    j result=j::array();
    dl_iterate_phdr([](struct dl_phdr_info * info, size_t, void * data) {
        static_cast<j*>(data)->push_back(info->dlpi_name);
        return 0;
    }, &result);
    return result;
}
#endif
'''+text[end:]

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
    a.source.write_text(port(a.source.read_text()))
