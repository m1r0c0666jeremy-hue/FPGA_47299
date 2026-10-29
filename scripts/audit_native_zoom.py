"""Strict current-input native evidence; historical five-zoom runs remain historical."""
from pathlib import Path
import argparse,json,datetime,hashlib
from refined_testlib import R
from native_zoom_policy import canonical_build_inputs,compiler_paths,sha
from audit_stage1 import specs,evidence

NATIVE={
 'controls':'STAGE1_K_CONTROLS_PASS', 'zoom_controls':'NATIVE_ZOOM_CONTROLS_PASS',
 'k_keys75m':'STAGE1_K_KEYS_75M_PASS', 'bridge':'NATIVE_BRIDGE_PASS',
 'average':'NATIVE_DOWNSAMPLE_PASS','average_full':'NATIVE_DOWNSAMPLE_PASS source=2560x1440',
 'source_gate':'NATIVE_SOURCE_GATE_PASS','frame_store':'NATIVE_FRAME_STORE_PASS',
 'isp_full':'NATIVE_ISP_PASS','camera_full':'NATIVE_CAMERA_PASS fault0','camera_tail_fault':'NATIVE_CAMERA_PASS fault1',
 'transitions':'NATIVE_TRANSITIONS_PASS six_frames pixels4792320',
 'capture_shared_masks':'NATIVE_SHARED_MASKS_PASS',
 'capture_shared_full':'NATIVE_SHARED_CAPTURE_PASS frames10 pixels9216000',
 'capture_shared_fault':'NATIVE_SHARED_FAULT_PASS frames6',
 'capture_shared_reducer':'NATIVE_SHARED_REDUCER_PASS frames200 quads3200',
 'read_adapter':'NATIVE_READ_ADAPTER_PASS','arbitration_low':'NATIVE_ARBITRATION_PASS','arbitration_dense':'NATIVE_ARBITRATION_PASS',
 'ingress':'NATIVE_INGRESS_PASS','sensor_rom':'NATIVE_SENSOR_ROM_PASS','selector_equivalence':'NATIVE_SELECTOR_EQUIVALENCE_PASS'}
NATIVE.update({f'crop_phase{i}':'NATIVE_CROP_PASS' for i in range(4)})
NATIVE.update({f'video_{z}_{r}':f'NATIVE_VIDEO_PASS zoom{z} rotate{r}' for z in range(3) for r in range(2)})
NATIVE.update({f'colors_{z}_{p}_{r}':f'NATIVE_COLOR_MODES_PASS zoom{z} rotate{r}' for z in range(3) for p in range(2) for r in range(2)})
from test_stage1_camera_readback import cases
NATIVE.update({'camera_readback_'+n:'STAGE1_CAMERA_READBACK_PASS' for n,_,_ in cases})

def native_evidence(name,marker):
 for p in sorted((R/'build/sim/refined').glob('native_zoom_'+name+'_*/native_receipt.json'),reverse=True):
  try:
   d=json.loads(p.read_text(encoding='utf-8'));out=p.parent
   if d['test']!=name:continue
   modules={str((R/'rtl/color_regions'/n).resolve().relative_to(R)):h for n,h in d['rtl'].items()}
   if not all(sha(R/n)==h for n,h in modules.items()):continue
   if sha(out/'tb.sv')!=d['fixture_sha256']:continue
   if sha(R/'scripts/test_native_zoom_core.py')!=d['producer_sha256']:continue
   if not d['producer_inputs'] or not all(sha(R/n)==h for n,h in d['producer_inputs'].items()):continue
   record=R/'reports/refined/regression'/(out.name+'.json');log=record.with_suffix('.log')
   r=json.loads(record.read_text(encoding='utf-8'))
   if r['exit_code'] or r['expected_failure'] or marker not in log.read_text(encoding='utf-8'):continue
   if {(R/k).resolve().relative_to(R).as_posix():v for k,v in r['inputs'].items()}!={k.replace('\\','/'):v for k,v in modules.items()}:continue
   return {'receipt':p.relative_to(R).as_posix(),'receipt_sha256':sha(p),'record':record.relative_to(R).as_posix(),
    'record_sha256':sha(record),'log_sha256':sha(log),'inputs':modules,'fixture_sha256':d['fixture_sha256'],'producer_inputs':d['producer_inputs']}
  except (OSError,ValueError,KeyError):continue
 return None

def audit():
 inputs={p.relative_to(R).as_posix():sha(p) for p in compiler_paths()}
 canonical_build_inputs(inputs)
 # Reuse only checks of unchanged logic. The old integration records remain
 # separately identified; none qualify a new camera/reader profile.
 legacy={n:evidence(n,*s) for n,s in specs().items()}
 new={n:native_evidence(n,m) for n,m in NATIVE.items()}
 guard=None
 for p in sorted((R/'build').glob('native_zoom_guard_*/receipt.json'),reverse=True):
  g=json.loads(p.read_text(encoding='utf-8'))
  if g.get('inputs')==inputs and g.get('case_count')==11 and g.get('status')=='NATIVE_GUARDS_PASS' and g.get('producer_sha256')==sha(R/'scripts/test_native_zoom_guards.py') and g.get('policy_sha256')==sha(R/'scripts/native_zoom_policy.py') and g.get('codegen_sha256')==sha(R/'scripts/native_zoom_codegen.py'):
   guard={'record':p.relative_to(R).as_posix(),'sha256':sha(p),'cases':11};break
 return {'status':'PASS' if all(legacy.values()) and all(new.values()) and guard else 'INCOMPLETE',
  'scope':'155 original-module regressions plus independent native-profile qualification; historical 3x/4x are not native cases',
  'compiler_inputs':inputs,'native_required':len(new),'native_passed':sum(bool(x) for x in new.values()),
  'legacy_required':len(legacy),'legacy_passed':sum(bool(x) for x in legacy.values()),
  'native':new,'legacy_unchanged':legacy,'negative_guards':guard,'missing_native':[n for n,e in new.items() if not e],
  'missing_legacy':[n for n,e in legacy.items() if not e]}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--require-pass',action='store_true');a=ap.parse_args()
 result=audit();(R/a.output).write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
 print({k:v for k,v in result.items() if k not in ('compiler_inputs','native','legacy_unchanged')})
 if a.require_pass and result['status']!='PASS':raise SystemExit(2)
