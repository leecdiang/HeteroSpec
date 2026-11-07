"""Preserve row order and avoid copying an ever-growing prefix at query width 32."""
from paths import once
def apply(src):
    p=src/'src/query_head.h';s=p.read_text(encoding='utf-8')
    s=once(s,'    if (mode==Mode::PQ) {','    if (mode==Mode::PQ) {\n        std::vector<ggml_tensor *> columns;')
    s=once(s,'            b.out=b.out?ggml_concat(ctx,b.out,col,1):col;\n        }\n        return b;','''            columns.push_back(col);
        }
        while (columns.size()>1) {
            std::vector<ggml_tensor *> joined;
            for (size_t j=0;j<columns.size();j+=2) {
                joined.push_back(j+1==columns.size() ? columns[j] : ggml_concat(ctx,columns[j],columns[j+1],1));
            }
            columns.swap(joined);
        }
        b.out=columns.front();
        return b;''')
    p.write_text(s,encoding='utf-8',newline='\n')
