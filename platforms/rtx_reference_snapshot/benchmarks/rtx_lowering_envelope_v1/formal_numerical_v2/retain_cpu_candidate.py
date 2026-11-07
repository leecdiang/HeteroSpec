"""Preserve earlier actual CPU builds/results before final output-cap build."""
import re,shutil
from common import V,save
def apply_diff(base,patch):
    old=base.splitlines(True);lines=patch.splitlines(True);out=[];at=0;i=0
    while i<len(lines):
        m=re.match(r'@@ -(\d+)(?:,\d+)? \+\d+(?:,\d+)? @@',lines[i])
        if not m:i+=1;continue
        target=int(m.group(1))-1;out.extend(old[at:target]);at=target;i+=1
        while i<len(lines) and not lines[i].startswith('@@'):
            line=lines[i]
            if line.startswith((' ','-')):
                assert old[at]==line[1:];at+=1
            if line.startswith((' ','+')):out.append(line[1:])
            i+=1
    out.extend(old[at:]);return ''.join(out)
def main():
    base=(V.parent/'repair_timer_v1/native_repair.cpp').read_text(encoding='utf-8')
    t=V/'candidate_address_cpu';t.mkdir(exist_ok=False)
    names=['COMPILE.json','LINK_IDENTITY.json','lowering113_formal.exe','lowering113_formal.pdb','CPU_WIRES.json','CPU_ADDRESSES.json','CPU_DESCRIPTOR_NEGATIVES.json','CPU_NATIVE_TESTS.json','CPU_FIXTURE','cpu_tests','SOURCE.diff','native_cpu.stdout','native_cpu.stderr']
    assert t.resolve().is_relative_to(V.resolve())
    for name in names:shutil.move(str(V/name),str(t/name))
    with (t/'native_formal.cpp').open('x',encoding='utf-8',newline='\n') as f:f.write(apply_diff(base,(t/'SOURCE.diff').read_text(encoding='utf-8')))
    shutil.copyfile(V/'formal_gate.h',t/'formal_gate.h')
    first=V/'candidate_initial'
    with (first/'native_formal.cpp').open('x',encoding='utf-8',newline='\n') as f:f.write(apply_diff(base,(first/'SOURCE.diff').read_text(encoding='utf-8')))
    h=(V/'formal_gate.h').read_text(encoding='utf-8');h=h[:h.index('static int all_addresses')]+'}\n'
    with (first/'formal_gate.h').open('x',encoding='utf-8',newline='\n') as f:f.write(h)
    save(V/'CONTROL_TEXT_FAILURES.json',dict(failures=[dict(operation='inline diagnostic reference byte count',error='PowerShell quoting produced Python SyntaxError before execution'),
        dict(operation='inline CPU candidate preservation command',error='PowerShell quoting produced Python SyntaxError before execution; no move or child execution occurred')],
        preservation='Switched to saved source script. Both earlier CPU candidates, exact source reconstructed from their saved SOURCE.diff, binaries, PDBs, fixtures and all results retained.',GPU_native_or_device_starts_from_failed_commands=0))
    print('Preserved both valid earlier CPU candidates and source; no experiment data overwritten')
if __name__=='__main__':main()
