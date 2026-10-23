"""Adopt proven shared region-state RAM; preserve controls, cycles and all assertions."""
from pathlib import Path
import datetime,hashlib,json,re,subprocess,sys,zipfile
A=Path(__file__).resolve().parent;R=A.parents[1];O=R/'build/stage1_shared_region_ram_20261024_0517'
sys.path.insert(0,str(R/'scripts'))
from stage1_policy import canonical_build_inputs,check_branch,check_protected
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
check_branch(R)
assert subprocess.check_output(['powershell','-NoProfile','-Command','@(Get-Process -Name td_commands_prompt,vvp -ErrorAction SilentlyContinue).Count'],text=True).strip()=='0'
assert not subprocess.check_output(['git','-c','safe.directory='+R.as_posix(),'diff','--name-only'],cwd=R).strip(),'Preserve any intervening changes'
proof=O/'validation.json';d=json.loads(proof.read_text());assert len(d['checks'])==4
canonical_build_inputs(d['unchanged_formal_inputs'])
full_path=R/'reports/stage1/software_current_20261024_0532.json';full=json.loads(full_path.read_text());assert full['passed']==full['required']==110 and not full['missing']
assert all(sha(R/n)==h for e in full['regression'].values() for group in ('inputs','fixture_inputs','producer_inputs') for n,h in e[group].items())
comparison=next(O.glob('gate_comparison_*.json'));g=json.loads(comparison.read_text());base=g['outputs']['baseline'];candidate=g['outputs']['shared_region_ram']
assert candidate['resources']==dict(slice=3767,lut6=1783,reg=4191,eram=2,dsp=0)
assert base['resources']==dict(slice=3756,lut6=1766,reg=4191,eram=3,dsp=0)
assert sha(O/'gate.py')==g['producer_sha256'] and sha(proof)==g['validation_sha256']
for output in (base,candidate):
 p=R/output['directory'];assert sha(p/'td.log')==output['log_sha256'];assert sha(p/'isolated_gate.db')==output['checkpoint_sha256'];assert sha(p/'isolated_netlist.v')==output['netlist_sha256']
for e in d['checks'].values():
 assert sha(R/e['record'])==e['record_sha256'] and sha((R/e['record']).with_suffix('.log'))==e['log_sha256']
 assert all(sha(R/n)==h for group in ('inputs','fixtures','producers') for n,h in e[group].items())
renderer=R/'rtl/color_regions/stage1_render.v';test=R/'scripts/test_stage1_render.py';old={renderer:renderer.read_bytes(),test:test.read_bytes()}
assert sha(renderer)==json.loads((O/'source.json').read_text())['baseline_sha256']
assert (O/'stage1_render_reference.v').read_bytes().replace(b'module stage1_render_reference #',b'module stage1_render #',1)==old[renderer]
assert b'\r' not in old[renderer] and b'\r' not in (O/'stage1_render.v').read_bytes()
newtest,changed=re.subn(rb'dut\.edge_mem\[([^\]]+)\]',lambda m:b'dut.state_line_mem[768+('+m[1]+b')][15:0]',old[test]);assert changed==8
assert newtest.replace(b'dut.state_line_mem[768+(',b'dut.state_line_mem[768+(')!=old[test]
backup=A/'before.zip'
with zipfile.ZipFile(backup,'x',zipfile.ZIP_DEFLATED) as z:
 for p,b in old.items():z.writestr(p.relative_to(R).as_posix(),b)
for p,b in old.items():assert p.read_bytes()==b
renderer.write_bytes((O/'stage1_render.v').read_bytes());test.write_bytes(newtest)
assert sha(renderer)==d['candidate_sha256']
assert all(sha(R/n)==h for n,h in d['unchanged_formal_inputs'].items() if n!='rtl/color_regions/stage1_render.v')
check_protected()
record=dict(status='ADOPTED_SHARED_REGION_RAM_FRESH_FORMAL_SOFTWARE_AND_PHYSICAL_PENDING',time=datetime.datetime.now().astimezone().isoformat(),previous_compiled_source='69a8e6993424ea822e42b55380f9eb4ef67de7b8',previous_software=full_path.relative_to(R).as_posix(),before={p.relative_to(R).as_posix():hashlib.sha256(b).hexdigest() for p,b in old.items()},after={p.relative_to(R).as_posix():sha(p) for p in old},backup=backup.relative_to(R).as_posix(),backup_sha256=sha(backup),private_validation=proof.relative_to(R).as_posix(),private_validation_sha256=sha(proof),gate_comparison=comparison.relative_to(R).as_posix(),gate_comparison_sha256=sha(comparison),local_baseline=base['resources'],local_candidate=candidate['resources'],local_delta={n:candidate['resources'][n]-base['resources'][n] for n in base['resources']},source_normalization='None; formal renderer byte-identical to private LF candidate',scope='One 1024x32 dual-port RAM replaces 256x16 edge state and 640x32 line masks; pixel read latency, control FSM, interfaces and cycles unchanged. Only new region renderer storage changed; old RGB buffers/FIFOs untouched. Local ERAM -1, Slice +11, LUT6 +17; registers/DSP unchanged. No whole-device/routing credit yet.',fixture_change='Exactly eight failure-only EDGE diagnostic references map edge_mem[k] to state_line_mem[768+k][15:0]. No assertions, vector generation or pixel oracles changed. Original producer bytes preserved in before.zip; all fresh formal evidence must use the new producer.')
with (R/'reports/stage1/shared_region_ram_adoption_20261024_0624.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2)
print('SHARED_REGION_RAM_ADOPTION_DONE: exact private renderer; 8 diagnostic references only')
