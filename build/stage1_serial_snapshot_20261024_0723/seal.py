"""Seal only all five private proofs; no adoption or CAD."""
from pathlib import Path
import hashlib,json,sys
O=Path(__file__).resolve().parent;R=O.parents[1];sys.path.insert(0,str(R/'scripts'))
from stage1_policy import canonical_build_inputs
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=json.loads((O/'source.json').read_text());canonical_build_inputs(s['unchanged_formal_inputs'])
a=json.loads((O/'selected_validation_v3.json').read_text());assert len(a['checks'])==4 and a['candidates']==s['candidates'];assert sha(O/'probe_v3.py')==a['producer_sha256']
b=json.loads((O/'overlap_validation_v2.json').read_text());assert sha(O/'timing_proof_v2.py')==b['producer_sha256']
full=R/s['baseline'];f=json.loads(full.read_text());assert sha(full)==s['baseline_sha256'] and f['passed']==f['required']==110 and not f['missing']
assert all(sha(R/n)==h for e in f['regression'].values() for g in ('inputs','fixture_inputs','producer_inputs') for n,h in e[g].items())
checks=a['checks'];d=json.loads((R/b['record']).read_text());assert d['exit_code']==0
checks['serial_snapshot_overlap']=dict(record=b['record'],record_sha256=b['record_sha256'],log_sha256=b['log_sha256'],inputs={n.replace('\\','/'):h for n,h in d['inputs'].items()},bench=b['bench'],bench_sha256=b['bench_sha256'],fixtures={b['fixture']:b['fixture_sha256'],'rtl/color_regions/stage1_osd.v':b['frame_coordinate_source_sha256']},producers={(O/'timing_proof_v2.py').relative_to(R).as_posix():sha(O/'timing_proof_v2.py'),'scripts/refined_testlib.py':sha(R/'scripts/refined_testlib.py')},private_fixture_adjustment='New dedicated real-command test. Same candidate data feeds frozen F renderer. Actual frame-start x/y reset modeled from stage1_osd.v; all7 deadline/payload/transaction/reset cases retained. Failed initial fixture that kept y623 across frames is preserved.')
markers={'stage1_regions':'STAGE1_REGIONS_CAPACITY_PASS areas=4 points=32','stage1_render_guards':'STAGE1_RENDER_GUARDS_PASS','stage1_render_14_624':'STAGE1_RENDER_PASS cases=14 pixels=11182080','stage1_overlay':'STAGE1_OVERLAY_PASS cases=8 pixels=6389760','serial_snapshot_overlap':'SERIAL_SNAPSHOT_OVERLAP_PASS cases=7 pixels=1597440'}
for label,e in checks.items():
 assert sha(R/e['record'])==e['record_sha256'] and sha((R/e['record']).with_suffix('.log'))==e['log_sha256'];assert sha(R/e['bench'])==e['bench_sha256']
 assert all(sha(R/n)==h for g in ('inputs','fixtures','producers') for n,h in e[g].items());assert markers[label] in (R/e['record']).with_suffix('.log').read_text()
assert all(sha(O/n)==h for n,h in s['candidates'].items())
result=dict(status='PRIVATE_FIVE_PROOFS_PASSED_NOT_ADOPTED_NO_RESOURCE_CREDIT',checks=checks,candidates=s['candidates'],references=s['references'],unchanged_formal_inputs=s['unchanged_formal_inputs'],baseline=s['baseline'],baseline_sha256=s['baseline_sha256'],producer_sha256=sha(Path(__file__)),source_sha256=sha(O/'source.json'),individual_producers={'probe_v3.py':sha(O/'probe_v3.py'),'timing_proof_v2.py':sha(O/'timing_proof_v2.py')},preparation_latency_change='40 copy clocks plus1 fetch per32 edge preparations=72 extra initial clocks. Pixel pipeline remains1 clock. Controller deferral at most40 clocks after frame commit;41 blocked edges including commit proven. Original10000-clock readiness deadlines retained.',comparison_scope='Every original real-editor/capacity/controller-cycle assertion retained. Extra F/G display comparison is active-video only because blanking preparation duration deliberately differs. Full14 edge frames/8RGB and7 additional overlap/reset cases pass. No formal or physical credit.')
with (O/'validation_all.json').open('x',encoding='utf-8') as h:json.dump(result,h,indent=2)
print('PRIVATE_G_FIVE_PROOFS_SEALED_NO_ADOPTION',flush=True)
