"""Packaging-only Windows short-path adapter; frozen scientific sources stay intact."""
import os
from pathlib import Path
import deliver_complete as delivery
import study

def main():
    alias = Path('C:/hs/bpiv1pkg')
    assert alias.exists() and os.path.samefile(alias, study.ROOT), 'Create a junction to this checkout first'
    temporary = Path('C:/hs/bpiv1tmp')
    temporary.mkdir(parents=True, exist_ok=True)
    os.environ['TMP'] = os.environ['TEMP'] = str(temporary)
    study.ROOT = delivery.ROOT = alias
    delivery.PLAN = alias/'benchmarks/b570_partition_intervention_v1'
    delivery.SRC = alias/'scripts/platform/b570_partition_intervention_v1'
    delivery.RAW = alias/'artifacts/b570_partition_intervention_v1/raw'
    delivery.archive()

if __name__ == '__main__':
    main()
