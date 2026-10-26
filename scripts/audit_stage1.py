"""Current-source software and final physical gates for the region candidate."""
from pathlib import Path
import argparse,datetime,hashlib,json,re,subprocess,sys,zipfile
from stage1_policy import check_branch,check_protected,baseline_inputs,canonical_build_inputs,git,sha
from refined_build_report import assess
R=Path(__file__).resolve().parents[1]
ARCHIVE=R/'build/target_color_regions_osd_memory_20261019_234705/osd_memory_same_source.zip'
BASE_AUDIT=R/'reports/osd_memory/final_audit_20261019_2344.json'

def old_modules():
    assert sha(ARCHIVE)=='9ec0eb66550b2c67db809c6ce4e5cc69258b0187d89d891bf0f99f6469ead9d3'
    old=json.loads(BASE_AUDIT.read_text(encoding='utf-8'));result={}
    with zipfile.ZipFile(ARCHIVE) as z:
        assert BASE_AUDIT.read_bytes()==z.read(BASE_AUDIT.relative_to(R).as_posix())
        for name,e in old['regression'].items():
            rp=e['record'].replace('\\','/');lp=str(Path(rp).with_suffix('.log')).replace('\\','/')
            assert hashlib.sha256(z.read(rp)).hexdigest()==e['record_sha256'],name
            assert hashlib.sha256(z.read(lp)).hexdigest()==e['log_sha256'],name
            for n,h in e['inputs'].items():
                n=n.replace('\\','/');p=R/n
                data=p.read_bytes() if p.is_file() else z.read(n)
                assert hashlib.sha256(data).hexdigest()==h,'Changed baseline dependency '+n
            result[name]=e
    assert len(result)==160
    return dict(scope='UNCHANGED BASELINE MODULES ONLY; new UI/control/region behavior requires new checks',
                archive=ARCHIVE.relative_to(R).as_posix(),archive_sha256=sha(ARCHIVE),checks=result)

def specs():
    d={
      'stage1_teach_motion':('STAGE1_TEACH_MOTION_PASS distance_cases=100',('stage1_regions',)),
      'stage1_teach_route':('STAGE1_TEACH_ROUTE_PASS 60s',('stage1_regions',)),
      'stage1_teach_integration':('STAGE1_TEACH_INTEGRATION_PASS',('stage1_regions','stage1_sequence','stage1_controls','refined_zoom_geometry')),
      'stage1_teach_ui':('STAGE1_TEACH_UI_PASS cases=37',('stage1_ui_formatter',)),
      'stage1_teach_pixels':('STAGE1_TEACH_PIXELS_PASS cases=12 pixels=9584640',('stage1_regions','stage1_osd','stage1_ui_formatter')),
      'stage1_teach_keys_75m':('STAGE1_TEACH_KEYS_75M_PASS',('stage1_controls',)),
      'stage1_real_keys':('STAGE1_REAL_KEYS_PASS durations50/100/300',('stage1_controls','stage1_regions','refined_line_reader','stable_display')),
      'stage1_real_keys_faults':('STAGE1_REAL_KEYS_FAULTS_PASS',('stage1_controls','stage1_regions','refined_line_reader','stable_display')),
      'stage1_transactions':('STAGE1_TRANSACTIONS_PASS',('stage1_regions','stage1_render','stage1_sequence')),
      'stage1_project_guards':('STAGE1_PROJECT_GUARDS_PASS',()),
      'stage1_controls':('STAGE1_CONTROLS_PASS',('stage1_controls',)),
      'stage1_sequence':('STAGE1_SEQUENCE_PASS',('stage1_sequence',)),
      'stage1_age_equivalence_1':('STAGE1_AGE_EQUIVALENCE_PASS period=1 cycles=1284003',('stage1_sequence',)),
      'stage1_age_equivalence_3':('STAGE1_AGE_EQUIVALENCE_PASS period=3 cycles=3452003',('stage1_sequence',)),
      'stage1_regions':('STAGE1_EDIT_RENDER_PASS point_pixels=134400',('stage1_regions','stage1_sequence','stage1_render')),
      'stage1_buzzer':('STAGE1_BUZZER_PASS',('stage1_buzzer',)),
      'stage1_buzzer_75m':('STAGE1_BUZZER_75M_PASS',('stage1_buzzer','stage1_top')),
      'stage1_camera_0':('NACK=0 retries=0',('stage1_controls','stage1_top')),
      'stage1_camera_1':('NACK=1 retries=1',('stage1_controls','stage1_top')),
      'stage1_render_14_624':('STAGE1_RENDER_PASS cases=14 pixels=11182080',('stage1_render',)),
      'stage1_rect_capacity':('RECT_CAPACITY_PASS',('stage1_regions','stage1_render','stage1_sequence')),
      'stage1_rect_geometry':('RECT_GEOMETRY_PASS cases=1024',('stage1_regions','stage1_sequence')),
      'stage1_render_guards':('STAGE1_RENDER_GUARDS_PASS',('stage1_render',)),
      'stage1_overlay':('STAGE1_OVERLAY_PASS cases=8 pixels=6389760',('stage1_osd','stage1_render')),
      'stage1_ui':('STAGE1_UI_CONTRACT_PASS',('stage1_ui_formatter','stage1_ui_text')),
      'stage1_region_footer':('STAGE1_REGION_FOOTER_PASS cases=13 pixels=1597440',('stage1_osd','stage1_ui_formatter')),
      'stage1_english_ui':('STAGE1_ENGLISH_UI_PASS 45 cases 5529600 pixels',('stage1_osd',)),
      'stage1_english_abort':('STAGE1_ENGLISH_ABORT_PASS 2 cases 245760 pixels',('stage1_osd',)),
      'stage1_english_wait':('STAGE1_ENGLISH_WAIT_PASS 1 cases 122880 pixels',('stage1_osd',)),
    }
    jobs=[(p,z,m,r,0,1) for p in (0,1) for z in range(5) for m in range(4) for r in (0,1)]
    jobs += [(0,0,0,r,1,2) for r in (0,1)]+[(0,1,0,r,0,2) for r in (0,1)]
    for p,z,m,r,f,n in jobs:d[f'stage1_video_{p}_{z}_{m}_{r}_f{f}_n{n}']=('STABLE_VIDEO_PASS:',('stage1_osd','refined_line_reader'))
    for p in (0,1):
        for r in (0,1):d[f'stage1_v4_live_{p}_{r}_refined_g160']=('STAGE1_LIVE_EDITOR_PASS',('stage1_regions','stage1_osd','stable_capture','refined_frame_store'))
    return d

def evidence(prefix,marker,modules):
    required={'rtl/color_regions/'+m+'.v' for m in modules}
    for p in sorted((R/'reports/refined/regression').glob(prefix+'_*.json'),reverse=True):
        try:
            d=json.loads(p.read_text(encoding='utf-8-sig'))
            if d.get('exit_code')!=0 or d.get('expected_failure'):continue
            inputs={n.replace('\\','/'):h for n,h in d['inputs'].items()}
            if not required.issubset(inputs):continue
            fixtures=d.get('fixture_inputs',{});producers=d.get('producer_inputs',{})
            if not fixtures or not producers:continue
            if not all((R/n).is_file() and sha(R/n)==h for group in (inputs,fixtures,producers) for n,h in group.items()):continue
            if marker not in p.with_suffix('.log').read_text(encoding='utf-8'):continue
            if prefix=='stage1_regions' and 'STAGE1_REGIONS_PASS' not in p.with_suffix('.log').read_text():continue
            if prefix=='stage1_ui' and not d.get('oracle_passed'):continue
            if prefix.startswith('stage1_v4_live_') and 'STABLE_LIVE_PASS' not in p.with_suffix('.log').read_text():continue
            return dict(record=p.relative_to(R).as_posix(),record_sha256=sha(p),log_sha256=sha(p.with_suffix('.log')),
                        inputs=inputs,fixture_inputs=fixtures,producer_inputs=producers)
        except (OSError,ValueError,KeyError):continue
    return None

def signature(path,parent,out):
    text=path.read_text(encoding='utf-8').replace('\r','')
    for p in (parent,out):text=text.replace(p.as_posix(),'<ATTEMPT>')
    return '\n'.join(x.rstrip() for x in text.splitlines() if not re.match(r'^(Generated[ \t]+:|[|][ \t]+Date[ \t]+:|Generated (on|at)|Date:|Time:)',x.strip())).strip()

def routing_audit(path):
    text=Path(path).read_text(encoding='utf-8')
    start=text.rfind('RUN-1002 : start command "route"')
    assert start>=0,'Missing route command'
    final=text[start:]
    # TD's DRC stage number changes when post-route optimization adds stages.
    # Bind the actual start/end and its Bound Check to the same stage number.
    drcs=list(re.finditer(r'^PHY-1001 : Stage (\d+) \| Routing DRC\s*$',final,re.M))
    assert len(drcs)==1,'Missing or ambiguous routing DRC'
    drc=drcs[0];stage=drc.group(1)
    end=re.search(r'^PHY-1001 : End Stage '+re.escape(stage)+r' \| Routing DRC;',final,re.M)
    assert drc and end and end.start()>drc.end(),'Missing completed routing DRC'
    congestion=re.findall(r'over cnt = (\d+)\([^)]*\), over = (\d+), worst = (\d+)',final[:drc.start()])
    assert congestion and tuple(map(int,congestion[-1]))==(0,0,0),'Final routing conflicts remain or are unreported'
    checks=final[drc.end():end.start()]
    assert 'No multi-drive.' in checks and 'No abnormal timing path.' in checks
    bound=re.search(r'Stage '+re.escape(stage)+r'\.6 \| Bound Check(.*?)End Stage '+re.escape(stage)+r'\.6',checks,re.S)
    assert bound and 'Check Pass.' in bound[1],'Routing bound check did not pass'
    finish=final.find('RUN-1003 : finish command "route"',end.end())
    assert finish>=0 and final.find('REFINED_CHECKPOINT_FULL_COMPLETED',finish)>finish
    assert 'BUILD_FAILED:' not in final
    return dict(final_over_count=0,final_over=0,final_worst=0,routing_drc_pass=True,log_sha256=sha(Path(path)))


def gate_reuse_audit(parent,before,commit):
    """Verify the original compiler identity behind an optional gate reflow."""
    context=json.loads((parent/'source_context.json').read_text())
    reuse=context.get('reused_gate')
    if not reuse:return None
    ps=json.loads((parent/'summary.json').read_text())
    assert ps['reused_gate']==reuse and ps['gate_input_unchanged']
    assert reuse['git_blob_inputs_verified']==len(before)
    creator=reuse['placement_created_commit'];assert re.fullmatch('[0-9a-f]{40}',creator)
    subprocess.run(['git','-c','safe.directory='+R.as_posix(),'merge-base','--is-ancestor',creator,'HEAD'],cwd=R,check=True)
    origin=(R/reuse['parent']).resolve();assert origin.is_relative_to(R/'build') and origin!=parent
    assert sha(origin/'summary.json')==reuse['parent_summary_sha256']
    assert sha(origin/'source_context.json')==reuse['parent_context_sha256']
    assert sha(origin/'inputs.json')==reuse['parent_inputs_sha256']==sha(parent/'inputs.json')
    original=json.loads((origin/'summary.json').read_text())
    assert original['stage']=='place' and original['exit_code']==0 and original['inputs_unchanged']
    original_context=json.loads((origin/'source_context.json').read_text())
    assert original_context['compiled_source_commit']==commit==context['compiled_source_commit']
    assert not original_context.get('reused_gate'),'Nested gate reuse requires its own provenance support'
    assert before==json.loads((origin/'inputs_after.json').read_text())
    assert all(sha(origin/'compiled_source'/n)==h for n,h in before.items())
    db='target_color_regions_gate.db'
    assert sha(parent/'input_gate.db')==sha(origin/db)==original['checkpoints'][db]==reuse['checkpoint_sha256']
    return dict(parent=origin.relative_to(R).as_posix(),checkpoint_sha256=reuse['checkpoint_sha256'],
                compiled_source_commit=commit,placement_created_commit=creator,inputs_verified=len(before))


def build_audit(attempt):
    out=(R/attempt).resolve();assert out.is_relative_to(R/'build')
    s=json.loads((out/'summary.json').read_text());a=assess(out,'full')
    assert s['stage']=='full' and s['exit_code']==0 and s['inputs_unchanged'] and s['resource_pass'] and s['timing_pass']
    assert a['resource_pass'] and a['timing_pass'] and a['resources']==s['resources'] and a['slack_ns']==s['slack_ns']
    routing=routing_audit(out/'td.log')
    before=json.loads((out/'inputs.json').read_text());canonical_build_inputs(before)
    assert before==json.loads((out/'inputs_after.json').read_text())
    assert all(sha(out/'compiled_source'/n)==h for n,h in before.items())
    context=json.loads((out/'source_context.json').read_text());commit=context['compiled_source_commit']
    assert context['input_count']==len(before) and context['inputs_sha256']==sha(out/'inputs.json')
    assert re.fullmatch('[0-9a-f]{40}',commit)
    subprocess.run(['git','-c','safe.directory='+R.as_posix(),'merge-base','--is-ancestor',commit,'HEAD'],cwd=R,check=True)
    names=list(before)
    raw=subprocess.run(['git','-c','safe.directory='+R.as_posix(),'cat-file','--batch'],cwd=R,
      input=('\n'.join(commit+':'+n for n in names)+'\n').encode(),capture_output=True,check=True).stdout
    offset=0
    for n in names:
        end=raw.index(b'\n',offset);header=raw[offset:end];offset=end+1
        assert not header.endswith(b' missing'),n
        size=int(header.split()[-1]);assert hashlib.sha256(raw[offset:offset+size]).hexdigest()==before[n],n;offset+=size+1
    proof=s['checkpoint_provenance'];assert context['placed_checkpoint']==proof and s['checkpoint_unchanged']
    parent=(R/proof['parent']).resolve();assert parent.is_relative_to(R/'build')
    assert sha(parent/'summary.json')==proof['parent_summary_sha256']
    assert sha(parent/'source_context.json')==proof['parent_context_sha256']
    assert sha(parent/'inputs.json')==proof['parent_inputs_sha256']==sha(out/'inputs.json')
    ps=json.loads((parent/'summary.json').read_text());assert ps['stage']=='place' and ps['exit_code']==0 and ps['resource_pass'] and ps['inputs_unchanged']
    assert before==json.loads((parent/'inputs_after.json').read_text())
    assert all(sha(parent/'compiled_source'/n)==h for n,h in before.items())
    assert json.loads((parent/'source_context.json').read_text())['compiled_source_commit']==commit
    reused_gate=gate_reuse_audit(parent,before,commit)
    db=proof['checkpoint_name'];assert db=='target_color_regions_placed.db'
    assert sha(parent/db)==sha(out/db)==proof['checkpoint_sha256']==ps['checkpoints'][db]
    assert 'CHECKPOINT_CONSTRAINT_ROUNDTRIP_PASS' in (out/'td.log').read_text()
    for n in ('placed_clocks.txt','placed_exceptions.timing'):assert signature(parent/n,parent,out)==signature(out/n,parent,out),n
    for n,h in s.get('route_checkpoints',{}).items():assert sha(out/n)==h
    assert (out/'target_color_regions.bit').is_file()
    timing=(out/'target_color_regions_pr.timing').read_text()
    return dict(attempt=out.relative_to(R).as_posix(),summary=s,compiled_source_commit=commit,
                git_blob_inputs_verified=len(before),reused_gate=reused_gate,bit_sha256=sha(out/'target_color_regions.bit'),routing=routing,
                sta_coverage_percent=float(re.search(r'STA coverage\s*:\s*([\d.]+)%',timing)[1]))

def audit(attempt=None,progress=False):
    check_branch(R);baseline_inputs(R);check_protected()
    subprocess.run([sys.executable,'-X','utf8',str(R/'scripts/generate_stage1.py'),'--check'],cwd=R,check=True)
    result=dict(branch=git(R,'branch','--show-current'),head=git(R,'rev-parse','HEAD'),baseline=old_modules(),
                original_protection_pass=True,generator_pass=True,hardware_status='PENDING')
    result['regression']={};missing=[]
    for n,(marker,mods) in specs().items():
        e=evidence(n,marker,mods)
        if e:result['regression'][n]=e
        else:missing.append(n)
    result.update(required=len(specs()),passed=len(result['regression']),missing=missing)
    if not progress:assert not missing,'Missing current evidence: '+', '.join(missing)
    if attempt:result['build']=build_audit(attempt)
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--attempt');ap.add_argument('--progress',action='store_true');ap.add_argument('--output');a=ap.parse_args()
    obj=audit(a.attempt,a.progress)
    if a.output:
        p=R/a.output;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:obj[k] for k in ('head','required','passed','missing')},ensure_ascii=False))
