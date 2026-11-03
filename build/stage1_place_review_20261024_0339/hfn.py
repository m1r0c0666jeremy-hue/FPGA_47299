"""Report a verified checkpoint's inherited parameters; no circuit build.
Run only after current TD ends. Original DB/source are never modified.
"""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys
O=Path(__file__).resolve().parent;R=O.parents[1];sys.path.insert(0,str(R/'scripts'))
from stage1_policy import canonical_build_inputs,check_protected
assert subprocess.check_output(['powershell','-NoProfile','-Command','@(Get-Process -Name td_commands_prompt -ErrorAction SilentlyContinue).Count'],text=True).strip()=='0','Do not run a second TD'
parent=R/'build/stage1_place_20261024_032009';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();summary=json.loads((parent/'summary.json').read_text());inputs=json.loads((parent/'inputs.json').read_text());canonical_build_inputs(inputs)
db=parent/'target_color_regions_placed.db';expected=summary['checkpoints'][db.name];assert sha(db)==expected and summary['exit_code']==0 and summary['inputs_unchanged']
assert all(sha(parent/'compiled_source'/n)==h for n,h in inputs.items())
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');out=O/('inspection_'+stamp);out.mkdir(exist_ok=False)
t="""if {[catch {
import_device ph1_35p.db -package PH1P35MDG324 -speed 3
cd {OUT}
import_db {DB}
report_param -detail -stage place -file inherited_place.txt
report_param -detail -stage route -file inherited_route.txt
report_param -detail -stage flow -file inherited_flow.txt

if {[catch {report_hfn place} e]} {puts "HFN_REPORT_UNAVAILABLE: $e"}
puts "CHECKPOINT_STRUCTURE_REPORT_ONLY_DONE"
} message]} {puts stderr "PARAM_REPORT_FAILED: $message";puts stderr $::errorInfo;exit 1}
exit
""".replace('OUT',out.as_posix()).replace('DB',db.as_posix())
script=out/'report.tcl';script.write_bytes(t.encode());td=Path('D:/26_software/TangDynasty/bin/td_commands_prompt.exe');env=os.environ.copy();env['PATH']=str(td.parent)+os.pathsep+env.get('PATH','')
with (out/'td.log').open('x',encoding='utf8') as f:p=subprocess.run([td,script.as_posix()],cwd=out,env=env,stdout=f,stderr=subprocess.STDOUT)
assert p.returncode==0 and 'CHECKPOINT_STRUCTURE_REPORT_ONLY_DONE' in (out/'td.log').read_text()
assert sha(db)==expected;canonical_build_inputs(inputs);check_protected()
reports={f.name:sha(f) for f in out.glob('inherited_*.txt')};assert len(reports)==3

result=dict(status='CHECKPOINT_PARAMETER_REPORT_ONLY_NO_BUILD',parent=parent.relative_to(R).as_posix(),checkpoint_sha256=expected,reports=reports,log_sha256=sha(out/'td.log'),producer_sha256=sha(Path(__file__)),source_inputs_unchanged=True)
with (out/'review.json').open('x',encoding='utf8') as f:json.dump(result,f,indent=2)
print('PARAMETER_INSPECTION_COMPLETE',out,flush=True)
for f in out.glob('inherited_*.txt'):
 for line in f.read_text().splitlines():
  if any(k in line for k in ('max_fanout','pr_strategy','pack_mode','target_density','congestion_recovery','post_route_opt','fix_hold','timing','effort','thread')):print(f.name,line)
