#include "loop4_tensor.hpp"
#include <iostream>
#include <vector>
using namespace hs_loop4;
int main(){
 int checks=0;auto check=[&](bool b){++checks;if(!b)throw std::runtime_error("check "+std::to_string(checks));};
 for(uint64_t q=5;q<=32;++q)for(uint64_t blocks:{1u,8u,17u})for(uint64_t rows:{1u,3u,127u}){
    const auto p=plan(q,blocks,rows,36);check(p.count==(q+3)/4);
    std::vector<int> covered(q,0);std::vector<uint8_t> quantized(q*blocks*36);
    std::vector<uint32_t> expected(q*rows),actual(q*rows,0xffffffffu);
    for(size_t i=0;i<quantized.size();++i)quantized[i]=uint8_t(i*13+7);
    for(uint64_t c=0;c<q;++c)for(uint64_t r=0;r<rows;++r)expected[c*rows+r]=uint32_t(quantized[c*blocks*36]+r);
    for(const auto & tile:p){
      check(tile.width>=1 && tile.width<=4);check(tile.begin+tile.width<=q);
      check(tile.input_byte_offset==tile.begin*blocks*36);check(tile.output_float_offset==tile.begin*rows);
      check(tile.input_group_blocks==tile.width*blocks);check(tile.output_group_floats==tile.width*rows);
      for(uint64_t c=0;c<tile.width;++c){++covered[tile.begin+c];for(uint64_t r=0;r<rows;++r)
        actual[tile.output_float_offset+c*rows+r]=uint32_t(quantized[tile.input_byte_offset+c*blocks*36]+r);}
    }
    check(actual==expected);for(auto n:covered)check(n==1);
 }
 for(auto q:{0u,1u,4u,33u}){bool bad=false;try{plan(q,1,1,36);}catch(const std::invalid_argument&){bad=true;}check(bad);}
 for(auto args:std::vector<std::array<uint64_t,4>>{{8,0,1,36},{8,1,0,36},{8,1,1,0},{32,UINT64_MAX,1,36},{32,1,UINT64_MAX,36},{8,1,1,UINT64_MAX}}){
    bool bad=false;try{plan(args[0],args[1],args[2],args[3]);}catch(const std::exception&){bad=true;}check(bad);
 }
 auto * ctx=ggml_init({1024*1024,nullptr,true});check(ctx!=nullptr);
 auto * w=ggml_new_tensor_2d(ctx,GGML_TYPE_Q8_0,32,8);auto * x=ggml_new_tensor_2d(ctx,GGML_TYPE_F32,32,8);
 auto * out=ggml_mul_mat(ctx,w,x);mark(out);require(w,x,out);check(marked(out));
 bool bad=false;try{mark(out);}catch(const std::invalid_argument&){bad=true;}check(bad);
 x->nb[1]++;bad=false;try{require(w,x,out);}catch(const std::invalid_argument&){bad=true;}check(bad);x->nb[1]--;
 out->op_params[1]=1;bad=false;try{require(w,x,out);}catch(const std::invalid_argument&){bad=true;}check(bad);out->op_params[1]=0;
 x->ne[2]=2;bad=false;try{require(w,x,out);}catch(const std::invalid_argument&){bad=true;}check(bad);x->ne[2]=1;
 out->op_params[15]=0;check(!marked(out));ggml_free(ctx);
 std::cout<<"LOOP4_CPU_GEOMETRY_CHECKS="<<checks<<" CUDA_COMPILE=NOT_RUN GPU_EXECUTIONS=0\n";
}
