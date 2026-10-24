"""Reuse the exact proven writer stress bench, with new log/output locations."""
from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1];O=R/'build/sim/color_regions/ingress';O.mkdir(parents=True,exist_ok=True)
s=(R/'scripts/test_robust_ingress.py').read_text(encoding='utf-8')
s=s.replace('Path(__file__).resolve().parents[1]',f'Path({str(R)!r})').replace('build/sim/robust','build/sim/color_regions/ingress').replace('reports/robust_ingress.log','reports/color_regions_ingress.log')
p=O/'run.py';p.write_text(s,encoding='utf-8');subprocess.run([sys.executable,str(p)],cwd=R,check=True)
