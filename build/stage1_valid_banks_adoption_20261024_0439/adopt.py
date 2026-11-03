"""Adopt the measured five-bank snapshot; no guard or control changes."""
from pathlib import Path
import datetime,hashlib,json,sys,zipfile
A=Path(__file__).resolve().parent;R=A.parents[1];O=R/'build/stage1_snapshot_valid_banks_20261024_0356'
sys.path.insert(0,str(R/'scripts'))
from stage1_policy import canonical_build_inputs,check_branch,check_protected
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
check_branch(R)
proof=O/'validation.json';d=json.loads(proof.read_text());assert len(d['checks'])==4
canonical_build_inputs(d['unchanged_formal_inputs'])
full_path=R/'reports/stage1/software_current_20261024_0406.json';full=json.loads(full_path.read_text())
assert full['passed']==full['required']==110 and not full['missing']
assert all(sha(R/n)==h for e in full['regression'].values() for group in ('inputs','fixture_inputs','producer_inputs') for n,h in e[group].items())
comparison=next(O.glob('gate_comparison_*.json'));g=json.loads(comparison.read_text())
base=g['outputs']['baseline'];candidate=g['outputs']['valid_banks']
assert candidate['resources']==dict(slice=3756,lut6=1766,reg=4191,eram=3,dsp=0)
assert base['resources']==dict(slice=3805,lut6=1756,reg=4191,eram=3,dsp=0)
assert sha(O/'gate.py')==g['producer_sha256'] and sha(proof)==g['validation_sha256']
for output in (base,candidate):
    p=R/output['directory']
    assert sha(p/'td.log')==output['log_sha256']
    assert sha(p/'isolated_gate.db')==output['checkpoint_sha256']
    assert sha(p/'isolated_netlist.v')==output['netlist_sha256']
for e in d['checks'].values():
    assert sha(R/e['record'])==e['record_sha256']
    assert sha((R/e['record']).with_suffix('.log'))==e['log_sha256']
    assert all(sha(R/n)==h for group in ('inputs','fixtures','producers') for n,h in e[group].items())
renderer=R/'rtl/color_regions/stage1_render.v';old=renderer.read_bytes()
assert sha(renderer)==json.loads((O/'source.json').read_text())['baseline_sha256']
assert (O/'stage1_render_reference.v').read_bytes().replace(b'module stage1_render_reference #',b'module stage1_render #',1)==old
assert b'\r' not in old and b'\r' not in (O/'stage1_render.v').read_bytes()
before=sha(renderer);backup=A/'before.zip';assert not backup.exists()
with zipfile.ZipFile(backup,'x',zipfile.ZIP_DEFLATED) as z:z.writestr(renderer.relative_to(R).as_posix(),old)
renderer.write_bytes((O/'stage1_render.v').read_bytes())
assert sha(renderer)==d['candidate_sha256']
assert all(sha(R/n)==h for n,h in d['unchanged_formal_inputs'].items() if n!='rtl/color_regions/stage1_render.v')
check_protected()
record=dict(status='ADOPTED_VALID_BANKS_FRESH_FORMAL_SOFTWARE_AND_PHYSICAL_PENDING',time=datetime.datetime.now().astimezone().isoformat(),previous_compiled_source='d61da977b7cfff8f8e09dca8fd623e1ccd5ad0fa',previous_software=full_path.relative_to(R).as_posix(),before={renderer.relative_to(R).as_posix():before},after={renderer.relative_to(R).as_posix():sha(renderer)},backup=backup.relative_to(R).as_posix(),backup_sha256=sha(backup),private_validation=proof.relative_to(R).as_posix(),private_validation_sha256=sha(proof),gate_comparison=comparison.relative_to(R).as_posix(),gate_comparison_sha256=sha(comparison),local_baseline=base['resources'],local_candidate=candidate['resources'],local_delta={n:candidate['resources'][n]-base['resources'][n] for n in base['resources']},source_normalization='None; formal renderer byte-identical to private LF candidate',scope='Five bank payload enables replace forty per-vertex enables. All controls/interfaces/cycles unchanged. Local Slice -49, LUT6 +10, registers/ERAM/DSP unchanged. No whole-device or routing credit yet.',guard_change='None; original current guard and every pixel oracle unchanged.')
with (R/'reports/stage1/valid_banks_adoption_20261024_0439.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2)
print('VALID_BANKS_ADOPTION_DONE: exact private bytes; only renderer compiler input changed',flush=True)
