"""Publish a local SRAM candidate only from verified, matching frozen inputs."""
from pathlib import Path
import argparse,datetime,hashlib,json,shutil,sys,zipfile
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'))
from refined_build_report import assess

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def require(value,message):
    if not value:raise SystemExit('CANDIDATE_REJECTED: '+message)
def read(path):return json.loads(path.read_text(encoding='utf-8'))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--attempt',type=Path,required=True)
    ap.add_argument('--regression',type=Path,required=True);ap.add_argument('--bad-scene',type=Path,required=True)
    ap.add_argument('--check-only',action='store_true');a=ap.parse_args()
    attempt=a.attempt.resolve();reg=a.regression.resolve();extra=a.bad_scene.resolve()
    build=read(attempt/'summary.json');result=assess(attempt,'full')
    require(build.get('stage')=='full' and build.get('completed') and build.get('exit_code')==0,'full TD flow did not complete')
    require(result['resource_pass'] and result['timing_pass'],'physical resources or final timing failed')
    require('Confidence          : Routed' in (attempt/'target_color_regions_pr.timing').read_text(encoding='utf-8'),'missing routed timing evidence')
    bit=attempt/'target_color_regions_1080p30.bit'
    require(bit.is_file() and bit.stat().st_size>1024,'missing generated bit')
    inputs=read(attempt/'inputs.json')
    for n,h in inputs.items():
        require((R/n).is_file() and sha(R/n)==h,'current build input changed: '+n)
        require(sha(attempt/'compiled_source'/n)==h,'frozen build input changed: '+n)
    suite=read(reg/'summary.json')
    require(suite.get('passed') and suite.get('inputs_unchanged'),'final software suite did not pass with unchanged inputs')
    require(len(suite['jobs'])==16 and all(j['exit_code']==0 for j in suite['jobs']),'missing final software jobs')
    for j in suite['jobs']:
        require(sha(Path(j['log']))==j['log_sha256'],'software log changed: '+j['name'])
    software_inputs=read(reg/'inputs.json');constraint_updates=[]
    for n,h in software_inputs.items():
        if not (R/n).is_file() or sha(R/n)!=h:
            # SDC is not consumed by RTL simulation. A later SDC revision is
            # allowed only when the final physical run above validated its
            # exact current bytes. No RTL/test/other input differences pass.
            # The build runner is validated by the actual full TD invocation,
            # not executed by the RTL suite. It must itself be frozen exactly.
            require(n in ('td_project/target_1080p30.sdc','scripts/run_fhd_build.py') and inputs.get(n)==sha(R/n),'software input changed: '+n)
            constraint_updates.append(n)
    bad=read(extra);require(bad.get('passed') and bad.get('inputs_unchanged') and not bad.get('timed_out'),'distinct short-frame recovery check failed')
    for n,h in bad['inputs'].items():require(sha(R/n)==h,'recovery input changed: '+n)
    fixture=Path(bad['output'])/'tb.sv'
    require(sha(fixture)==bad['fixture_sha256'] and "f==10?8'ha0" in fixture.read_text(encoding='utf-8'),'missing distinguishable invalid scene')
    templates=read(R/'reports/fhd/template_manifest.json')
    for n,h in templates.items():
        require(sha(R/n)==h and sha(R/'templates/fhd'/n)==h,'reviewed template differs: '+n)
    require(read(R/'reports/fhd/original_unchanged.json')['unchanged'],'original 720p input audit did not pass')
    cdc=read(R/'reports/fhd/cdc_routes.json')
    require(cdc.get('report_created') and Path(cdc['log']).resolve().parent==attempt and sha(Path(cdc['log']))==cdc['log_sha256'],'missing matching routed CDC diagnostics')
    print('CANDIDATE_GATES_PASS',json.dumps(result),flush=True)
    if a.check_only:return 0
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    out=R/'build'/('delivery_1080p30_'+stamp);out.mkdir()
    target=out/'native_1080p30_sram.bit';shutil.copyfile(bit,target)
    info=dict(status='software_and_routed_timing_pass_hardware_pending',created_local=datetime.datetime.now().isoformat(),
              source_commit=read(R/'reports/fhd/source_commit.json')['commit'],
              bit=target.name,bit_sha256=sha(target),physical=result,physical_strategy=read(attempt/'physical_settings.json'),build_attempt=str(attempt),build_inputs_sha256=sha(attempt/'inputs.json'),
              regression=str(reg/'summary.json'),regression_sha256=sha(reg/'summary.json'),bad_scene=str(extra),bad_scene_sha256=sha(extra),
              physical_inputs_revalidated_after_simulation=constraint_updates,hardware_verified=False,
              pending=['SRAM download','actual source frame rate','focus/FOV/recognition','full controls','recovery','30 minute run','720p versus 1080p detail comparison'])
    manifest=out/'CANDIDATE.json';manifest.write_text(json.dumps(info,indent=2),encoding='utf-8')
    archive=out/'native_1080p30_source_and_evidence.zip'
    folders=('rtl','ip','user_source','assets','scripts','sim','td_project','templates','reports','docs','.scratch','tests')
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for folder in folders:
            for p in sorted((R/folder).rglob('*')):
                if p.is_file() and '__pycache__' not in p.parts:z.write(p,p.relative_to(R).as_posix())
        for name in ('README.md','profile_1080p30.json','.gitignore','.gitattributes'):
            z.write(R/name,name)
        for p in R.glob('*.py'):z.write(p,p.name)
        for p in (R/'tools/iverilog').rglob('*'):
            if p.is_file():z.write(p,p.relative_to(R).as_posix())
        z.write(R/'tools/native_sim/manifest.json','tools/native_sim/manifest.json')
        z.write(manifest,'CANDIDATE.json')
        for name in ('inputs.json','summary.json','run.tcl','td.log','target_color_regions_phy.ts','target_color_regions_phy.area',
                     'target_color_regions_pr.timing','target_color_regions_exception.timing','fhd_clocks.txt','physical_settings.json','cdc_routes.log','audit_cdc_routes.tcl'):
            z.write(attempt/name,'verification/td/'+name)
        # Preserve executed fixtures and their external coordinate oracle, not
        # host-specific generated simulation binaries.
        for p in (R/'build/sim').rglob('*'):
            if p.is_file() and p.suffix in ('.sv','.hex'):z.write(p,p.relative_to(R).as_posix())
    info.update(source_archive=archive.name,source_archive_sha256=sha(archive),candidate_directory=str(out))
    manifest.write_text(json.dumps(info,indent=2),encoding='utf-8')
    (out/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in (target,archive,manifest)),encoding='ascii')
    (R/'reports/fhd/delivery.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
    require(sha(target)==sha(bit),'bit copy changed')
    with zipfile.ZipFile(archive) as z:
        for n,h in inputs.items():require(hashlib.sha256(z.read(n)).hexdigest()==h,'archived build input differs: '+n)
    print('CANDIDATE_PUBLISHED',out,flush=True)
    return 0
if __name__=='__main__':sys.exit(main())
