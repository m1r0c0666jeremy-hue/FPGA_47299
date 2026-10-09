"""Unchanged original four-mode algorithm, new independent log."""
from pathlib import Path
r=Path(__file__).resolve().parents[1]
p=r/'scripts/test_imagepreprocess_10_3.py'
code=p.read_text(encoding='utf-8').replace('reports/imagepreprocess_10_3_simulation.log','reports/dualcolor_preprocess_regression.log')
exec(compile(code,str(p),'exec'),{'__file__':str(p),'__name__':'__main__'})
