"""Independent byte-level review of a completed candidate archive."""
from pathlib import Path
import argparse,datetime,hashlib,json,zipfile
from audit_refined import R,audit
from osd_memory_branch import check_osd_only
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--directory',required=True);a=ap.parse_args()
    dest=(R/a.directory).resolve();assert dest.is_relative_to(R/'build') and dest.name.startswith('target_color_regions_osd_memory_')
    d=json.loads((dest/'delivery.json').read_text(encoding='utf-8'))
    manifest=json.loads((dest/'source_files.json').read_text(encoding='utf-8'))
    assert sha(R/d['bit'])==d['bit_sha256']
    archive=R/d['source_zip'];assert sha(archive)==d['source_zip_sha256']
    with zipfile.ZipFile(archive) as z:
        assert set(z.namelist())==set(manifest)|{'SOURCE_MANIFEST.json'}
        assert json.loads(z.read('SOURCE_MANIFEST.json'))==manifest
        for n,h in manifest.items():
            assert hashlib.sha256(z.read(n)).hexdigest()==h,'ZIP member '+n
            assert (R/n).is_file() and sha(R/n)==h,'Current source '+n
    compiled=json.loads((dest/'inputs.json').read_text(encoding='utf-8'))
    assert all(manifest[n]==h for n,h in compiled.items())
    for line in (dest/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        expected,name=line.split('  ',1);assert sha(dest/name)==expected,name
    current=audit(d['build']['attempt'],True)
    assert current['build']['bit_sha256']==d['bit_sha256']
    assert current['build']['compiled_source_commit']==d['build']['compiled_source_commit']
    assert len(current['regression'])==160 and check_osd_only(R)==292
    original=R/'build/target_color_regions_refined_20261019_100417'
    assert sha(original/'target_color_regions.bit')==d['baseline_bit_sha256']
    assert sha(original/'color_video_refined_source.zip')=='84711c7f21cb0f5d025d3842c9cb52cc62028695356b4442e9f5b5981ec5502e'
    assert sha(R/'td_project/target_color_regions.al')=='4467601011e2e6df3603c786579b175bcc71a537469bfc75c6b533ffee05de64'
    result=dict(passed=True,directory=dest.relative_to(R).as_posix(),source_files=len(manifest),compiled_inputs=len(compiled),
                regression_checks=len(current['regression']),bit_sha256=d['bit_sha256'],source_zip_sha256=d['source_zip_sha256'],
                original_chinese_delivery_preserved=True,user_project_preserved=True,hardware='PENDING')
    target=R/'reports/osd_memory'/('delivery_review_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.json')
    with target.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print('OSD_MEMORY_DELIVERY_REVIEW_PASS',json.dumps(result),flush=True)

if __name__=='__main__':main()
