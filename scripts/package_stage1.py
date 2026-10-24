"""Publish only a fully audited, same-source stage-one board-test candidate."""
from pathlib import Path
import argparse,datetime,json,shutil,zipfile
from audit_stage1 import R,audit,sha

def write_new(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')

def package(attempt):
    proof=audit(attempt)
    guard_report=R/'reports/stage1/routing_guards_20261024_123949.json'
    guards=json.loads(guard_report.read_text(encoding='utf-8'))
    assert guards['status']=='ROUTING_GUARDS_PASS' and len(guards['checks'])==6 and set(guards['checks'].values())=={'REJECTED'}
    assert guards['auditor_sha256']==sha(R/'scripts/audit_stage1.py')
    assert guards['producer_sha256']==sha(R/'scripts/test_stage1_routing_guards.py')
    assert all(sha(R/n)==h for n,h in guards['fixtures'].items())
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    report=R/'reports/stage1'/('final_audit_'+stamp+'.json');report.parent.mkdir(parents=True,exist_ok=True)
    write_new(report,proof)
    build=R/proof['build']['attempt'];compiled=json.loads((build/'inputs.json').read_text())
    dest=R/'build'/('target_region_sequence_stage1_'+stamp);dest.mkdir(exist_ok=False)
    paths={R/n for n in compiled}|{build/'compiled_source'/n for n in compiled}|{report,guard_report}|{R/n for n in guards['fixtures']}
    for folder in ('scripts','sim','rtl'):
        paths|={p for p in (R/folder).rglob('*') if p.is_file() and p.suffix in ('.py','.tcl','.txt','.sv','.v','.json')}
    paths|={p for p in (R/'assets/osd/anlogic').iterdir() if p.is_file()}
    paths|={R/'README.md',R/'reports/stage1/validation.md',R/'reports/stage1/software_current_20261024_0944.json',
            R/'reports/stage1/guards_20261024_123949.json',
            R/'docs/区域顺序_第一阶段_执行记录.md',R/'docs/区域顺序_第一阶段_操作与实测.md',R/'reports/osd_memory/final_audit_20261019_2344.json',
            R/proof['baseline']['archive']}
    for e in proof['regression'].values():
        rp=R/e['record'];paths|={rp,rp.with_suffix('.log')}
        paths|={R/n for group in (e['inputs'],e['fixture_inputs'],e['producer_inputs']) for n in group}
    parent=R/proof['build']['summary']['checkpoint_provenance']['parent']
    paths|={parent/'compiled_source'/n for n in compiled}
    if proof['build'].get('reused_gate'):
        origin=R/proof['build']['reused_gate']['parent']
        paths|={origin/'compiled_source'/n for n in compiled}
        paths|={origin/n for n in ('summary.json','source_context.json','inputs.json','inputs_after.json',
                                  'flow_options.json','run.tcl','td.log','target_color_regions_gate.db')}
        gate_guard_report=R/'reports/stage1/gate_reuse_guards_20261024_123949.json'
        gate_guards=json.loads(gate_guard_report.read_text(encoding='utf-8'))
        assert gate_guards['status']=='GATE_REUSE_GUARDS_PASS' and len(gate_guards['checks'])==4
        assert set(gate_guards['checks'].values())=={'REJECTED'}
        assert gate_guards['auditor_sha256']==sha(R/'scripts/audit_stage1.py')
        assert gate_guards['producer_sha256']==sha(R/'scripts/test_stage1_gate_reuse_guards.py')
        assert all(sha(R/n)==h for n,h in gate_guards['fixtures'].items())
        paths|={gate_guard_report}|{R/n for n in gate_guards['fixtures']}
    for directory in (parent,build):
        for p in directory.iterdir():
            if p.is_file() and p.suffix in ('.json','.tcl','.area','.timing','.ts','.txt','.log','.zip','.db','.bit'):paths.add(p)
    for p in paths:assert p.is_file() and p.is_relative_to(R),p
    manifest={p.relative_to(R).as_posix():sha(p) for p in sorted(paths)}
    assert all(manifest[n]==h for n,h in compiled.items())
    archive=dest/'region_sequence_same_source.zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(paths):z.write(p,p.relative_to(R).as_posix())
        z.writestr('SOURCE_MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    for n in ('target_color_regions.bit','summary.json','inputs.json','inputs_after.json','source_context.json','flow_options.json',
              'checkpoint_provenance.json','target_color_regions_phy.area','target_color_regions_phy.ts','target_color_regions_pr.timing',
              'target_color_regions_clocks.txt','target_color_regions_exception.timing','placed_clocks.txt','placed_exceptions.timing','td.log'):
        if (build/n).is_file():shutil.copy2(build/n,dest/n)
    write_new(dest/'source_files.json',manifest)
    delivery=dict(status='CANDIDATE_SOFTWARE_AND_FINAL_PHYSICAL_PASSED_HARDWARE_PENDING',
      archive_name='矩形区域顺序报警第一阶段候选',branch=proof['branch'],head=proof['head'],
      compiled_source_commit=proof['build']['compiled_source_commit'],attempt=proof['build']['attempt'],
      directory=dest.relative_to(R).as_posix(),bit_sha256=sha(dest/'target_color_regions.bit'),
      source_zip_sha256=sha(archive),source_file_count=len(manifest),audit=report.relative_to(R).as_posix(),audit_sha256=sha(report),
      resources=proof['build']['summary']['resources'],slack_ns=proof['build']['summary']['slack_ns'],
      baseline_module_checks=160,stage1_checks=proof['passed'],hardware_status='PENDING; no board download or Flash write')
    write_new(dest/'delivery.json',delivery)
    with (dest/'SHA256SUMS.txt').open('x',encoding='utf-8') as f:
        for p in sorted(dest.iterdir()):
            if p.is_file() and p.name!='SHA256SUMS.txt':f.write(sha(p)+'  '+p.name+'\n')
    from verify_stage1_delivery import verify
    checked=verify(dest)
    write_new(R/'reports/stage1'/('delivery_review_'+stamp+'.json'),checked)
    print('STAGE1_DELIVERY_VERIFIED',dest)
    return dest

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--attempt',required=True);a=ap.parse_args();package(a.attempt)
