static void replay(ggml_backend_dev_t gpu,const json&j,const fs::path&root){
    auto be=ggml_backend_dev_init(gpu,nullptr);check(be,"CUDA backend init");fs::path src=j.at("replay").get<std::string>();
    auto records=read(src/"receipt.json").at("nodes");
    for(const auto&op:records){
        const auto name=op["weight"]["name"].get<std::string>();fs::path p=src/name;
        auto weights=bytes(p/"weight.bin"),input=bytes(p/"input.bin"),live=bytes(p/"output.bin");
        int k=op["weight"]["ne"][0],m=op["weight"]["ne"][1];
        check(op["backend"]=="CUDA0" && op["input"]["nb"][1]==k*4 && op["output"]["nb"][1]==m*4,"descriptor");
        auto dir=root/name;fs::create_directories(dir);
        for(int n:{2,4,8,16,32}){
            for(std::string route:{"scalar","tile","wide","packed"}){
                if(route=="packed" && n<8)continue;
                auto t=Clock::now();
                auto ctx=ggml_init({4*1024*1024,nullptr,true});check(ctx,"metadata arena");
                auto w=ggml_new_tensor_2d(ctx,GGML_TYPE_Q8_0,k,m);
                auto x=ggml_new_tensor_2d(ctx,GGML_TYPE_F32,k,n);
                auto gf=ggml_new_graph_custom(ctx,256,false);
                ggml_tensor*y=nullptr;int matmuls=0;size_t joins=0;
                if(route=="packed"){
                    auto groups=ggml_reshape_3d(ctx,x,k,4,n/4);
                    y=ggml_reshape_2d(ctx,ggml_mul_mat(ctx,w,groups),m,n);matmuls=1;
                }else{
                    int step=route=="tile"?4:route=="scalar"?1:n;
                    for(int i=0;i<n;i+=step){
                        int cols=std::min(step,n-i);
                        auto slice=n==cols?x:ggml_view_2d(ctx,x,k,cols,x->nb[1],i*x->nb[1]);
                        auto part=ggml_mul_mat(ctx,w,slice);matmuls++;
                        if(y){y=ggml_concat(ctx,y,part,1);joins+=ggml_nbytes(y);}else y=part;
                    }
                }
                ggml_build_forward_expand(gf,y);
                double plan=elapsed(t);auto buf=ggml_backend_alloc_ctx_tensors(ctx,be);check(buf,"device allocation");
                ggml_backend_tensor_set(w,weights.data(),0,ggml_nbytes(w));ggml_backend_tensor_set(x,input.data(),0,ggml_nbytes(x));
                std::vector<double>submit,sync;for(int rep=0;rep<4;rep++){
                    if(rep==3)profile::begin();t=Clock::now();check(ggml_backend_graph_compute_async(be,gf)==GGML_STATUS_SUCCESS,"replay compute");
                    submit.push_back(elapsed(t));t=Clock::now();ggml_backend_synchronize(be);sync.push_back(elapsed(t));if(rep==3)profile::end(dir/(std::to_string(n)+"-"+route+"-gpu.json"));
                }
                std::vector<char>out(ggml_nbytes(y));ggml_backend_tensor_get(y,out.data(),0,out.size());
                auto key=std::to_string(n)+"-"+route;write_bytes(dir/(key+".bin"),out.data(),out.size());
                save(dir/(key+".json"),{{"plan_s",plan},{"submit_s",submit},{"sync_s",sync},{"matmuls",matmuls},{"concat_output_bytes",joins},{"bytes_equal_live_prefix",std::equal(out.begin(),out.end(),live.begin())}});
                ggml_backend_buffer_free(buf);ggml_free(ctx);
            }
        }
    }
    ggml_backend_free(be);
}
