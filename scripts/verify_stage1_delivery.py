"""Independent member-by-member verification of a saved stage-one delivery."""
from pathlib import Path
import argparse,hashlib,json,zipfile
from stage1_policy import sha,canonical_build_inputs,check_protected
R=Path(__file__).resolve().parents[1]

def verify(directory):
    dest=(R/directory).resolve();assert dest.is_relative_to(R/'build')
    d=json.loads((dest/'delivery.json').read_text(encoding='utf-8'));assert d['directory']==dest.relative_to(R).as_posix()
    assert d['status']=='CANDIDATE_SOFTWARE_AND_FINAL_PHYSICAL_PASSED_HARDWARE_PENDING'
    assert sha(dest/'target_color_regions.bit')==d['bit_sha256']
    archive=dest/'region_sequence_same_source.zip';assert sha(archive)==d['source_zip_sha256']
    manifest=json.loads((dest/'source_files.json').read_text(encoding='utf-8'))
    assert len(manifest)==d['source_file_count']
    with zipfile.ZipFile(archive) as z:
        assert len(z.namelist())==len(set(z.namelist()))
        assert set(z.namelist())==set(manifest)|{'SOURCE_MANIFEST.json'}
        assert json.loads(z.read('SOURCE_MANIFEST.json'))==manifest
        for n,h in manifest.items():
            p=Path(n);assert not p.is_absolute() and not p.drive and '..' not in p.parts
            assert hashlib.sha256(z.read(n)).hexdigest()==h and sha(R/n)==h,n
        compiled=json.loads(z.read(d['attempt']+'/inputs.json'));canonical_build_inputs(compiled)
        assert all(manifest[n]==h for n,h in compiled.items())
        assert hashlib.sha256(z.read(d['attempt']+'/target_color_regions.bit')).hexdigest()==d['bit_sha256']
    checked=[]
    for line in (dest/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        h,n=line.split('  ',1);assert Path(n).name==n and sha(dest/n)==h,n
        checked.append(n)
    assert len(checked)==len(set(checked)) and set(checked)=={p.name for p in dest.iterdir() if p.is_file() and p.name!='SHA256SUMS.txt'}
    assert sha(R/d['audit'])==d['audit_sha256']
    from audit_stage1 import audit
    proof=audit(d['attempt']);assert proof['passed']==d['stage1_checks'] and not proof['missing']
    assert proof['build']['compiled_source_commit']==d['compiled_source_commit']
    assert proof['build']['summary']['resources']==d['resources'] and proof['build']['summary']['slack_ns']==d['slack_ns']
    if 'safety_receipts' in d:
        assert len(d['safety_receipts'])==3
        expected={'ROUTING_GUARDS_PASS':('test_stage1_routing_guards.py',6),
                  'RELEASE_GUARDS_PASS':('test_stage1_release_guards.py',4),
                  'GATE_REUSE_GUARDS_PASS':('test_stage1_gate_reuse_guards.py',4)}
        seen=set()
        for name,h in d['safety_receipts'].items():
            assert manifest[name]==h and sha(R/name)==h
            record=json.loads((R/name).read_text(encoding='utf-8'));status=record['status'];producer,count=expected[status];seen.add(status)
            assert len(record['checks'])==count and set(record['checks'].values())=={'REJECTED'}
            if status=='ROUTING_GUARDS_PASS':assert len(record['current_checks'])==8 and set(record['current_checks'].values())=={'REJECTED'}
            assert record['auditor_sha256']==sha(R/'scripts/audit_stage1.py')
            assert record['producer_sha256']==sha(R/'scripts'/producer)
            assert all(manifest[n]==v and sha(R/n)==v for n,v in record['fixtures'].items())
        assert seen==set(expected)
        receipt=json.loads((R/d['software_receipt']).read_text(encoding='utf-8'))
        assert receipt['passed']==proof['passed'] and not receipt['missing'] and receipt['regression']==proof['regression']
    check_protected()
    return dict(passed=True,directory=d['directory'],bit_sha256=d['bit_sha256'],source_zip_sha256=d['source_zip_sha256'],
                verified_members=len(manifest),current_stage1_checks=proof['passed'],compiled_inputs=len(compiled),hardware_status='PENDING')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('directory');a=ap.parse_args();print(json.dumps(verify(a.directory),ensure_ascii=False,indent=2))
