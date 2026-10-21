"""Reject forged passing summaries, negative physical slack, and stale RTL evidence."""
from pathlib import Path
import datetime,json
from audit_stage1 import R,build_audit,evidence,sha

def main():
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    root=R/'build'/('stage1_release_guards_'+stamp);root.mkdir(exist_ok=False)
    outcomes={}
    for label,slices,slack in [('over_capacity',21217,0.1),('negative_setup',20000,-0.001),('negative_hold',20000,0.1)]:
        p=root/label;p.mkdir()
        resources=dict(slice=slices,lut6=19000,reg=24000,eram=98,dsp=40)
        (p/'target_color_regions_phy.area').write_text(''.join(f'#{n} {v}\n' for n,v in resources.items()))
        (p/'target_color_regions_phy.ts').write_text(f'SWNS: {slack}ns\nHWNS: {"-0.001" if label=="negative_hold" else "0.020"}ns\n')
        # Deliberately dishonest flags: the independent physical parser must win.
        (p/'summary.json').write_text(json.dumps(dict(stage='full',exit_code=0,inputs_unchanged=True,resource_pass=True,timing_pass=True,
                                                     resources=resources,slack_ns=dict(SWNS=slack,HWNS=0.020))))
        try:build_audit(p.relative_to(R).as_posix())
        except AssertionError:outcomes[label]='REJECTED'
        else:raise AssertionError('Unsafe physical record accepted: '+label)
    name='private_guard_stale_'+stamp
    records=R/'reports/refined/regression';record=records/(name+'_fixture.json')
    bench=root/'artificial_tb.sv';bench.write_text('// Artificial guard fixture, not an executed test.\n')
    module='rtl/color_regions/stage1_point.v';expected=sha(R/module)
    inputs={module:('0' if expected[0]!='0' else '1')+expected[1:]}
    record.write_text(json.dumps(dict(artificial_guard_fixture=True,inputs=inputs,exit_code=0,expected_failure=False,
       fixture_inputs={bench.relative_to(R).as_posix():sha(bench)},producer_inputs={'scripts/test_stage1_release_guards.py':sha(Path(__file__))})))
    record.with_suffix('.log').write_text('PRIVATE_STALE_EVIDENCE_SENTINEL\n')
    assert evidence(name,'PRIVATE_STALE_EVIDENCE_SENTINEL',('stage1_point',)) is None
    outcomes['stale_source']='REJECTED'
    result=dict(status='RELEASE_GUARDS_PASS',checks=outcomes,scope='Artificial negative fixtures only; not board or functional evidence')
    report=R/'reports/stage1'/('guards_'+stamp+'.json');report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(result,indent=2));print('STAGE1_RELEASE_GUARDS_PASS',outcomes)

if __name__=='__main__':main()
