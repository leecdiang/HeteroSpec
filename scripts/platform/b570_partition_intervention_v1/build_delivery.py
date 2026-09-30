"""Derive delivery with the final independent all-endpoint verifier."""
from pathlib import Path

def main():
    root=Path(__file__).resolve().parent
    text=(root/'deliver.py').read_text(encoding='utf-8')
    text=text.replace("SRC/'verify.py'","SRC/'verify_complete.py'")
    text=text.replace('scripts/platform/b570_partition_intervention_v1/verify.py --root .','scripts/platform/b570_partition_intervention_v1/verify_complete.py --root .')
    text=text.replace("SRC/'verify_archive.py'","SRC/'verify_archive_complete.py'")
    text=text.replace("    status=result['status'];q=", "    subprocess.run([sys.executable,str(SRC/'characterize.py'),'--root',str(ROOT),'--output',str(PLAN/'ENDPOINT_ANALYSIS.json')],check=True)\n    status=result['status'];q=")
    marker="    text+='The old 72/72"
    addition="    text+=f\"Raw-score effects: {result.get('score_difference_executions',0)} executions, {result.get('score_difference_prompts',0)} prompts. Downstream trajectory differences: {result.get('trajectory_difference_executions',0)} executions, {result.get('trajectory_difference_prompts',0)} prompts.\\n\\n\"\n"
    assert text.count(marker)==1
    text=text.replace(marker,addition+marker)
    # Retain the full upstream copyright/license in the portable package.
    text=text.replace("'common/sampling.cpp','common/sampling.h'", "'LICENSE','common/sampling.cpp','common/sampling.h'")
    (root/'deliver_complete.py').write_text(text,encoding='utf-8',newline='\n')
    text=(root/'verify_archive.py').read_text(encoding='utf-8').replace('verify.py','verify_complete.py')
    (root/'verify_archive_complete.py').write_text(text,encoding='utf-8',newline='\n')

if __name__=='__main__':main()
