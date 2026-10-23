"""Adopt only the proven renderer, preserving formal LF and all guard assertions."""
from pathlib import Path
import datetime,hashlib,json,sys,zipfile
A=Path(__file__).resolve().parent;R=A.parents[1];O=R/'build/stage1_snapshot_valid_lanes_20261024_0219'
sys.path.insert(0,str(R/'scripts'))
from stage1_policy import canonical_build_inputs,check_branch,check_protected
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
check_branch(R)
proof=O/'validation.json';d=json.loads(proof.read_text());assert len(d['checks'])==4
canonical_build_inputs(d['unchanged_formal_inputs'])
comparison=next(O.glob('gate_comparison_*.json'));g=json.loads(comparison.read_text())
base=g['outputs']['baseline'];candidate=g['outputs']['valid_lanes']
assert candidate['resources']==dict(slice=3805,lut6=1756,reg=4191,eram=3,dsp=0)
assert base['resources']==dict(slice=3796,lut6=1767,reg=4212,eram=3,dsp=0)
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
renderer=R/'rtl/color_regions/stage1_render.v';guard=R/'scripts/test_stage1_render_guards.py'
old=renderer.read_bytes();gb=guard.read_bytes()
assert sha(renderer)==json.loads((O/'source.json').read_text())['baseline_sha256']
assert (O/'stage1_render_reference.v').read_text().replace('module stage1_render_reference #','module stage1_render #',1)==renderer.read_text()
assert gb.count(b"16'h0003")==1 and gb.count(b'stage1_render #(.SPLIT_DRAFT(1)) dut(')==1
assert b'\r' not in old and b'\r' not in gb
before={p.relative_to(R).as_posix():sha(p) for p in (renderer,guard)}
backup=A/'before.zip';assert not backup.exists()
report=R/'reports/stage1/valid_lanes_adoption_20261024_0316.json';assert not report.exists()
with zipfile.ZipFile(backup,'x',zipfile.ZIP_DEFLATED) as z:
    z.writestr(renderer.relative_to(R).as_posix(),old)
    z.writestr(guard.relative_to(R).as_posix(),gb)
candidate_bytes=(O/'stage1_render.v').read_bytes()
assert sha(O/'stage1_render.v')==d['candidate_sha256']
new_bytes=candidate_bytes.replace(b'\r\n',b'\n')
comment=b'// B vertex inspected below is valid; unused snapshot payload is unspecified.\n'
new_guard=gb.replace(b"16'h0003",b"16'h0033",1).replace(b'stage1_render #(.SPLIT_DRAFT(1)) dut(',comment+b'stage1_render #(.SPLIT_DRAFT(1)) dut(',1)
renderer.write_bytes(new_bytes);guard.write_bytes(new_guard)
assert renderer.read_text()==(O/'stage1_render.v').read_text()
assert all(sha(R/n)==h for n,h in d['unchanged_formal_inputs'].items() if n!='rtl/color_regions/stage1_render.v')
check_protected()
record=dict(status='ADOPTED_VALID_LANES_FRESH_FORMAL_SOFTWARE_AND_PHYSICAL_PENDING',time=datetime.datetime.now().astimezone().isoformat(),previous_compiled_source='6164d3d31a52840f1ddfe2986c5946e8636adb43',previous_software='reports/stage1/software_current_20261024_0131.json',before=before,after={p.relative_to(R).as_posix():sha(p) for p in (renderer,guard)},backup=backup.relative_to(R).as_posix(),backup_sha256=sha(backup),private_validation=proof.relative_to(R).as_posix(),private_validation_sha256=sha(proof),gate_comparison=comparison.relative_to(R).as_posix(),gate_comparison_sha256=sha(comparison),local_baseline=base['resources'],local_candidate=candidate['resources'],local_delta={n:candidate['resources'][n]-base['resources'][n] for n in base['resources']},local_commit_fanout_before=934,local_commit_fanout_after=105,private_candidate_sha256=d['candidate_sha256'],formal_candidate_sha256=sha(renderer),source_normalization='Only CRLF -> original formal LF; decoded candidate text identical',scope='Only localized valid payload enables; all controls/interfaces/cycles unchanged. Added 9 local Slice, reduced 11 LUT6 and 21 registers. No whole-device resource or congestion result yet.',guard_change='Declare B snapshot vertex valid (counts0003->0033), retain every assertion; no expected-pixel oracle edited.')
with report.open('x',encoding='utf-8') as f:json.dump(record,f,indent=2)
for suffix,reason in (('0313','Compared formal original hash to renamed reference hash'),('0314','Compared raw reference bytes without accounting for CRLF normalization')):
    path=R/('build/stage1_valid_lanes_adoption_20261024_'+suffix)/'preflight_failure.json'
    with path.open('x',encoding='utf-8') as f:json.dump(dict(status='NO_FORMAL_WRITES_BEFORE_PREFLIGHT_STOP',reason=reason,original_files=before,correct_adoption=report.relative_to(R).as_posix()),f,indent=2)
print('ADOPTION_DONE: exact candidate text; LF preserved; only renderer compiler input changed',flush=True)
