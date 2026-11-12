from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'pe_identity_e04.py').read_text()
old="    tls_rva,tls_bytes=directory(9)\n"
new="""    tls_rva,tls_bytes=directory(9)
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
"""
if old not in s:raise RuntimeError('PE TLS anchor missing')
s=s.replace(old,new).replace("'imports':imports,'import_symbols':import_symbols,","'imports':imports,'import_symbols':import_symbols,'delay_imports':delay_imports,'delay_import_symbols':delay_symbols,")
with (p/'pe_identity_v2.py').open('x',encoding='utf8',newline='\n') as f:f.write(s)
