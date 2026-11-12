"""Conservative whole-archive evidence. Exact duplicate member occurrence is unproved."""
from pathlib import Path
import hashlib,re
from link_witness import Archive,WitnessError,_resolve_archive,_member_reference,_map_reference,norm_name,basename
def need(v,m):
    if not v:raise WitnessError(m)
def analyze(trace,archives,objects,map_text):
    loaded=[Archive(Path(p).resolve(strict=True)) for p in archives]
    need(len({str(a.path).casefold() for a in loaded})==len(loaded),'duplicate archive container')
    direct={str(Path(p).resolve()).casefold():Path(p).resolve() for p in objects}
    read_archives=set();read_objects=set();member_lines=[];map_lines=[]
    def member_exists(a,name):
        need(any(norm_name(m['name'])==norm_name(name) or basename(m['name'])==basename(name) for m in a.members),'traced member not in frozen container')
    for n,line in enumerate(trace.splitlines(),1):
        read=re.match(r'^\s*(?:lld-link:\s*)?Reading\s+(.+?)\s*$',line)
        if read:
            text=read.group(1).strip('"');member=_member_reference(text)
            if member:
                a=_resolve_archive(member.group(1),loaded);member_exists(a,member.group(2));member_lines.append({'line':n,'archive':str(a.path),'member_label':member.group(2),'kind':'Reading'})
            elif re.search(r'\.(a|lib)$',text,re.I):read_archives.add(str(_resolve_archive(text,loaded).path))
            else:
                key=str(Path(text).resolve()).casefold();need(key in direct,'unfrozen direct linker input: '+text);read_objects.add(key)
        extracted=re.match(r'^\s*(?:lld-link:\s*)?Loaded\s+(.+?)\s+for\s+(?:symbol\s+)?(.+?)\s*$',line)
        if extracted:
            member=_member_reference(extracted.group(1))
            need(member is not None,'unsupported Loaded line: '+line)
            a=_resolve_archive(member.group(1),loaded);member_exists(a,member.group(2));member_lines.append({'line':n,'archive':str(a.path),'member_label':member.group(2),'kind':'Loaded','symbol_label':extracted.group(2)})
    for n,line in enumerate(map_text.splitlines(),1):
        symbol=re.match(r'^\s*[0-9A-Fa-f]{4}:[0-9A-Fa-f]+\s+(\S+)\s+[0-9A-Fa-f]+\s+(.+?)\s*$',line)
        if symbol:
            found=_map_reference(symbol.group(2),loaded)
            if found:
                a,name=found;member_exists(a,name);map_lines.append({'line':n,'archive':str(a.path),'member_label':name,'symbol_label':symbol.group(1)})
    need(read_archives=={str(a.path) for a in loaded},'actual Reading trace does not match complete explicit archive-container set')
    need(read_objects==set(direct),'actual Reading trace does not match direct object set')
    need(member_lines and map_lines,'empty member trace or map is unsupported')
    return {'schema':'heterospec.e04.lld-whole-archive-closure.v1','status':'PASS_WHOLE_ARCHIVE_INPUT_CLOSURE','archive_containers':[{'path':str(a.path),'bytes':len(a.data),'sha256':a.sha256} for a in loaded],'direct_objects':[{'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in direct.values()],'member_labels':member_lines,'map_labels':map_lines,'exact_selected_member_occurrence':'NOT_ATTESTED','duplicate_differing_members':'all candidate bytes bound by frozen complete archive containers','limits':'actual selected archive paths and member labels are covered; exact duplicate-name assignment, arbitrary linker filesystem reads and mutable OS DLLs are not attested'}
