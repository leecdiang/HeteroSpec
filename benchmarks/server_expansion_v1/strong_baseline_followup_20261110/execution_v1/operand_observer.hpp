#pragma once
// Heavy-only capture of the first registered 32-column G projection. The
// original scalar nodes supply each actual column; CPU assembly is explicit.
inline fs::path sb_operand_root;
inline std::map<std::string,json> sb_operand_specs;
inline std::map<std::string,std::set<int>> sb_operand_seen;
inline int sb_operand_width=0;
inline void sb217_operand_set_call(int width,int base){sb_operand_width=(base==0&&(width==4||width==32))?width:0;}
inline void sb217_operand_configure(const json& job,const fs::path& out){
    if(!job.value("capture_operands",false))return;
    need(job.at("arm")=="G","Operand provenance capture requires graph scalar G");
    sb_operand_root=out/"operands";
    for(const auto& spec:job.at("operand_capture_classes")){
        std::string name=spec.at("weight_name");need(!name.empty()&&name.find_first_of("/\\")==std::string::npos,"Operand weight name");
        need(sb_operand_specs.emplace(name,spec).second,"Duplicate captured shape class");
    }
    need(sb_operand_specs.size()==8,"Complete frozen type/shape class inventory");
}
inline int sb_operand_column(ggml_tensor* t){
    const std::string name=t->name;const auto at=name.rfind('_');
    need(name.rfind("hs_ref1_loop_",0)==0&&at!=std::string::npos,"Actual scalar G column identity");
    const auto text=name.substr(at+1);need(!text.empty()&&text.find_first_not_of("0123456789")==std::string::npos,"G column suffix");
    int col=std::stoi(text);need(col>=0&&col<32,"Frozen first q32 columns");return col;
}
static bool q32_operand_wanted(ggml_tensor* t,const std::string& phase){
    if(!sb_operand_width||sb_operand_specs.empty()||phase!="VERIFY"||t->op!=GGML_OP_MUL_MAT||!t->src[0]||!t->src[1])return false;
    auto i=sb_operand_specs.find(t->src[0]->name);if(i==sb_operand_specs.end())return false;
    auto key=std::to_string(sb_operand_width)+":"+i->first;
    if(sb_operand_seen[key].size()==size_t(sb_operand_width))return false;
    return !sb_operand_seen[key].count(sb_operand_column(t));
}
static void q32_operand_copy(ggml_tensor* t){
    auto* w=t->src[0];auto* x=t->src[1];const auto& spec=sb_operand_specs.at(w->name);const int col=sb_operand_column(t);
    const int width=sb_operand_width;need((width==4||width==32)&&col<width,"Actual registered capture width");
    const std::string seen_key=std::to_string(width)+":"+w->name;
    const fs::path folder=width==32?sb_operand_root:sb_operand_root/"q4";
    need(w->ne[0]==spec.at("K")&&w->ne[1]==spec.at("M")&&w->ne[2]==1&&w->ne[3]==1&&
         ggml_type_name(w->type)==spec.at("type_ggml").get<std::string>()&&x->type==GGML_TYPE_F32&&
         x->ne[0]==w->ne[0]&&x->ne[1]==1&&x->ne[2]==1&&x->ne[3]==1&&
         t->ne[0]==w->ne[1]&&t->ne[1]==1&&ggml_is_contiguous(w)&&ggml_is_contiguous(x),"Frozen real operand descriptor");
    for(auto* tensor:{w,x,t}){
        need(tensor->buffer,"Operand buffer");auto* dev=ggml_backend_buft_get_device(ggml_backend_buffer_get_type(tensor->buffer));
        need(dev&&ggml_backend_dev_type(dev)==GGML_BACKEND_DEVICE_TYPE_GPU,"Operand actual device");
    }
    fs::create_directories(folder);const std::string name=w->name;
    auto copy=[&](ggml_tensor* tensor,const fs::path& p){
        std::vector<uint8_t> value(ggml_nbytes(tensor));ggml_backend_tensor_get(tensor,value.data(),0,value.size());
        tpds_decisive::capture_write_new(p,value.data(),value.size());return json{{"file",p.filename().string()},{"bytes",value.size()},{"sha256",hash_file(p)}};
    };
    json weight;
    if(sb_operand_seen[seen_key].empty())weight=copy(w,folder/(name+".weight.bin"));
    const auto id=name+"-col-"+std::to_string(col);
    auto input=copy(x,folder/(id+".activation.f32"));auto output=copy(t,folder/(id+".output.f32"));
    json record={{"origin","registered real G initial-prefix graph, original scalar column"},{"capture_width",width},{"column",col},
                 {"weight_name",name},{"shape_class",spec},{"activation",input},{"output",output}};
    auto layout=[](ggml_tensor* tensor){return json{{"ne",{tensor->ne[0],tensor->ne[1],tensor->ne[2],tensor->ne[3]}},
        {"nb",{tensor->nb[0],tensor->nb[1],tensor->nb[2],tensor->nb[3]}},{"view_offset",tensor->view_offs}};};
    record["actual_weight_layout"]=layout(w);record["actual_input_column_layout"]=layout(x);record["actual_output_layout"]=layout(t);
    if(x->view_src)record["actual_input_view_parent_layout"]=layout(x->view_src);
    if(!weight.is_null())record["weight"]=weight;
    dump(folder/(id+".json"),record);need(sb_operand_seen[seen_key].insert(col).second,"Duplicate captured column");
}
inline json sb217_operand_complete(){
    json result=json::array();for(int width:{4,32})for(const auto& entry:sb_operand_specs){
        need(sb_operand_seen[std::to_string(width)+":"+entry.first].size()==size_t(width),"Missing real input columns; no synthetic replacement");
        result.push_back({{"weight",entry.first},{"columns",width}});
    }return result;
}
