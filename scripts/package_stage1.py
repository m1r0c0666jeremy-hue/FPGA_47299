"""Publish only a fully audited, same-source stage-one board-test candidate."""
from pathlib import Path
import argparse,datetime,json,shutil,zipfile
from audit_stage1 import R,audit,sha

def write_new(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')

def package(attempt,software,routing_guards,release_guards,gate_reuse_guards):
    proof=audit(attempt)
    software_report=R/software
    saved=json.loads(software_report.read_text(encoding='utf-8'))
    assert saved['passed']==proof['required'] and not saved['missing']
    assert saved['regression']==proof['regression'],'Software receipt differs from current evidence'
    guard_report=R/routing_guards
    guards=json.loads(guard_report.read_text(encoding='utf-8'))
    assert guards['status']=='ROUTING_GUARDS_PASS' and len(guards['checks'])==6 and set(guards['checks'].values())=={'REJECTED'}
    assert len(guards['current_checks'])==8 and set(guards['current_checks'].values())=={'REJECTED'}
    assert guards['auditor_sha256']==sha(R/'scripts/audit_stage1.py')
    assert guards['producer_sha256']==sha(R/'scripts/test_stage1_routing_guards.py')
    assert all(sha(R/n)==h for n,h in guards['fixtures'].items())
    safety_reports=[guard_report]
    safety_fixtures={R/n for n in guards['fixtures']}
    for name,status,producer in ((release_guards,'RELEASE_GUARDS_PASS','test_stage1_release_guards.py'),
                                (gate_reuse_guards,'GATE_REUSE_GUARDS_PASS','test_stage1_gate_reuse_guards.py')):
        path=R/name;result=json.loads(path.read_text(encoding='utf-8'))
        assert result['status']==status and len(result['checks'])==4 and set(result['checks'].values())=={'REJECTED'}
        assert result['auditor_sha256']==sha(R/'scripts/audit_stage1.py')
        assert result['producer_sha256']==sha(R/'scripts'/producer)
        assert all(sha(R/n)==h for n,h in result['fixtures'].items())
        safety_reports.append(path);safety_fixtures|={R/n for n in result['fixtures']}
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    report=R/'reports/stage1'/('final_audit_'+stamp+'.json');report.parent.mkdir(parents=True,exist_ok=True)
    write_new(report,proof)
    build=R/proof['build']['attempt'];compiled=json.loads((build/'inputs.json').read_text())
    dest=R/'build'/('target_region_sequence_stage1_'+stamp);dest.mkdir(exist_ok=False)
    paths={R/n for n in compiled}|{build/'compiled_source'/n for n in compiled}|{report,software_report}|set(safety_reports)|safety_fixtures
    for folder in ('scripts','sim','rtl'):
        paths|={p for p in (R/folder).rglob('*') if p.is_file() and p.suffix in ('.py','.tcl','.txt','.sv','.v','.json')}
    paths|={p for p in (R/'assets/osd/anlogic').iterdir() if p.is_file()}
    paths|={R/'README.md',R/'reports/stage1/validation.md',
            R/'docs/区域顺序_第一阶段_执行记录.md',R/'docs/区域顺序_第一阶段_操作与实测.md',
            R/'docs/示教录制回放与运动状态_操作与验证.md',R/'reports/osd_memory/final_audit_20261019_2344.json',
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
      archive_name='单条路线示教回放与区域运动状态候选',branch=proof['branch'],head=proof['head'],
      compiled_source_commit=proof['build']['compiled_source_commit'],attempt=proof['build']['attempt'],
      directory=dest.relative_to(R).as_posix(),bit_sha256=sha(dest/'target_color_regions.bit'),
      source_zip_sha256=sha(archive),source_file_count=len(manifest),audit=report.relative_to(R).as_posix(),audit_sha256=sha(report),
      resources=proof['build']['summary']['resources'],slack_ns=proof['build']['summary']['slack_ns'],
      baseline_module_checks=160,stage1_checks=proof['passed'],
      software_receipt=software_report.relative_to(R).as_posix(),
      safety_receipts={p.relative_to(R).as_posix():sha(p) for p in safety_reports},
      hardware_status='PENDING; no board download or Flash write')
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
    ap=argparse.ArgumentParser();ap.add_argument('--attempt',required=True)
    for name in ('software','routing-guards','release-guards','gate-reuse-guards'):ap.add_argument('--'+name,required=True)
    a=ap.parse_args();package(a.attempt,a.software,a.routing_guards,a.release_guards,a.gate_reuse_guards)
