import copy,hashlib,json,sys,unittest
from pathlib import Path
from dep_witness_v2 import parse_dependency,resolved_cpu,DependencyRefusal
from input_freeze import ReadFreeze,FreezeRefusal,snapshot,sha,verify_manifest_identity

HERE=Path(__file__).resolve().parent
class FreezeContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=HERE/('freeze-fixtures-v1-O' if sys.flags.optimize else 'freeze-fixtures-v1-normal');cls.root.mkdir(exist_ok=False)
    def folder(self,name):p=self.root/name;p.mkdir();return p
    def test_resolved_cc1_quoted_and_unquoted_target_vectors(self):
        a='"C:/path with space/zig.exe" "-cc1" "-target-cpu" "arrowlake-s" "-target-feature" "+avx2" "-target-feature" "-avx512f"'
        b='zig.exe -cc1 -target-cpu arrowlake-s -target-feature +avx2 -target-feature -avx512f'
        self.assertEqual(resolved_cpu(a),resolved_cpu(b));self.assertEqual(resolved_cpu(a),[('cpu','arrowlake-s'),('feature','+avx2'),('feature','-avx512f')])
    def test_empty_or_malformed_CPU_proof_refuses(self):
        for text in ['zig.exe -cc1','zig.exe -cc1 -target-cpu arrowlake-s','zig.exe -cc1 -target-cpu x -target-cpu y -target-feature +avx2','no cc1 record']:
            with self.assertRaises(DependencyRefusal):resolved_cpu(text)
    def test_make_rule_escaped_space_and_drive_colon(self):
        root=self.folder('space rule');src=root/'entry.cpp';header=root/'header file.hpp';target=root/'worker.obj';src.write_text('x');header.write_text('y');dep=root/'worker.d'
        esc=lambda p:str(p).replace('\\','/').replace(' ','\\ ')
        dep.write_text(esc(target)+': \\\n '+esc(src)+' \\\n '+esc(header)+'\n',encoding='utf8')
        self.assertEqual(parse_dependency(dep,target,src),sorted([str(src.resolve()),str(header.resolve())]))
    def test_empty_wrong_target_source_variables_and_extra_rules_refuse(self):
        root=self.folder('bad rules');src=root/'entry.cpp';h=root/'h.hpp';t=root/'out.obj';d=root/'x.d';prefix=lambda p:p.as_posix()
        bad=['',prefix(t)+': '+prefix(src)+'\n',prefix(t)+': '+prefix(src)+' $(injected)\n',prefix(t)+': '+prefix(src)+' '+prefix(h),prefix(t)+': '+prefix(src)+' '+prefix(h)+'\nother: file\n',prefix(root/'other.obj')+': '+prefix(src)+' '+prefix(h)+'\n',prefix(t)+': '+prefix(root/'wrong.cpp')+' '+prefix(h)+'\n']
        for text in bad:
            d.write_text(text,encoding='utf8')
            with self.assertRaises(DependencyRefusal):parse_dependency(d,t,src)
    def test_own_OS_readlock_refuses_write_and_delete_but_allows_read(self):
        root=self.folder('os lock');file=root/'owned.hpp';file.write_bytes(b'owned immutable fixture\n');entry=snapshot([file]);events=[]
        with ReadFreeze(entry):
            self.assertEqual(file.read_bytes(),b'owned immutable fixture\n')
            for op in ('write','delete'):
                try:
                    if op=='write':file.write_bytes(b'forbidden')
                    else:file.unlink()
                except OSError as exc:events.append({'operation':op,'refused':True,'winerror':getattr(exc,'winerror',None)})
                else:events.append({'operation':op,'refused':False})
        (root/'LOCK_RECEIPT.json').write_text(json.dumps(events,indent=2),encoding='utf8');self.assertTrue(all(x['refused'] for x in events));self.assertEqual(file.read_bytes(),b'owned immutable fixture\n')
    def test_changed_header_compiler_tool_and_manifest_identity_refuse(self):
        records=[]
        for role in ('header.hpp','compiler.exe','codegen-tool.dat'):
            root=self.folder(role.replace('.','_'));p=root/role;p.write_bytes(b'golden');manifest=root/'prepared.json';manifest.write_text(json.dumps({'entries':snapshot([p])}),encoding='utf8');expected=sha(manifest)
            p.write_bytes(b'changed')
            with self.assertRaises(FreezeRefusal):verify_manifest_identity(manifest,expected)
            records.append({'role':role,'mutated_own_fixture_only':True,'refused':True})
        root=self.folder('identity path');p=root/'compiler.exe';p.write_bytes(b'golden');other=root/'other.exe';other.write_bytes(b'golden');manifest=root/'prepared.json';initial={'entries':snapshot([p])};manifest.write_text(json.dumps(initial),encoding='utf8');expected=sha(manifest);changed=copy.deepcopy(initial);changed['entries'][0]['path']=str(other);manifest.write_text(json.dumps(changed),encoding='utf8')
        with self.assertRaisesRegex(FreezeRefusal,'manifest identity'):verify_manifest_identity(manifest,expected)
        (self.root/'TAMPER_RECEIPT.json').write_text(json.dumps(records+[{'role':'compiler path identity','refused':True}],indent=2),encoding='utf8')

if __name__=='__main__':unittest.main()
