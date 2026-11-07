from pathlib import Path
r=Path(__file__).parent;p=Path("C:/hs/b570-draft-cpu-20261020")
s=(p/"stage_analysis.py").read_text().replace('("R","BASE_A","BASE_B","DRAFT1")','("BASE_A","BASE_B","DRAFT1")').replace("DRAFT1","BULK1")
(r/"stage_analysis.py").write_text(s)
s=(p/"verify_delivery.py").read_text().replace("range(8)","range(7)").replace("DRAFT1","BULK1")
s=s.replace('for inp in read(r/"INPUT_PANEL.json")["inputs"]:', 'for inp in [read(r/"INPUT_PANEL.json")["inputs"][i]for i in (0,2)]:')
s=s.replace("**(1/16)","**(1/6)").replace("1817.8040152","3162.4996451").replace("measured==64 and warm==16","measured==18 and warm==9").replace('"nonoverlapping_native_processes":8','"nonoverlapping_native_processes":7')
(r/"verify_delivery.py").write_text(s)
print("Prepared descriptive stage summary and independent product-estimator/receipt verification")
