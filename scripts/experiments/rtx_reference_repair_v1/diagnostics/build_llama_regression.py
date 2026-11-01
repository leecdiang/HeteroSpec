"""Adapt only the family guard and fresh-context capacity probe for pinned Llama."""
import pathlib,sys,subprocess,shutil
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from common import *
import native
repo=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();staged=out.parent/(out.name+'_source_adapter')
old=read('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/repo/work/native-metadata4-v4/BUILD.json');archive=Path('D:/hsc95/SOURCE_RUNTIME_V02.zip')
need(file_hash(archive)==old['source_zip_sha256']=='36be0d738ad5d29579b75825f68337003eb127405cc5418abc566cb07718a4d8','original Llama source archive')
native.stage(repo,staged,0,True);worker=staged/'worker.cpp';original=worker.read_text();changed=native.once(original,'need(family=="Qwen","dense14b uses original Qwen source cohort");','need(family=="Llama","pinned Llama metadata4 regression only");')
anchor='''        if(admission_only){
            result["producer_allocation_probes"]=json::array();'''
replacement='''        if(admission_only){
            Pair fresh_capacity;
            if(!resident_life)provision(fresh_capacity,t,d,arm_spec("C_QB"),root/"fresh_capacity");
            result["producer_allocation_probes"]=json::array();'''
changed=native.once(changed,anchor,replacement)
changed=native.once(changed,'need(resident_life && residents.size()==3,"admission requires three registered dense14b pools");','need((resident_life && residents.size()==3)||(!resident_life && family=="Llama"),"registered residency capacity probe required");')
# The candidate's natural request, producer bridge and speculative loop are exact.
start='static json request(';end='int main('
need(original.count(start)==changed.count(start)==1,'request function anchor')
need(original.split(start)[1].split(end)[0]==changed.split(start)[1].split(end)[0],'regression changed request semantics')
(staged/'WORKER_BEFORE_REGRESSION.cpp').write_text(original,encoding='utf-8',newline='\n');worker.write_text(changed,encoding='utf-8',newline='\n')
save(staged/'REGRESSION_ADAPTATION.json',{'family':'Llama','variant':'metadata4','before_sha256':file_hash(staged/'WORKER_BEFORE_REGRESSION.cpp'),'after_sha256':file_hash(worker),'request_function_byte_identical':True,'changes':'family guard; zero-token fresh C_QB receiver/draft plus transient producer capacity probe; temporary pair destroyed before model cleanup','native_requests':0},exclusive=True)
manifest=staged/'NUMERICAL_DLLS.json';save(manifest,{'numerical_DLL_sha256':old['numerical_modules']},exclusive=True)
cmd=[sys.executable,'-B',str(staged/'build_native.py'),'--variant','metadata4','--archive',str(archive),'--out',str(out),'--dll-manifest',str(manifest),'--dll-dir','C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/repo/work/native-metadata4-v4/bin']
for key in ['zig','cmake','ninja']:cmd+=['--'+key,old['tools'][key]['path']]
cmd+=['--jobs','4','--command-timeout','3600'];save(staged/'BUILD_COMMAND.json',{'argv':cmd},exclusive=True);subprocess.run(cmd,check=True)
print(read(out/'BUILD.json')['status'])
