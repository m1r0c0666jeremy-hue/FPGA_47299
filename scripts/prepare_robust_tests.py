"""One-time setup of independent test/build entries; do not rerun after edits."""
from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parents[1]
def read(p):return (r/p).read_text(encoding='utf-8-sig')
def write(p,s):(r/p).write_text(s,encoding='utf-8',newline='\n')
project=read('td_project/target_lock_candidates.al').replace('<Name>target_lock_candidates</Name>','<Name>target_lock_robust</Name>')
write('td_project/target_lock_robust.al',project)
write('scripts/build_target_lock_robust.tcl',read('scripts/build_target_lock_candidates.tcl').replace('target_lock_candidates','target_lock_robust').replace('TARGET_LOCK_CANDIDATES','TARGET_LOCK_ROBUST'))
for name in ('unit','video','regression'):
 s=read(f'scripts/test_candidate_{name}.py').replace('build/sim/candidate','build/sim/robust').replace('reports/candidate_', 'reports/robust_')
 write(f'scripts/test_robust_{name}.py',s)
s=read('scripts/candidate_reference.py').replace('30*bbox','0*bbox').replace('64<=area<=20000','32<=area<=921600').replace('min(areas)<64 or max(areas)>20000','min(areas)<32 or max(areas)>921600')
write('scripts/robust_reference.py',s)
s=read('scripts/test_candidate_detection.py').replace('from candidate_reference','from robust_reference').replace('build/sim/candidate','build/sim/robust').replace('reports/candidate_', 'reports/robust_').replace('tb_candidate_pipeline','tb_robust_pipeline')
s=s.replace('m>=80 and m-o1>=32 and m-o2>=32 and 2*m>=3*o1 and 2*m>=3*o2','m>=40 and m-o1>=12 and m-o2>=12 and 8*m>=9*o1 and 8*m>=9*o2')
s=s.replace('min(v1,v2)>=80 and min(v1,v2)-other>=24 and 4*min(v1,v2)>=5*other and max(v1,v2)<=2*min(v1,v2)','min(v1,v2)>=40 and min(v1,v2)-other>=12 and 8*min(v1,v2)>=9*other and max(v1,v2)<=4*min(v1,v2)')
# Keep all old boundary colors and add new minima/difference/ratio/balance and
# light/dark red/blue/yellow/purple samples, testing each palette independently.
s=s.replace('for color in colors:', 'colors += [(40,40,28),(39,40,0),(40,40,29),(108,108,96),(107,107,96),(160,40,0),(161,40,0),(200,170,170),(40,12,12),(170,170,200),(12,12,40),(200,200,170),(200,170,200),(255,244,0),(255,243,0)]\nfor color in colors:')
write('scripts/test_robust_detection.py',s)
params='.COLOR_MIN(40),.COLOR_DIFF(12),.RATIO_NUM(9),.RATIO_DEN(8),.AREA_MIN(32),.AREA_MAX(921600),.FILL_PERCENT_MIN(0),.YP_MIN(40),.YP_DIFF(12),.YP_RATIO_NUM(9),.YP_RATIO_DEN(8),.YP_BALANCE(4),'
s=read('sim/tb_candidate_pipeline.sv').replace('tb_candidate_pipeline','tb_robust_pipeline').replace('target_detector #(','target_detector #('+params).replace('target_tracker #(','target_tracker #(.SEP_MAX(1468),').replace('sep<=360000','sep<=2155024')
write('sim/tb_robust_pipeline.sv',s)
vendor={'user_source/hdl_source/video_in.v':hashlib.sha256((r/'user_source/hdl_source/video_in.v').read_bytes()).hexdigest()}
write('reports/robust_vendor_changes.json',json.dumps(vendor,indent=2)+'\n')
print('Prepared independent robust test/build entries')
