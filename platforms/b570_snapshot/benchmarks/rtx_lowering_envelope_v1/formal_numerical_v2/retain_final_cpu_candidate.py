"""Retain the CPU-validated candidate before failure-receipt ordering refinement."""
import shutil
from common import V
def main():
    t=V/'candidate_writer_cpu';t.mkdir(exist_ok=False);assert t.resolve().is_relative_to(V.resolve())
    for name in ('native_formal.cpp','formal_gate.h'):shutil.copyfile(V/name,t/name)
    for name in ('COMPILE.json','LINK_IDENTITY.json','lowering113_formal.exe','lowering113_formal.pdb','CPU_WIRES.json','CPU_ADDRESSES.json','CPU_DESCRIPTOR_NEGATIVES.json','CPU_NATIVE_TESTS.json','CPU_FIXTURE','cpu_tests','SOURCE.diff','native_cpu.stdout','native_cpu.stderr'):shutil.move(str(V/name),str(t/name))
    # These expected tables remain identical: numerical Graph construction has
    # not changed. Keep prior fixtures/results, and rebuild final ones later.
    print('Prior complete CPU candidate retained; no old research output modified')
if __name__=='__main__':main()
