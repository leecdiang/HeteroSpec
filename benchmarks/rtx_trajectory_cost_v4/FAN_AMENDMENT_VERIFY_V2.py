"""Additive archive metadata path adapter for the original independent fan verifier."""
import sys,json,importlib.util
from pathlib import Path

def check(root):
    root=Path(root);source=Path(__file__).with_name('FAN_AMENDMENT_VERIFY.py')
    spec=importlib.util.spec_from_file_location('fan_amendment_original_independent_verifier',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);original_sha=module.sha
    def mapped_sha(path):
        path=Path(path)
        if (root/'metadata').exists() and not path.exists():
            relative=path.relative_to(root).as_posix()
            if relative.startswith('benchmarks/rtx_trajectory_cost_v4/'):path=root/'metadata'/path.name
        return original_sha(path)
    module.sha=mapped_sha
    result=module.check(root);result['archive_metadata_path_adapter']='V2; original frozen assertions and numerical verifier unchanged'
    return result
if __name__=='__main__':print(json.dumps(check(sys.argv[1]),ensure_ascii=True))
