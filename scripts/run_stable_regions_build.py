"""Unique, frozen production TD attempts. Existing bit files are never replaced."""
from pathlib import Path
import argparse,datetime,subprocess,os,json,hashlib,zipfile,re
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--stage',choices=['synth','full'],default='synth');p.add_argument('--prefix',choices=['stable_regions','ring_stability'],default='stable_regions');a=p.parse_args()
stamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')
name=f'{a.prefix}_{a.stage}_{stamp}';out=R/'build'/name;out.mkdir(exist_ok=False)
project=R/'td_project/target_color_regions.al'
paths=[project,R/'td_project/target_lock.adc',R/'td_project/target_lock.sdc',R/'rtl/03_tool_detection/target_config.json']
for s in re.findall(r'<File Path="([^"]+)"',project.read_text(encoding='utf-8')):
    q=(project.parent/s).resolve()
    if q.is_file():paths.append(q)
paths += [q for q in (R/'user_source').rglob('*') if q.is_file() and q.suffix.lower() in
          ('.v','.sv','.vhd','.xml','.json','.tcl','.adc','.sdc','.mem','.hex','.dat','.txt') and 'log' not in q.parts]
paths=sorted(set(paths));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest={q.relative_to(R).as_posix():sha(q) for q in paths}
(out/'inputs.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
with zipfile.ZipFile(out/'source_snapshot.zip','w',zipfile.ZIP_DEFLATED) as z:
    for q in paths:z.write(q,q.relative_to(R))
t=(R/'scripts/build_target_color_regions.tcl').read_text(encoding='utf-8')
t=t.replace('set root [file normalize [file join [file dirname [info script]] ..]]',f'set root {{{R.as_posix()}}}')
t=re.sub(r'# PRODUCTION_OUTPUT_BEGIN.*?# PRODUCTION_OUTPUT_END',f'set out {{{out.as_posix()}}}',t,flags=re.S)
if a.stage=='synth':t=t[:t.index('    legalize_phy_inst')]+'''    puts "STABLE_REGIONS_SYNTH_COMPLETED"
} message]} {puts stderr "BUILD_FAILED: $message";puts stderr $::errorInfo;exit 1}
exit
'''
script=out/'run.tcl';script.write_text(t,encoding='utf-8');td=Path('D:/26_software/TangDynasty/bin/td_commands_prompt.exe')
env=os.environ.copy();env['PATH']=str(td.parent)+os.pathsep+env.get('PATH','')
log=R/'reports'/(name+'.log');print('TD_ATTEMPT',out,flush=True)
with log.open('w',encoding='utf-8') as f:result=subprocess.run([str(td),script.as_posix()],cwd=out,env=env,stdout=f,stderr=subprocess.STDOUT)
after={q.relative_to(R).as_posix():sha(q) for q in paths}
(out/'inputs_after.json').write_text(json.dumps(after,indent=2),encoding='utf-8')
print('TD_EXIT',result.returncode,'INPUTS_UNCHANGED',after==manifest,'LOG',log,flush=True)
if result.returncode==0 and after==manifest and a.stage=='full':
    timing=(out/'target_color_regions_phy.ts').read_text(encoding='utf-8')
    area=(out/'target_color_regions_phy.area').read_text(encoding='utf-8')
    slack={tag:float(re.search(tag+r':\s*([-\d.]+)ns',timing)[1]) for tag in ('SWNS','HWNS')}
    resources={tag:int(re.search(r'^#'+tag+r'\s+(\d+)',area,re.M)[1]) for tag in ('slice','lut6','reg','eram','dsp')}
    if min(slack.values())<0 or any(resources[k]>n for k,n in [('slice',21216),('lut6',21216),('reg',42432),('eram',108),('dsp',40)]):
        print('PRODUCTION_BUILD_REJECTED',slack,resources,flush=True);raise SystemExit(3)
    print('PRODUCTION_BUILD_QUALITY_PASS',slack,resources,flush=True)
raise SystemExit(result.returncode if after==manifest else 2)
