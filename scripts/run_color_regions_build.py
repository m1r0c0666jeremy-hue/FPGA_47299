"""A fresh, archived TD attempt per invocation; never overwrite an existing bit."""
from pathlib import Path
import argparse,subprocess,os,json,hashlib,zipfile,datetime,re
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--stage',choices=['synth','full'],default='synth');a=p.parse_args()
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');name='color_regions_'+a.stage+'_'+stamp
out=R/'build'/name;out.mkdir(parents=True,exist_ok=False)
# Preserve all functional inputs plus the unchanged original project dependencies.
paths=list((R/'rtl/color_regions').glob('*.v'))+[R/'td_project/target_color_regions.al',R/'td_project/target_lock.adc',R/'td_project/target_lock.sdc',R/'rtl/03_tool_detection/target_config.json']
for s in re.findall(r'<File Path="([^"]+)"',(R/'td_project/target_color_regions.al').read_text(encoding='utf-8')):
 q=(R/'td_project'/s).resolve()
 if q.is_file():paths.append(q)
# IP descriptors bring in subsidiary RTL/initialisation files not enumerated by
# the project XML. Freeze the vendor source tree, not just descriptor filenames.
paths += [q for q in (R/'user_source').rglob('*') if q.is_file() and
          q.suffix.lower() in ('.v','.sv','.vhd','.xml','.json','.tcl','.adc','.sdc','.mem','.hex','.dat','.txt') and 'log' not in q.parts]
paths += [R/'user_source/hdl_source/ph1p35_ddr/ddr2/src/adc/ddr2.adc',R/'user_source/hdl_source/ph1p35_ddr/ddr2/src/sdc/ddr2.sdc',R/'user_source/ip_source/w128_d512_fifo/w128_d512_fifo.tcl']
paths=sorted(set(paths));manifest={str(q.relative_to(R)).replace('\\','/'):hashlib.sha256(q.read_bytes()).hexdigest() for q in paths}
(out/'inputs.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
with zipfile.ZipFile(out/'source_snapshot.zip','w',zipfile.ZIP_DEFLATED) as z:
 for q in paths:z.write(q,q.relative_to(R))
t=(R/'scripts/build_target_color_regions.tcl').read_text(encoding='utf-8')
t=t.replace('set root [file normalize [file join [file dirname [info script]] ..]]',f'set root {{{R.as_posix()}}}')
t=t.replace('set out [file join $root build target_color_regions]',f'set out {{{out.as_posix()}}}')
if a.stage=='synth':t=t[:t.index('    legalize_phy_inst')]+'''    puts "COLOR_REGIONS_SYNTH_COMPLETED"
} message]} {puts stderr "BUILD_FAILED: $message";puts stderr $::errorInfo;exit 1}
exit
'''
script=out/'run.tcl';script.write_text(t,encoding='utf-8')
td=Path('D:/26_software/TangDynasty/bin/td_commands_prompt.exe')
env=os.environ.copy();env['PATH']=str(td.parent)+os.pathsep+env.get('PATH','')
log=R/'reports'/(name+'.log');print('TD_ATTEMPT',out,flush=True)
with log.open('w',encoding='utf-8') as f:
 result=subprocess.run([str(td),script.as_posix()],cwd=out,env=env,stdout=f,stderr=subprocess.STDOUT)
print('TD_EXIT',result.returncode,'LOG',log,flush=True)
raise SystemExit(result.returncode)
