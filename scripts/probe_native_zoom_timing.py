"""Read-only timing diagnosis from a successful placed native checkpoint."""
import argparse,datetime,hashlib,json,os,subprocess
from pathlib import Path
from native_zoom_policy import R,sha,canonical_build_inputs

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--parent',required=True);a=ap.parse_args()
 parent=(R/a.parent).resolve();assert parent.is_relative_to(R/'build')
 summary=json.loads((parent/'summary.json').read_text(encoding='utf-8'))
 inputs=json.loads((parent/'inputs.json').read_text(encoding='utf-8'));canonical_build_inputs(inputs)
 assert summary['exit_code']==0 and summary['resource_pass'] and summary['inputs_unchanged']
 checkpoint=parent/'target_color_regions_placed.db';assert sha(checkpoint)==summary['checkpoints'][checkpoint.name]
 out=R/'build'/('native_zoom_timing_probe_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));out.mkdir(exist_ok=False)
 t=f'''cd {{{out.as_posix()}}}
if {{[catch {{
 import_device ph1_35p.db -package PH1P35MDG324 -speed 3
 import_db {{{checkpoint.as_posix()}}}
 update_timing -mode manhattan
 report_timing_summary -file placed_diagnostic.timing
 report_timing_status -file placed_diagnostic.ts
 puts "NATIVE_TIMING_PROBE_COMPLETE"
}} message]}} {{puts stderr "PROBE_FAILED: $message";exit 1}}
exit
'''
 (out/'run.tcl').write_text(t,encoding='utf-8')
 td=Path('D:/26_software/TangDynasty/bin/td_commands_prompt.exe');env=os.environ.copy();env['PATH']=str(td.parent)+os.pathsep+env.get('PATH','')
 print('NATIVE_TIMING_PROBE',out,flush=True)
 with (out/'td.log').open('w',encoding='utf-8') as log:code=subprocess.run([str(td),str(out/'run.tcl')],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
 assert sha(checkpoint)==summary['checkpoints'][checkpoint.name] and all(sha(R/n)==h for n,h in inputs.items())
 (out/'receipt.json').write_text(json.dumps({'exit_code':code,'parent':a.parent,'checkpoint_sha256':sha(checkpoint),'scope':'Manhattan estimate for diagnosis only; does not replace final routed timing'},indent=2),encoding='utf-8')
 print('NATIVE_TIMING_PROBE_RESULT',code,(out/'placed_diagnostic.ts').read_text(encoding='utf-8') if code==0 else (out/'td.log').read_text(encoding='utf-8'))
 raise SystemExit(code)
