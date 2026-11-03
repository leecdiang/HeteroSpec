"""Stage actual wide Q8 column tiling and capacity-derived K/V broadcast strides."""
from paths import *
import shutil
def stage():
    src=ROOT/'source-00'
    shutil.copytree(PR165/'source-01',src)
    shared=HERE.parents[1]/'src/reference_batching/reference_batching.hpp'
    assert sha(shared)=='7c1e2ee97e0af5b306ec9ba3cf7e2fb55c37749da07891f46cccd88041530809'
    shutil.copyfile(shared,src/'src/hs_reference_batching.hpp')
    def edit(rel,fn):
        p=src/rel;p.write_text(fn(p.read_text(encoding='utf-8')),encoding='utf-8',newline='\n')
    edit('src/query_head.h',lambda s:once(s,'nq<=4','nq<=32'))
    def graph(s):
        s=once(s,'GGML_ASSERT(q->ne[0] == 128 && q->ne[2] == 32 && k->ne[2] == 8);',r'''GGML_ASSERT((q->ne[0]==128 && q->ne[2]==32 && k->ne[2]==8) ||
                    (q->ne[0]==64 && ((q->ne[2]==32 && k->ne[2]==32) || (q->ne[2]==9 && k->ne[2]==3))));''')
        s=once(s,'q->ne[1] <= 4','q->ne[1] <= 32')
        s=once(s,'k->ne[1] <= 1024','k->ne[1] <= 4096')
        return s
    edit('src/llama-graph.cpp',graph)
    edit('src/llama-context.cpp',lambda s:once(s,'cparams.n_ubatch <= 4','cparams.n_ubatch <= 32'))
    vk='ggml/src/ggml-vulkan/'
    def backend(s):
        start=s.index('static bool ggml_vk_qb_gqa_av_broadcast(')
        end=s.index('static void ggml_vk_mul_mat_vec_nc_f16_f32(',start)
        s=s[:start]+r'''
static bool hs_head_geometry(int64_t d, int64_t h, int64_t hk) {
    return (d==128 && h==32 && hk==8) || (d==64 && ((h==32 && hk==32) || (h==9 && hk==3)));
}

// Check the actual byte strides of the capacity-strided F16 V and interleaved K.
// An extent-cropped view retains the full allocated cache's row/head strides.
static bool hs_qb_operand(const ggml_tensor *a,const ggml_tensor *b,bool value) {
    if(a->type!=GGML_TYPE_F16 || b->type!=GGML_TYPE_F32 || a->ne[3]!=1 ||
       b->ne[3]<2 || b->ne[3]>32 || b->ne[1]!=1 || a->nb[0]!=2 || b->nb[0]!=4) return false;
    const int64_t d=a->ne[value?1:0], extent=a->ne[value?0:1], hk=a->ne[2];
    if(!hs_head_geometry(d,b->ne[2],hk) || extent<256 || extent>4096 || extent%256 ||
       b->ne[0]!=a->ne[0]) return false;
    const size_t scalar=2, head=scalar*d, token=head*hk;
    if(a->nb[3]%token) return false;
    const size_t capacity=a->nb[3]/token;
    if(capacity<size_t(extent) || capacity>4096 || capacity%256) return false;
    return value ? (a->nb[1]==capacity*scalar && a->nb[2]==capacity*head && ggml_is_contiguous(b))
                 : (a->nb[1]==token && a->nb[2]==head);
}
static bool ggml_vk_qb_gqa_av_broadcast(const ggml_tensor *a,const ggml_tensor *b) {
    return hs_qb_operand(a,b,true);
}
''' +s[end:]
        start=s.index('                // Experimental Qwen3 32/8 GQA')
        end=s.index('                if (a->ne[3] != b->ne[3]',start)
        s=s[:start]+'''                const bool qb_gqa_broadcast = op->op == GGML_OP_MUL_MAT &&
                    (hs_qb_operand(a,b,false) || hs_qb_operand(a,b,true));
'''+s[end:]
        # Keep one graph-wide dense operation. Multiple column tiles execute
        # across grid Y within one dispatch; each uses the proven scalar reduction.
        start=s.index('static void ggml_vk_mul_mat_vec_q_f16(')
        end=s.index('static void ggml_vk_mul_mat_vec_p021',start)
        body=s[start:end]
        body=once(body,'    // Check for mmq first',r'''    uint32_t tile=std::min<uint64_t>(ne11,mul_mat_vec_max_cols);
    while(ne11%tile) --tile;
    const uint32_t tile_groups=ne11/tile;
    GGML_ASSERT(tile_groups==1 || (selected && src0->type==GGML_TYPE_Q8_0 && !quantize_y && ne12*ne13==1));
    // Check for mmq first''')
        body=body.replace('GGML_TYPE_Q8_1, ne11, ne20','GGML_TYPE_Q8_1, tile, ne20').replace('src1->type, ne11, ne20','src1->type, tile, ne20')
        head,grid=body.split('    ggml_pipeline_request_descriptor_sets(ctx, dmmv, CEIL_DIV(ne12 * ne13,',1)
        grid='    ggml_pipeline_request_descriptor_sets(ctx, dmmv, CEIL_DIV(ne12 * ne13,'+grid
        grid=grid.replace('ne12 * ne13','ne12 * ne13 * tile_groups')
        grid=once(grid,'(uint32_t)r2, (uint32_t)r3,','(uint32_t)r2, tile_groups>1?tile:(uint32_t)r3,')
        s=s[:start]+head+grid+s[end:]
        s=once(s,'dst->ne[1] <= mul_mat_vec_max_cols && src1->ne[2] * src1->ne[3] == 1','(dst->ne[1] <= mul_mat_vec_max_cols || (dst->op_params[0]==GGML_PREC_F32 && src0->type==GGML_TYPE_Q8_0 && src1->type==GGML_TYPE_F32 && dst->ne[1]<=32 && ggml_is_contiguous(src1))) && src1->ne[2] * src1->ne[3] == 1')
        s=once(s,'    subctx->s->buffer->buf.dispatch(wg0, wg1, wg2);',r'''    if(std::getenv("HS_PARALLEL_DISPATCH")) std::fprintf(stderr,"TP_DISPATCH %s %u %u %u\n",pipeline->name.c_str(),wg0,wg1,wg2);
    subctx->s->buffer->buf.dispatch(wg0, wg1, wg2);''')
        return s
    edit(vk+'ggml-vulkan.cpp',backend)
    def shader(s):
        for v in ('b','d'):
            s=once(s,'batch_idx * p.batch_stride_'+v+';','batch_idx * (p.batch_stride_a==0 ? p.broadcast3 : 1) * p.batch_stride_'+v+';')
        return s
    edit(vk+'vulkan-shaders/mul_mat_vec_base.glsl',shader)
    from wb_plan import apply
    apply(src)
    from pq_join import apply as join
    join(src)
    from p021 import apply as extend_p021
    extend_p021(src)
    write(ROOT/'SOURCE.json',dict(parent='5aae66e05b0f6e8a8b44dac719b2b05b8f84f34f',header_sha256=sha(src/'src/hs_reference_batching.hpp'),changes={p:sha(src/p) for p in ('src/llama-graph.cpp','src/query_head.h','src/llama-context.cpp',vk+'ggml-vulkan.cpp',vk+'vulkan-shaders/mul_mat_vec_base.glsl')}))
if __name__=='__main__':
    ROOT.mkdir(exist_ok=True);stage()
    os.environ['VULKAN_SDK']='C:/VulkanSDK/1.4.357.0';os.environ['PATH']=os.environ['VULKAN_SDK']+'/Bin;'+os.environ['PATH']
    command(['cmake','-S',KIT,'-B',ROOT/'build-00','-G','Visual Studio 17 2022','-A','x64','-DLLAMA_SOURCE='+(ROOT/'source-00').as_posix(),'-DHS_COMPANION_ORACLE=OFF','-DCMAKE_PREFIX_PATH=C:/VulkanSDK/1.4.357.0','-DLLAMA_BUILD_NUMBER=10839','-DLLAMA_BUILD_COMMIT=0cae43063'],ROOT/'configure.log')
    command(['cmake','--build',ROOT/'build-00','--config','Release','--parallel','4'],ROOT/'build.log')
