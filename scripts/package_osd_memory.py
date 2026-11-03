"""Archive a verified OSD candidate without editing any prior delivery/report."""
from pathlib import Path
import argparse,datetime,hashlib,json,re,shutil,zipfile
from audit_refined import R,audit
from osd_memory_branch import check_osd_only

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def record(p,obj):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--attempt',required=True);a=ap.parse_args()
    obj=audit(a.attempt,True);check_osd_only(R)
    assert obj['english_ui'] and obj['build']['summary']['resources']['eram']<=99,'No verified memory saving'
    attempt=R/obj['build']['attempt'];stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    dest=R/'build'/('target_color_regions_osd_memory_'+stamp);dest.mkdir(exist_ok=False)
    obj.update(status='CANDIDATE_SOFTWARE_AND_BUILD_PASSED_HARDWARE_PENDING',baseline_commit='7df95aabb9fedc7927d03aa6013aa6a9346eb962',
               baseline_bit_sha256='fe6029bb4fd343df1e7757418c1b2540e2c9884d93f27206a9464509bc3586fe',
               archive_name='英文共用字库与静态文字表节省存储候选',hardware='PENDING; no board download or Flash write',
               delivery_directory=dest.relative_to(R).as_posix())
    for n in ('target_color_regions.bit','compiled_inputs.zip','summary.json','inputs.json','inputs_after.json','source_context.json','run.tcl',
              'target_color_regions_phy.area','target_color_regions_phy.ts','target_color_regions_pr.timing',
              'target_color_regions_clocks.txt','target_color_regions_exception.timing','td.log','checkpoint_provenance.json','placed_clocks.txt','placed_exceptions.timing'):
        if (attempt/n).is_file():shutil.copy2(attempt/n,dest/n)
    assert sha(dest/'target_color_regions.bit')==obj['build']['bit_sha256']
    compiled=json.loads((attempt/'inputs.json').read_text(encoding='utf-8'))
    paths={R/n for n in compiled}
    paths|={attempt/'compiled_source'/n for n in compiled}
    paths|={attempt/n for n in obj['build']['summary'].get('route_checkpoints',{})}
    for folder in ('scripts','rtl','sim'):
        paths|={p for p in (R/folder).rglob('*') if p.is_file() and p.suffix in ('.py','.tcl','.txt','.v','.sv','.json')}
    paths|={p for p in (R/'assets/osd/anlogic').iterdir() if p.is_file()}
    paths|={p for p in (R/'build/sim').glob('refined_video*/*.hex') if p.is_file()}
    paths|={R/'docs/OSD英文节省存储_实施说明.md',R/'docs/颜色视频显示改进_上板一页.md'}
    paths|={p for p in (R/'reports/osd_memory').glob('*') if p.is_file()}
    for name in ('osd_memory_baseline','osd_memory_english_baseline'):
        p=R/'reports/refined'/(name+'.json');paths.add(p);paths.add(R/json.loads(p.read_text())['archive'])
    # The old compact check and generator retain the original protection snapshots.
    for p in (R/'reports/refined/protected_inputs.json',R/'reports/refined/user_project_change_20261017.json'):
        paths.add(p)
    protection=json.loads((R/'reports/refined/protected_inputs.json').read_text())
    observed=json.loads((R/'reports/refined/user_project_change_20261017.json').read_text())
    paths|={R/protection['backup']/'sources_before.zip',R/observed['preserved_copy']}
    for e in obj['regression'].values():
        rp=R/e['record'];paths|={rp,rp.with_suffix('.log')};paths|={R/n for n in e['inputs']}
        entry=json.loads(rp.read_text(encoding='utf-8-sig'))
        if entry.get('output'):
            benches=[Path(entry['output'])/'tb.sv']
        else:
            # The original ingress wrapper predates refined_testlib and stores
            # only inputs/passed. Its timestamp identifies three saved benches.
            assert rp.stem.startswith('ingress_'),'Unknown legacy evidence schema: '+rp.name
            benches=sorted((R/'build/sim'/('refined_'+rp.stem)).glob('*.sv'))
            assert len(benches)==3,'Legacy ingress replay benches are incomplete'
        for bench in benches:
            assert bench.is_relative_to(R) and bench.is_file();paths.add(bench)
            for n in re.findall(r'\$readmem[hb]\s*\(\s*"([^"]+)"',bench.read_text(encoding='utf-8-sig')):
                p=Path(n);p=p if p.is_absolute() else R/p
                assert p.is_relative_to(R) and p.is_file(),p;paths.add(p)
    for n in ('summary.json','inputs.json','inputs_after.json','source_context.json','run.tcl','td.log','compiled_inputs.zip','flow_options.json',
              'target_color_regions_phy.area','target_color_regions_pr.timing','target_color_regions_exception.timing','target_color_regions_clocks.txt','checkpoint_provenance.json','placed_clocks.txt','placed_exceptions.timing'):
        if (attempt/n).is_file():paths.add(attempt/n)
    if obj['build']['summary'].get('checkpoint_provenance'):
        proof=obj['build']['summary']['checkpoint_provenance'];parent=R/proof['parent']
        paths.add(attempt/proof['checkpoint_name'])
        paths|={parent/'compiled_source'/n for n in compiled}
        for n in ('summary.json','source_context.json','inputs.json','inputs_after.json','flow_options.json','run.tcl','td.log',
                  'target_color_regions_gate.area','target_color_regions_phy.area','placed_clocks.txt','placed_exceptions.timing',proof['checkpoint_name']):
            if (parent/n).is_file():paths.add(parent/n)
    manifest={p.relative_to(R).as_posix():sha(p) for p in sorted(paths)}
    assert all(manifest[n]==h for n,h in compiled.items())
    archive=dest/'osd_memory_same_source.zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(paths):z.write(p,p.relative_to(R).as_posix())
        z.writestr('SOURCE_MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    with zipfile.ZipFile(archive) as z:
        assert set(z.namelist())==set(manifest)|{'SOURCE_MANIFEST.json'}
        for n,h in manifest.items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
    record(dest/'source_files.json',manifest)
    obj.update(bit=(dest/'target_color_regions.bit').relative_to(R).as_posix(),bit_sha256=sha(dest/'target_color_regions.bit'),
               source_zip=archive.relative_to(R).as_posix(),source_zip_sha256=sha(archive),source_file_count=len(manifest))
    record(dest/'delivery.json',obj);record(R/'reports/osd_memory'/('delivery_'+stamp+'.json'),obj)
    with (dest/'SHA256SUMS.txt').open('x',encoding='utf-8') as f:
        for p in sorted(dest.iterdir()):
            if p.is_file() and p.name!='SHA256SUMS.txt':f.write(sha(p)+'  '+p.name+'\n')
    print('OSD_MEMORY_DELIVERY_VERIFIED',dest,flush=True)

if __name__=='__main__':main()
