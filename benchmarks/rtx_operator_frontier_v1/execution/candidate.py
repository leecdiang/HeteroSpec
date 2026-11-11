"""Pack full four-column tiles into one broadcasted matmul. Keep a bounded tail."""
import os,shutil,subprocess,time
from host import *
def prepare():
    new=ROOT/"candidate01";new.mkdir()
    shutil.copytree(FROZEN/"source",new/"source")
    p=new/"source/src/llama-graph.cpp";s=p.read_text(encoding="utf8")
    old='''        for (int64_t i = 0; i < cur->ne[1]; i += 4) {'''
    assert s.count(old)==1
    s=s.replace(old,'''        int64_t first_tail = 0;
        // Dense F32 columns share one Q8 weight. Preserve the four-column
        // reduction descriptor and expose independent groups in dimension 2.
        if (ggml_is_contiguous(cur) && w->ne[2]==1 && w->ne[3]==1 && cur->ne[1]>=8) {
            first_tail = cur->ne[1] / 4 * 4;
            auto * groups = ggml_view_3d(ctx0, cur, cur->ne[0], 4, first_tail/4,
                                         cur->nb[1], 4*cur->nb[1], 0);
            auto * batch = ggml_mul_mat(ctx0, w, groups);
            ggml_format_name(batch,"frontier_packed_%s",w->name);
            res = ggml_reshape_2d(ctx0,batch,w->ne[1],first_tail);
        }
        for (int64_t i = first_tail; i < cur->ne[1]; i += 4) {''')
    p.write_text(s,encoding="utf8")
    (new/"core").mkdir();(new/"bin").mkdir()
    for f in (FROZEN/"core").glob("*.cmd"):shutil.copy2(f,new/"core"/f.name)
    for f in (FROZEN/"bin").glob("*.dll"):os.link(f,new/"bin"/f.name)
    for stage in ("configure","core"):
        args=[s.replace(str(FROZEN),str(new)).replace(FROZEN.as_posix(),new.as_posix()) for s in read(sorted(FROZEN.glob(stage+"-*.json"))[-1])["argv"]]
        with (new/(stage+".log")).open("xb") as f:subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,timeout=3600,check=True)
    build("new-driver",core=new)
if __name__=="__main__":prepare()

