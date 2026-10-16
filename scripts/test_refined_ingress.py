"""Reuse independent writer byte/address and clock/fault oracles in new outputs."""
from pathlib import Path
import datetime,hashlib,json
R=Path(__file__).resolve().parents[1]
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
source=(R/'scripts/test_stable_ingress.py').read_text(encoding='utf-8')
source=source.replace("O=R/'build/sim/stable_ingress'",f"O=R/'build/sim/refined_ingress_{stamp}'")
source=source.replace('reports/transparent_ring/regression/stable_ingress.log',f'reports/refined/regression/ingress_{stamp}.log')
source=source.replace("R/'user_source/hdl_source/video_in.v'","R/'rtl/color_regions/refined_video_in.v'")
source=source.replace("s=s[:s.index('module divider')]","s=s[:s.index('module divider')].replace('video_in ', 'refined_video_in ')")
source=source.replace("for full in (False,True):","vendor.append(R/'rtl/color_regions/refined_reset_bridge.v')\nfor full in (False,True):")
source=source.replace('for cp,dp in [(8,7),(5,11),(11,5)]:',"robustbench=O/'robust.sv'\nrobustbench.write_text((R/'sim/tb_robust_ingress.sv').read_text(encoding='utf-8').replace('video_in ', 'refined_video_in '),encoding='utf-8')\nfor cp,dp in [(8,7),(5,11),(11,5)]:")
source=source.replace("R/'sim/tb_robust_ingress.sv',*vendor","robustbench,*vendor")
source=source.replace('STABLE_INGRESS','REFINED_INGRESS')
files=[R/'rtl/color_regions'/f'{n}.v' for n in ('refined_video_in','refined_reset_bridge','stable_awb','stable_packer')]
before={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
exec(compile(source,__file__,'exec'),{'__file__':__file__,'__name__':'__main__'})
assert before=={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(R/f'reports/refined/regression/ingress_{stamp}.json').write_text(json.dumps(dict(inputs=before,passed=True),indent=2),encoding='utf-8')
