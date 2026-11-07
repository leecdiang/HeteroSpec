#include "F:/rtx184/loop/native-arms/backend_loop4/ggml/src/hs_loop4_tensor.hpp"
static void replay(ggml_backend_dev_t gpu,const json&j,const fs::path&root){
    auto be=ggml_backend_dev_init(gpu,nullptr);check(be,"CUDA backend init");fs::path src=j.at("replay").get<std::string>();
    auto records=read(src/"receipt.json").at("nodes");std::string route=j.at("route");
    for(const auto&op:records){
        const auto name=op["weight"]["name"].get<std::string>();fs::path p=src/name;
        if(!fs::exists(p/"input.bin"))continue;
        auto weights=bytes(p/"weight.bin"),input=bytes(p/"input.bin");
        int k=op["weight"]["ne"][0],m=op["weight"]["ne"][1];
        check(op["backend"]=="CUDA0" && op["input"]["nb"][1]==k*4 && op["output"]["nb"][1]==m*4,"descriptor");
        auto dir=root/name;fs::create_directories(dir);
        for(int n:{1,4,5,7,8,9,16,31,32}){
            auto ctx=ggml_init({4*1024*1024,nullptr,true});check(ctx,"metadata arena");
            auto w=ggml_new_tensor_2d(ctx,GGML_TYPE_Q8_0,k,m);auto x=ggml_new_tensor_2d(ctx,GGML_TYPE_F32,k,n);
            auto gf=ggml_new_graph_custom(ctx,256,false);ggml_tensor*y=nullptr;int first=0,matmuls=0;size_t joins=0;
            if(route=="backend_loop4" && n>4){y=ggml_mul_mat(ctx,w,x);hs_loop4::mark(y);first=n;matmuls++;}
            if(route=="packed" && n>=8){first=n/4*4;auto groups=ggml_view_3d(ctx,x,k,4,first/4,x->nb[1],4*x->nb[1],0);y=ggml_reshape_2d(ctx,ggml_mul_mat(ctx,w,groups),m,first);matmuls++;}
            int step=route=="scalar"?1:4;
            for(int i=first;i<n;i+=step){int cols=std::min(step,n-i);auto slice=n==cols?x:ggml_view_2d(ctx,x,k,cols,x->nb[1],i*x->nb[1]);auto part=ggml_mul_mat(ctx,w,slice);matmuls++;if(y){y=ggml_concat(ctx,y,part,1);joins+=ggml_nbytes(y);}else y=part;}
            ggml_build_forward_expand(gf,y);auto buf=ggml_backend_alloc_ctx_tensors(ctx,be);check(buf,"device allocation");
            ggml_backend_tensor_set(w,weights.data(),0,ggml_nbytes(w));ggml_backend_tensor_set(x,input.data(),0,ggml_nbytes(x));
            std::vector<double>submit,sync;
            for(int rep=0;rep<4;rep++){if(rep==3 && j.value("diagnostic",false))profile::begin();auto t=Clock::now();check(ggml_backend_graph_compute_async(be,gf)==GGML_STATUS_SUCCESS,"replay compute");submit.push_back(elapsed(t));t=Clock::now();ggml_backend_synchronize(be);sync.push_back(elapsed(t));if(rep==3 && j.value("diagnostic",false))profile::end(dir/(std::to_string(n)+"-gpu.json"));}
            std::vector<char>out(ggml_nbytes(y));ggml_backend_tensor_get(y,out.data(),0,out.size());auto key=std::to_string(n);
            write_bytes(dir/(key+".bin"),out.data(),out.size());save(dir/(key+".json"),{{"route",route},{"width",n},{"submit_s",submit},{"sync_s",sync},{"matmuls",matmuls},{"concat_output_bytes",joins},{"input_bytes",ggml_nbytes(x)}});
            ggml_backend_buffer_free(buf);ggml_free(ctx);
        }
    }
    ggml_backend_free(be);
}
