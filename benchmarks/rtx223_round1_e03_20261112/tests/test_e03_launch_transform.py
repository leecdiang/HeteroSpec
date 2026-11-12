import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"e03/launch_budget"))
from transform_launches import CoverageError,transform_text


class LaunchTransform(unittest.TestCase):
    def test_comments_strings_and_raw_literals_are_not_sites(self):
        source='// fake<<<g,b>>>();\nconst char *s="cudaGraphLaunch(x,y)";\nconst char *r=R"tag(k<<<g,b>>>())tag";\n'
        output,rows=transform_text(source,"literal.cu")
        self.assertEqual(output,source)
        self.assertEqual(rows,[])

    def test_raw_launch_guard_precedes_configuration_submission(self):
        source='kernel<<<dim3((n+31)/32, 2), block, 0, stream>>>(x);'
        output,rows=transform_text(source,"nested.cu")
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["kind"],"prelaunch-raw")
        self.assertIn('<<<(hs_launch_budget_before_launch_v1("nested.cu:1:raw"), dim3((n+31)/32, 2)), block',output)

    def test_template_ambiguity_is_refused(self):
        with self.assertRaises(CoverageError):
            transform_text('kernel<<<grid_template<A,B>(), block>>>(x);',"ambiguous.cu")

    def test_launch_ex_and_raw_are_separate_paths_not_double_entry_guard(self):
        text='if(pdl) cudaLaunchKernelEx(&cfg, kernel, x); else kernel<<<g,b>>>(x);'
        output,rows=transform_text(text,"wrapper.cuh")
        self.assertEqual(sum(r["kind"]=="prelaunch-api" for r in rows),1)
        self.assertEqual(sum(r["kind"]=="prelaunch-raw" for r in rows),1)
        self.assertEqual(output.count("hs_launch_budget_before_launch_v1"),2)

    def test_opaque_cooperative_graph_blas_cub_and_memory_are_denied(self):
        calls=['cudaLaunchCooperativeKernel(k,g,b,a,0,s)','cudaGraphLaunch(g,s)',
               'cudaStreamBeginCapture(s,mode)','cublasCreate(&h)','cublasGemmEx(h,a)',
               'cub::DeviceScan::InclusiveSum(tmp,n,x,y,count,s)','cudaMemsetAsync(x,0,n,s)',
               'cudaMemcpyAsync(a,b,n,kind,s)','cudaLaunchHostFunc(s,f,p)','ncclAllReduce(a,b,n,t,op,c,s)']
        output,rows=transform_text(';'.join(calls)+';',"opaque.cu")
        self.assertEqual(len(rows),len(calls))
        self.assertTrue(all(r["kind"].startswith("deny-") for r in rows))
        self.assertEqual(output.count("hs_launch_budget_deny_opaque_v1"),len(calls))

    def test_runtime_activity_is_unknown_not_misreported_as_counted(self):
        _,rows=transform_text('cudaMalloc(&p,n);cudaGetDevice(&d);',"runtime.cu")
        self.assertEqual([r["kind"] for r in rows],["runtime-call-unqualified"]*2)


if __name__=="__main__": unittest.main()
