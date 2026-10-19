"""Read-only audit of the refined branch, regression evidence and frozen build."""
from pathlib import Path
import argparse,hashlib,json,re,subprocess
R=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def evidence(prefix,required=()):
 records=[]
 for p in (R/'reports/refined/regression').glob(prefix+'_*.json'):
  d=json.loads(p.read_text(encoding='utf-8-sig'))
  if not set(required).issubset({n.replace('\\','/') for n in d.get('inputs',{})}):continue
  if (d.get('exit_code')!=0 and not d.get('passed')) or d.get('expected_failure'):continue
  if not all((R/name).is_file() and sha(R/name)==v for name,v in d.get('inputs',{}).items()):continue
  log=p.with_suffix('.log')
  if log.is_file() and 'PASS' in log.read_text(encoding='utf-8'):records.append((p,d))
 if not records:raise AssertionError('Missing current-source passing evidence: '+prefix)
 p,d=max(records,key=lambda v:v[0].name)
 return dict(record=p.relative_to(R).as_posix(),record_sha256=sha(p),log_sha256=sha(p.with_suffix('.log')),inputs=d['inputs'])
def required_inputs(prefix):
 required=[]
 if prefix=='camera_relay_equivalence' or prefix.startswith('camera_relay_production_'):
  required.append('rtl/color_regions/stable_top.v')
 if prefix.startswith('camera_relay_production_'):required.append('rtl/color_regions/refined_camera_config.v')
 if prefix.startswith('shared_hue_'):required.append('rtl/color_regions/stable_model_lane.v')
 if prefix=='hue_retime_equivalence':required.append('rtl/color_regions/stable_model_lane.v')
 if prefix.startswith('recovery_mailbox_equivalence_'):required.append('rtl/color_regions/stable_memory_video_out.v')
 if prefix.startswith('capture_history_pipeline_'):required.append('rtl/color_regions/stable_capture.v')
 if prefix.startswith('refined_v4_live_'):required.append('rtl/color_regions/refined_frame_store.v')
 if prefix.startswith(('refined_v4_live_','refined_video_','final_video_drain_')) or prefix in ('final_missing_snapshot','arbitration_bw240_recover','failed_bus_wait_peak'):
  required.append('rtl/color_regions/refined_line_reader.v')
 if prefix=='controls_with_camera_pause':required.append('rtl/color_regions/refined_controls.v')
 if prefix=='footer_late_abort_after':required.append('rtl/color_regions/refined_osd.v')
 if prefix=='tracker_storage_equivalence' or prefix in ('history_full_rgb_after','capture_diagnostics_v4','tracker_identity_adversarial','tracker_quality_and_diagnostics') or prefix.startswith('refined_v4_live_'):
  required.append('rtl/color_regions/stable_tracker.v')
 return tuple(required)
def checkpoint_report_signature(path,parent,out):
 text=path.read_text(encoding='utf-8').replace('\r','')
 for p in (parent,out):text=text.replace(p.as_posix(),'<ATTEMPT>')
 return '\n'.join(line.rstrip() for line in text.split('\n') if not re.match(r'^(Generated[ \t]+:|[|][ \t]+Date[ \t]+:|Generated (on|at)|Date:|Time:)',line.strip())).strip()

def canonical_build_inputs(inputs):
 names=set(inputs)
 assert {n for n in names if n.endswith('.al')}=={'td_project/target_color_regions_refined.al'},'Noncanonical project entry'
 assert all(not Path(n).is_absolute() and not Path(n).drive and '..' not in Path(n).parts and not n.replace('\\','/').startswith('build/') for n in names),'Private/escaped compiler input'
 required={'rtl/color_regions/'+n for n in ('stable_tracker.v','stable_capture.v','stable_grid.v','refined_line_reader.v','refined_frame_store.v')}
 assert required.issubset(names),'Noncanonical core module paths'
def audit(attempt=None,regression=False):
 branch=subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip()
 assert branch=='release/transparent-ring-stability-20261015',branch
 subprocess.run(['git','merge-base','--is-ancestor','2f79847f8443fb18f3896a6b88ae9b75c06c9ff8','HEAD'],cwd=R,check=True)
 subprocess.run([__import__('sys').executable,'-X','utf8',str(R/'scripts/refined_protection_current.py')],cwd=R,check=True)
 from generate_refined_regions import assets
 for name,value in assets().items():
  data=value if isinstance(value,bytes) else value.replace('\r\n','\n').encode('utf-8')
  assert (R/name).read_bytes()==data,'generated: '+name
 # Image/overlay rendering is identical. Footer diagnostic capture moves from
 # row 620 to 625; the separate late-abort pixel regression covers that change.
 a=(R/'rtl/color_regions/refined_osd.v').read_text(encoding='utf-8').replace('module refined_osd(', 'module stable_osd(').replace('refined_footer_program_rom program_rom','stable_footer_program_rom program_rom').replace('I_de && y==625 && x==0','I_de && y==620 && x==0')
 assert a==(R/'rtl/color_regions/stable_osd.v').read_text(encoding='utf-8')
 b=(R/'rtl/color_regions/refined_footer_program_rom.v').read_text(encoding='utf-8').replace('refined_footer_program_rom','stable_footer_program_rom').replace('ram_style="block"','rom_style="bram"')
 assert b==(R/'rtl/color_regions/stable_footer_program_rom.v').read_text(encoding='utf-8')
 result=dict(branch=branch,head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),protection_pass=True,generator_pass=True,image_renderer_identical=True,footer_capture_row=625)
 if regression:
  writer=(R/'rtl/color_regions/refined_video_in.v').read_text(encoding='utf-8').replace('module refined_video_in (','module arbitration_video_in #(parameter BW=240)(').replace('burst_count==239','burst_count==BW-1').replace('fifo_count>=240','fifo_count>=BW')
  assert (R/'build/sim/refined_arbitration/writer.v').read_text(encoding='utf-8')==writer,'arbitration fixture differs from current writer'
  prefixes=['source_time_and_endpoint','v4_frame_store_and_display','actual_isp_sof_tags','refined_v4_ui_pixels','controls_with_camera_pause','camera_frame_admission','camera_real_i2c','ddr_handshake','bank_actual_commit','final_missing_snapshot','ingress','calibration_calibration_acquisition','model_state_quality','history_full_rgb_after','tracker_identity_adversarial','tracker_quality_and_diagnostics','five_zoom_viewport','rational_overlay_geometry','recovery_budget','arbitration_bw240_recover']
  prefixes += ['tracker_storage_equivalence','failed_bus_wait_peak','shared_hue_math','shared_hue_exhaustive_rtl','footer_late_abort_after','capture_diagnostics_v4','store_cached_id_comparison','refined_v4_frame_store_and_display','controls_repeat_equivalence_100','controls_repeat_equivalence_135']+[f'camera_supervisor_{m}' for m in range(6)]+[f'final_video_drain_{m}' for m in range(3)]
  prefixes += [f'refined_video_{pair}_{z}_{page}_{rot}_f0_n1' for pair in (0,1) for z in range(5) for page in range(4) for rot in (0,1)]
  prefixes += [f'refined_v4_live_{pair}_{rot}' for pair in (0,1) for rot in (0,1)]
  prefixes += [f'refined_video_0_0_0_{rot}_f1_n2' for rot in (0,1)]+[f'refined_video_0_1_0_{rot}_f0_n2' for rot in (0,1)]
  prefixes += [f'sampling_after_{pair}_{case}' for pair,case in ((0,0),(0,1),(1,0),(1,1))]
  prefixes += ['calibration_after_'+n for n in ('blue_metal_reflection','broad_cluster','dark_blue_background','inseparable_background','polluted_frames','purple_dark_bias','purple_neutral_background','yellow_bright_neutral','yellow_dark_bias')]
  prefixes += ['camera_relay_equivalence','camera_relay_production_real_i2c']+[f'camera_relay_production_{m}' for m in range(6)]
  prefixes += ['hue_retime_equivalence']
  prefixes += [f'recovery_mailbox_equivalence_{p}' for p in (0,1,4,9)]
  prefixes += ['capture_history_pipeline_'+name for name in ('stale_context','matching_identity','expired_identity')]
  result['regression']={prefix:evidence(prefix,required_inputs(prefix)) for prefix in prefixes}
  late=result['regression']['footer_late_abort_after']
  for name in ('history_full_rgb_after','capture_diagnostics_v4'):
   assert 'CAPTURE_CANDIDATE_HOLD_PASS' in (R/result['regression'][name]['record']).with_suffix('.log').read_text(encoding='utf-8')
  assert 'V4_UI_CASE_PASS last_pixel_abort' in (R/late['record']).with_suffix('.log').read_text(encoding='utf-8')
  for mode in range(3):
   assert 'FAILED_JOB_PEAK_PASS' in (R/result['regression'][f'final_video_drain_{mode}']['record']).with_suffix('.log').read_text(encoding='utf-8')
   if mode:
    assert 'FAULT_COUNTS_STICKY_PASS' in (R/result['regression'][f'final_video_drain_{mode}']['record']).with_suffix('.log').read_text(encoding='utf-8')
  result['display_combinations']=80;result['live_frames']=20;result['hardware_status']='pending'
 if attempt:
  out=(R/attempt).resolve();assert out.is_relative_to(R/'build')
  s=json.loads((out/'summary.json').read_text(encoding='utf-8'))
  assert s['stage']=='full' and s['exit_code']==0 and s['resource_pass'] and s['timing_pass'] and s['inputs_unchanged'],s
  if s.get('official_strategy'):
   strategy=s['official_strategy'];assert sha(out/'official_strategy_ph1.json')==strategy['sha256']
   assert json.loads((out/'official_strategy_context.json').read_text(encoding='utf-8'))==strategy
   definitions=json.loads((out/'official_strategy_ph1.json').read_text(encoding='utf-8'))
   tcl=(out/'run.tcl').read_text(encoding='utf-8')
   if s.get('checkpoint_provenance'):
    strategy_parent=(R/s['checkpoint_provenance']['parent']).resolve()
    assert strategy_parent.is_relative_to(R/'build')
    tcl+='\n'+(strategy_parent/'run.tcl').read_text(encoding='utf-8')
   for name,definition in strategy['selected'].items():
    assert definitions[name]==definition
    for setting in definition['params']:
     assert f'set_param {setting["step"]} {setting["param"]} {setting["val"]}' in tcl
  before=json.loads((out/'inputs.json').read_text(encoding='utf-8'));after=json.loads((out/'inputs_after.json').read_text(encoding='utf-8'))
  canonical_build_inputs(before)
  assert before==after and all(sha(out/'compiled_source'/n)==v for n,v in before.items())
  assert all(sha(R/n)==v for n,v in before.items()),'current compilation inputs differ from candidate'
  assert (out/'target_color_regions.bit').is_file()
  context=json.loads((out/'source_context.json').read_text(encoding='utf-8'))
  if s.get('failed_checkpoint_provenance'):
   from refined_failed_checkpoint import verify_source
   fp=s['failed_checkpoint_provenance']
   proof,source_inputs,source_context,source_parent,parent=verify_source(R,R/fp['source_attempt'],R/fp['probe'],canonical_build_inputs,checkpoint_report_signature)
   assert proof==fp==context['failed_checkpoint_provenance'] and source_inputs==before
   assert context['compiled_source_commit']==source_context['compiled_source_commit']
   assert s['failed_checkpoint_unchanged'] and sha(out/'failed_normal_route.db')==proof['checkpoint_sha256']
   assert s['recovery_method']=='fresh_process_from_failed_normal_route'
   child_tcl=(out/'run.tcl').read_text(encoding='utf-8')
   assert 'import_db failed_normal_route.db' in child_tcl and f'set_param route effort {s["route_effort"]}' in child_tcl
   assert 'FAILED_CHECKPOINT_CONSTRAINT_ROUNDTRIP_PASS' in (out/'td.log').read_text(encoding='utf-8')
   probe=R/proof['probe']
   for name in ('restored_clocks.txt','restored_exceptions.timing'):
    assert checkpoint_report_signature(out/name,probe,out)==checkpoint_report_signature(probe/name,probe,out),name
   assert 'target_color_regions_routed.db' in s['route_checkpoints']
   for name,value in s['route_checkpoints'].items():
    assert name=='target_color_regions_routed.db' and sha(out/name)==value
  if s.get('checkpoint_provenance'):
   proof=s['checkpoint_provenance'];parent=(R/proof['parent']).resolve();assert parent.is_relative_to(R/'build')
   assert s['checkpoint_unchanged'] and context['placed_checkpoint']==proof
   assert sha(parent/'summary.json')==proof['parent_summary_sha256']
   assert sha(parent/'source_context.json')==proof['parent_context_sha256']
   assert sha(parent/'inputs.json')==proof['parent_inputs_sha256']==sha(out/'inputs.json')
   ps=json.loads((parent/'summary.json').read_text(encoding='utf-8'))
   assert ps['stage']=='place' and ps['exit_code']==0 and ps['resource_pass'] and ps['inputs_unchanged']
   db=proof['checkpoint_name'];assert db=='target_color_regions_placed.db'
   assert sha(parent/db)==sha(out/db)==proof['checkpoint_sha256']==ps['checkpoints'][db]
   assert before==json.loads((parent/'inputs.json').read_text(encoding='utf-8'))==json.loads((parent/'inputs_after.json').read_text(encoding='utf-8'))
   assert all(sha(parent/'compiled_source'/n)==v for n,v in before.items())
   assert context['compiled_source_commit']==json.loads((parent/'source_context.json').read_text(encoding='utf-8'))['compiled_source_commit']
   assert 'REFINED_PLACED_CHECKPOINT_READY' in (parent/'td.log').read_text(encoding='utf-8')
   assert 'CHECKPOINT_CONSTRAINT_ROUNDTRIP_PASS' in (out/'td.log').read_text(encoding='utf-8')
   for name in ('placed_clocks.txt','placed_exceptions.timing'):
    assert checkpoint_report_signature(parent/name,parent,out)==checkpoint_report_signature(out/name,parent,out),name
   if s.get('replaced_strategy') is not None:
    n=s['replaced_strategy'];assert n in range(1,12) and context['replaced_strategy']==n and s['placement_strategy']==n
    child_tcl=(out/'run.tcl').read_text(encoding='utf-8')
    assert f'set_param place pr_strategy {n}\n place\n' in child_tcl
    assert 'REFINED_REPLACEMENT_PLACE_COMPLETED' in (out/'td.log').read_text(encoding='utf-8')
   if s.get('retry_routability'):
    assert context['retry_routability'] and s['route_effort']=='normal'
    child_tcl=(out/'run.tcl').read_text(encoding='utf-8')
    assert 'catch {route} normal_error' in child_tcl and 'set_param route effort routability' in child_tcl
    retried='ROUTE_NORMAL_FAILED_RETRY_ROUTABILITY' in (out/'td.log').read_text(encoding='utf-8')
    assert s['route_retry_performed']==retried
    assert s['final_route_effort']==('routability' if retried else 'normal')
   if s.get('flow_threads') is not None:
    n=s['flow_threads'];assert n in (2,4,8,16,32) and context['flow_threads']==n
    assert f'set_param flow thread {n}\n' in (out/'run.tcl').read_text(encoding='utf-8')
    assert re.search(r'^\s*thread\s*\|\s*'+str(n)+r'\s*\|',(out/'effective_flow.txt').read_text(encoding='utf-8'),re.M)
   for name,value in s.get('route_checkpoints',{}).items():
    assert name in ('failed_normal_route.db','target_color_regions_routed.db') and sha(out/name)==value
  commit=context['compiled_source_commit'];assert re.fullmatch('[0-9a-f]{40}',commit)
  assert context['inputs_sha256']==sha(out/'inputs.json') and context['input_count']==len(before)
  subprocess.run(['git','merge-base','--is-ancestor',commit,'HEAD'],cwd=R,check=True)
  names=list(before);assert all('\n' not in n and '\r' not in n for n in names)
  blob=subprocess.run(['git','cat-file','--batch'],cwd=R,input=('\n'.join(commit+':'+n for n in names)+'\n').encode(),capture_output=True,check=True).stdout
  pos=0
  for name in names:
   end=blob.index(b'\n',pos);header=blob[pos:end];pos=end+1
   assert not header.endswith(b' missing'),name
   size=int(header.split()[-1]);data=blob[pos:pos+size];pos+=size+1
   assert hashlib.sha256(data).hexdigest()==before[name],'compiled input differs from committed bytes: '+name
  timing=(out/'target_color_regions_pr.timing').read_text(encoding='utf-8')
  exceptions=(out/'target_color_regions_exception.timing').read_text(encoding='utf-8')
  result['build']=dict(attempt=out.relative_to(R).as_posix(),summary=s,compiled_source_commit=commit,git_blob_inputs_verified=len(before),bit_sha256=sha(out/'target_color_regions.bit'),frozen_inputs=len(before),sta_coverage_percent=float(re.search(r'STA coverage\s*:\s*([\d.]+)%',timing)[1]),ignored_max_delay_constraints=int(re.search(r'Ignored\s*:\s*(\d+)',exceptions)[1]))
 return result
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--attempt');ap.add_argument('--regression',action='store_true');ap.add_argument('--record');args=ap.parse_args()
 data=audit(args.attempt,args.regression)
 if args.record:
  p=R/args.record;assert not p.exists(),p;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 print('REFINED_AUDIT_PASS',len(data.get('regression',{})),'current-source simulations',data.get('build',{}).get('attempt','no full build requested'))
