"""Frozen, non-overwriting TD builds of the independent refined project."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,re,subprocess,zipfile,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--stage',choices=['synth','place','full'],default='synth');a=ap.parse_args()
branch=subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip()
assert branch=='release/transparent-ring-stability-20261015'
subprocess.run(['git','merge-base','--is-ancestor','2f79847f8443fb18f3896a6b88ae9b75c06c9ff8','HEAD'],cwd=R,check=True)
stamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')
out=R/'build'/f'refined_{a.stage}_{stamp}';out.mkdir(exist_ok=False)
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
t=re.sub(r'# PRODUCTION_OUTPUT_BEGIN.*?# PRODUCTION_OUTPUT_END',f'set out {{{out.as_posix()}}}',t,flags=re.S)
if a.stage=='synth':t=t[:t.index('    legalize_phy_inst')]+'''    puts "REFINED_SYNTH_COMPLETED"
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
summary=dict(stage=a.stage,head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),exit_code=p.returncode,inputs_unchanged=before==after,working_tree_matches=all((R/name).is_file() and sha(R/name)==value for name,value in before.items()))
if p.returncode==0:
 from refined_build_report import assess
 summary.update(assess(out,a.stage))
(out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print('REFINED_TD_RESULT',json.dumps(summary),flush=True)
if p.returncode or before!=after or not summary.get('resource_pass',False) or not summary.get('timing_pass',a.stage!='full'):raise SystemExit(p.returncode or 3)
