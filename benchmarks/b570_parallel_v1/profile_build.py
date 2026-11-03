"""Bind a timestamp-label-only diagnostic Vulkan library. Timed workers use their frozen DLLs."""
from host import *
def build():
    dest=ROOT/'candidate-profile';dest.mkdir()
    cpp=ROOT/'source-00/ggml/src/ggml-vulkan/ggml-vulkan.cpp'
    original=cpp.read_bytes();s=original.decode()
    key='        *n_flops = ggml_vk_get_node_flops(node);'
    s=once(s,key,key+'''
        if ((node->op==GGML_OP_CONT || node->op==GGML_OP_CONCAT) && node->src[0]) {
            return std::string(ggml_op_name(node->op))+" ["+node->name+"] from ["+node->src[0]->name+"]";
        }''')
    (dest/'ggml-vulkan.cpp').write_text(s,encoding='utf-8',newline='\n')
    out=ROOT/'build-00/bin/Release/ggml-vulkan.dll'
    baseline=ROOT/'candidate-D/build/Release'
    assert sha(out)==sha(baseline/out.name)
    try:
        shutil.copyfile(dest/'ggml-vulkan.cpp',cpp)
        os.environ['VULKAN_SDK']='C:/VulkanSDK/1.4.357.0';os.environ['PATH']=os.environ['VULKAN_SDK']+'/Bin;'+os.environ['PATH']
        command(['cmake','--build',ROOT/'build-00','--config','Release','--target','ggml-vulkan','--parallel','4'],dest/'compile.log')
        bin=dest/'bin';bin.mkdir()
        shutil.copyfile(baseline/'frontier.exe',bin/'frontier.exe')
        for f in baseline.glob('*.dll'):shutil.copyfile(out if f.name==out.name else f,bin/f.name)
        bind('candidate-profile',bin)
    finally:
        cpp.write_bytes(original);shutil.copyfile(baseline/out.name,out)
    write(dest/'DIAGNOSTIC.json',dict(source_sha256=sha(dest/'ggml-vulkan.cpp'),formal_source_restored_sha256=sha(cpp),restored_formal_dll=sha(out),purpose='Only timestamp grouping labels change. Independently verify every trace output against the frozen numerical role.'))
if __name__=='__main__':build()
