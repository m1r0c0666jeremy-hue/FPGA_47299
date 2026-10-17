"""Frozen, non-overwriting TD builds of the independent refined project."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,re,subprocess,sys,zipfile,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--stage',choices=['synth','place','full'],default='synth')
ap.add_argument('--route-effort',choices=['normal','routability'],default='normal')
ap.add_argument('--strategy',type=int,choices=range(1,12),default=1)
ap.add_argument('--map-mode',choices=['auto','area_prior','logic_level_prior','balance_explore'],default='auto')
ap.add_argument('--pack-effort',choices=['medium','high','low'],default='medium')
ap.add_argument('--infer-fsm',choices=['project','off','auto','one_hot','sequential','manual'],default='project')
ap.add_argument('--map-strategy',type=int,choices=range(1,6))
ap.add_argument('--macro-performance',choices=['auto','dsp_wirelength','dsp_crit_path','ram_wirelength','ram_crit_path','dsp_ram_wirelength','dsp_ram_crit_path','macro_congestion'])
ap.add_argument('--pack-mode',choices=['auto','lower_pin_density','adaptive_pin_density','more_lut_pair'])
ap.add_argument('--place-effort',choices=['medium','high'])
ap.add_argument('--official-syn',choices=['AreaOptimizeMedium','AreaOptimizeHigh'])
ap.add_argument('--official-phy',choices=['CongestionMedium','CongestionHigh','TimingHigh','TimingUltra'])
ap.add_argument('--official-strategy-file',default='D:/26_software/TangDynasty/doc/strategies/official_strategy_ph1.json')
ap.add_argument('--max-fanout',type=int);a=ap.parse_args()
if a.max_fanout is not None:assert 9<=a.max_fanout<=999999
branch=subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip()
assert branch=='release/transparent-ring-stability-20261015'
created_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
subprocess.run(['git','merge-base','--is-ancestor','2f79847f8443fb18f3896a6b88ae9b75c06c9ff8','HEAD'],cwd=R,check=True)
stamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')
out=R/'build'/f'refined_{a.stage}_{stamp}';out.mkdir(exist_ok=False)
official=None;official_commands={step:[] for step in ('rtl','gate','place','route')}
if a.official_syn or a.official_phy:
 strategy_path=Path(a.official_strategy_file);strategy_bytes=strategy_path.read_bytes();strategies=json.loads(strategy_bytes)
 chosen=[name for name in (a.official_syn,a.official_phy) if name]
 selected={name:strategies[name] for name in chosen}
 for strategy in selected.values():
  for setting in strategy['params']:
   step,key,value=setting['step'],setting['param'],str(setting['val'])
   assert step in official_commands and re.fullmatch(r'[A-Za-z0-9_]+',key) and re.fullmatch(r'[A-Za-z0-9_.-]+',value)
   official_commands[step].append(f'    set_param {step} {key} {value}')
   if step=='gate' and key=='map_mode' and '--map-mode' not in sys.argv:a.map_mode=value
 official=dict(source_path=strategy_path.as_posix(),sha256=hashlib.sha256(strategy_bytes).hexdigest(),selected=selected)
 (out/'official_strategy_ph1.json').write_bytes(strategy_bytes)
 (out/'official_strategy_context.json').write_text(json.dumps(official,indent=2),encoding='utf-8')
project=R/'td_project/target_color_regions_refined.al'
paths={project,R/'td_project/target_lock.adc',R/'td_project/target_lock.sdc',R/'rtl/03_tool_detection/target_config.json'}
for s in re.findall(r'<File Path="([^"]+)"',project.read_text(encoding='utf-8')):
 p=(project.parent/s).resolve()
 if p.is_file():paths.add(p)
paths.update(p for p in (R/'user_source').rglob('*') if p.is_file() and 'log' not in p.parts)
paths.update(p for p in (R/'ip/refined_ddr2').rglob('*') if p.is_file())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={p.relative_to(R).as_posix():sha(p) for p in sorted(paths)}
(out/'inputs.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
(out/'source_context.json').write_text(json.dumps(dict(compiled_source_commit=created_head,creation_time=stamp,input_count=len(before),inputs_sha256=sha(out/'inputs.json')),indent=2),encoding='utf-8')
with zipfile.ZipFile(out/'compiled_inputs.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(paths):z.write(p,p.relative_to(R))
frozen=out/'compiled_source';frozen.mkdir()
for p in sorted(paths):
 target=frozen/p.relative_to(R);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())
assert before=={name:sha(frozen/name) for name in before},'source changed while freezing'
t=(R/'scripts/build_target_color_regions.tcl').read_text(encoding='utf-8')
t=t.replace('set root [file normalize [file join [file dirname [info script]] ..]]',f'set root {{{frozen.as_posix()}}}')
t=t.replace('td_project target_color_regions.al','td_project target_color_regions_refined.al')
# TD places a directory lock beside the project. Build a private project with
# absolute source paths instead of touching the user's open/stale project lock.
root=ET.fromstring(project.read_text(encoding='utf-8').replace('&','&amp;').replace('::','__TD_COLON__'))
root.set('Path',out.as_posix())
for node in root.findall('./Source_Files/*/File'):
 original=(project.parent/node.attrib['Path']).resolve()
 node.set('Path',(frozen/original.relative_to(R)).as_posix())
ET.indent(root,space='    ')
frozen_project=out/'target_color_regions_refined.al'
frozen_project.write_text('<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(root,encoding='unicode').replace('&amp;','&').replace('__TD_COLON__','::')+'\n',encoding='utf-8')
t=t.replace('set project [file join $root td_project target_color_regions_refined.al]',f'set project {{{frozen_project.as_posix()}}}')
t=t.replace('    legalize_phy_inst',f'    set_param place pr_strategy {a.strategy}\n    set_param route effort {a.route_effort}\n    legalize_phy_inst')
t=t.replace('    optimize_gate -packarea',f'    set_param gate map_mode {a.map_mode}\n    set_param gate pack_effort {a.pack_effort}\n    optimize_gate -packarea')
if a.infer_fsm!='project':t=t.replace('    optimize_rtl',f'    set_param rtl infer_fsm {a.infer_fsm}\n    optimize_rtl')
if a.map_strategy is not None:t=t.replace('    optimize_gate -packarea',f'    set_param gate map_strategy {a.map_strategy}\n    optimize_gate -packarea')
if a.macro_performance is not None:t=t.replace('    legalize_phy_inst',f'    set_param place macro_performance {a.macro_performance}\n    legalize_phy_inst')
if a.pack_mode is not None:t=t.replace('    legalize_phy_inst',f'    set_param place pack_mode {a.pack_mode}\n    legalize_phy_inst')
if a.place_effort is not None:t=t.replace('    legalize_phy_inst',f'    set_param place effort {a.place_effort}\n    legalize_phy_inst')
if a.max_fanout is not None:t=t.replace('    legalize_phy_inst',f'    set_param place max_fanout {a.max_fanout}\n    legalize_phy_inst')
# Apply the installed vendor strategy before the explicit command-line options.
# None of these tool settings modifies clocks, ADC or SDC exceptions.
if official:
 rtl_lines='\n'.join(official_commands['rtl'])
 gate_lines='\n'.join(official_commands['gate'])
 phy_lines='\n'.join(official_commands['place']+official_commands['route'])
 if rtl_lines:t=t.replace('    optimize_rtl',rtl_lines+'\n    optimize_rtl')
 # Insert gate presets before the explicit map-mode block already generated.
 if gate_lines:t=t.replace('    set_param gate map_mode',gate_lines+'\n    set_param gate map_mode',1)
 if phy_lines:t=t.replace('    set_param place pr_strategy',phy_lines+'\n    set_param place pr_strategy',1)
t=t.replace('    route\n','    report_area -io_info -file target_color_regions_place.area\n    route\n')
t=re.sub(r'# PRODUCTION_OUTPUT_BEGIN.*?# PRODUCTION_OUTPUT_END',f'set out {{{out.as_posix()}}}',t,flags=re.S)
if a.stage=='synth':t=t[:t.index('    legalize_phy_inst')]+'''    report_timing_summary -file target_color_regions_gate.timing
    puts "REFINED_SYNTH_COMPLETED"
} message]} {puts stderr "BUILD_FAILED: $message";puts stderr $::errorInfo;exit 1}
exit
'''
elif a.stage=='place':t=t[:t.index('    route')]+'''    report_area -io_info -file target_color_regions_phy.area
    puts "REFINED_PLACE_COMPLETED"
} message]} {puts stderr "BUILD_FAILED: $message";puts stderr $::errorInfo;exit 1}
exit
'''
script=out/'run.tcl';script.write_text(t,encoding='utf-8')
td=Path('D:/26_software/TangDynasty/bin/td_commands_prompt.exe')
env=os.environ.copy();env['PATH']=str(td.parent)+os.pathsep+env.get('PATH','')
log=out/'td.log';print('REFINED_TD_ATTEMPT',out,flush=True)
with log.open('w',encoding='utf-8') as f:p=subprocess.run([str(td),script.as_posix()],cwd=out,env=env,stdout=f,stderr=subprocess.STDOUT)
after={name:sha(frozen/name) for name in before}
(out/'inputs_after.json').write_text(json.dumps(after,indent=2),encoding='utf-8')
summary=dict(stage=a.stage,head=created_head,head_after=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),route_effort=a.route_effort,placement_strategy=a.strategy,map_mode=a.map_mode,pack_effort=a.pack_effort,infer_fsm=a.infer_fsm,map_strategy=a.map_strategy,macro_performance=a.macro_performance,pack_mode=a.pack_mode,place_effort=a.place_effort,max_fanout=a.max_fanout,exit_code=p.returncode,inputs_unchanged=before==after,working_tree_matches=all((R/name).is_file() and sha(R/name)==value for name,value in before.items()))
summary['official_strategy']=official
if p.returncode==0:
 from refined_build_report import assess
 summary.update(assess(out,a.stage))
(out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print('REFINED_TD_RESULT',json.dumps(summary),flush=True)
if p.returncode or before!=after or not summary.get('resource_pass',False) or not summary.get('timing_pass',a.stage!='full'):raise SystemExit(p.returncode or 3)
