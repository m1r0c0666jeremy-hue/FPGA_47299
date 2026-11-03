"""Adopt measured serial snapshot; require fresh112 and full physical acceptance."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys,zipfile
A=Path(__file__).resolve().parent;R=A.parents[1];O=R/'build/stage1_serial_snapshot_20261024_0752';B=O/'adoption_bundle'
sys.path.insert(0,str(R/'scripts'));from stage1_policy import canonical_build_inputs,compiler_paths,check_branch,check_protected,baseline_inputs
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
check_branch(R);assert subprocess.check_output(['powershell','-NoProfile','-Command','@(Get-Process -Name td_commands_prompt,vvp -ErrorAction SilentlyContinue).Count'],text=True).strip()=='0'
assert not subprocess.check_output(['git','-c','safe.directory='+R.as_posix(),'diff','--name-only'],cwd=R).strip(),'Preserve intervening changes'
proof_file=O/'validation_all.json';p=json.loads(proof_file.read_text());assert len(p['checks'])==6;canonical_build_inputs(p['unchanged_formal_inputs'])
assert all(sha(O/n)==h for k in ('candidates','references','individual_producers') for n,h in p[k].items())
assert sha(O/'seal.py')==p['producer_sha256'] and sha(O/'source.json')==p['source_sha256']
full_path=R/p['baseline'];full=json.loads(full_path.read_text());assert sha(full_path)==p['baseline_sha256'] and full['passed']==full['required']==110 and not full['missing']
assert all(sha(R/n)==h for e in full['regression'].values() for g in ('inputs','fixture_inputs','producer_inputs') for n,h in e[g].items())
for e in p['checks'].values():
 assert sha(R/e['record'])==e['record_sha256'] and sha((R/e['record']).with_suffix('.log'))==e['log_sha256'] and sha(R/e['bench'])==e['bench_sha256']
 assert all(sha(R/n)==h for g in ('inputs','fixtures','producers') for n,h in e[g].items())
gate_file=O/'gate_comparison_20261024_085106.json';g=json.loads(gate_file.read_text());base=g['outputs']['baseline'];candidate=g['outputs']['serial_snapshot']
assert base['resources']==dict(slice=3767,lut6=1783,reg=4191,eram=2,dsp=0)
assert candidate['resources']==dict(slice=3646,lut6=1795,reg=3368,eram=2,dsp=0)
assert sha(O/'gate.py')==g['producer_sha256'] and sha(proof_file)==g['validation_sha256']
for output in (base,candidate):
 d=R/output['directory'];assert sha(d/'td.log')==output['log_sha256'];assert sha(d/'isolated_gate.db')==output['checkpoint_sha256'];assert sha(d/'isolated_netlist.v')==output['netlist_sha256']
manifest_path=B/'PROPOSED_NOT_APPLIED.json';m=json.loads(manifest_path.read_text());assert m['expected_required_checks']==112 and m['proof_sha256']==sha(proof_file)
allowed={'rtl/color_regions/stage1_regions.v','rtl/color_regions/stage1_render.v','scripts/test_stage1_render_guards.py','scripts/audit_stage1.py','scripts/test_stage1_snapshot_protocol.py','scripts/test_stage1_snapshot_abort.py','sim/stage1_snapshot_protocol_tb.sv','sim/stage1_snapshot_abort_tb.sv','sim/stage1_snapshot_frozen_regions.v','sim/stage1_snapshot_frozen_render.v'}
assert set(m['files'])==allowed
original={};new={}
for n,e in m['files'].items():
 q=R/n;assert q.resolve().is_relative_to(R);assert sha(B/n)==e['proposed_sha256']
 if e['before_sha256'] is None:assert not q.exists()
 else:assert sha(q)==e['before_sha256'];original[n]=q.read_bytes()
 new[n]=(B/n).read_bytes()
for n in ('stage1_regions.v','stage1_render.v'):assert new['rtl/color_regions/'+n].decode().splitlines()==(O/n).read_text().splitlines()
for n in ('README.md','reports/stage1/validation.md','docs/区域顺序_第一阶段_执行记录.md','scripts/package_stage1.py'):original[n]=(R/n).read_bytes()
backup=A/'before.zip'
with zipfile.ZipFile(backup,'x',zipfile.ZIP_DEFLATED) as z:
 for n,b in original.items():z.writestr(n,b)
for n,b in new.items():
 q=R/n;e=m['files'][n];q.parent.mkdir(parents=True,exist_ok=True)
 if e['before_sha256'] is None:
  with q.open('xb') as f:f.write(b)
 else:assert q.read_bytes()==original[n];q.write_bytes(b)
 assert sha(q)==e['proposed_sha256']
assert {q.relative_to(R).as_posix() for q in compiler_paths(R)}==set(p['unchanged_formal_inputs'])
assert all(sha(R/n)==h for n,h in p['unchanged_formal_inputs'].items() if n not in ('rtl/color_regions/stage1_regions.v','rtl/color_regions/stage1_render.v'))
check_protected();baseline_inputs(R)
r=dict(status='ADOPTED_SERIAL_SNAPSHOT_CURRENT112_AND_FINAL_PHYSICAL_PENDING',time=datetime.datetime.now().astimezone().isoformat(),previous_compiled_source='124c37e21be6584e5e7445e8fc006aa13db58295',previous_software=p['baseline'],previous_software_sha256=p['baseline_sha256'],backup=backup.relative_to(R).as_posix(),backup_sha256=sha(backup),before={n:hashlib.sha256(b).hexdigest() for n,b in original.items()},after_program={n:sha(R/n) for n in new},new_targets=[n for n,e in m['files'].items() if e['before_sha256'] is None],private_validation=proof_file.relative_to(R).as_posix(),private_validation_sha256=sha(proof_file),gate_comparison=gate_file.relative_to(R).as_posix(),gate_comparison_sha256=sha(gate_file),local_baseline=base['resources'],local_candidate=candidate['resources'],local_delta={n:candidate['resources'][n]-base['resources'][n] for n in base['resources']},proposal_manifest=manifest_path.relative_to(R).as_posix(),proposal_manifest_sha256=sha(manifest_path),source_normalization=m['normalization'],scope='Local Slice -121, LUT6 +12, reg -823, ERAM2/DSP0 unchanged; not a whole-device or routing result.40-word snapshot in existing RAM640..679 replaces840 payload FF. Actual pixel pipeline remains1 clock; preparation has72 extra clocks plus bounded old-arithmetic drain (8 observed), original10000-clock deadline retained. Editor completion at most40 extra clocks. Interfaces/all old features/old RGB and FIFO paths unchanged.',verification='Guard only adapts exact22-bit FV/21-bit FD RAM addresses; all original assertions retained. Actual formal capacity generator is unchanged. Two additional actual-RTL overlap/reset and arithmetic recommit checks raise requirement110 to112. All software and14 negative auditor guards must refresh before release; old F0708 is history.')
with (R/'reports/stage1/serial_snapshot_adoption_20261024_0855.json').open('x',encoding='utf-8') as f:json.dump(r,f,indent=2)
print('SERIAL_SNAPSHOT_ADOPTED;10 program/test files; current112 and whole physical pending',flush=True)
