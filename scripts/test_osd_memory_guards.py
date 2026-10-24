"""Reject stale/failed delivery attempts and retain all Chinese release bytes."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
from audit_refined import R,canonical_build_inputs
from osd_memory_branch import check_branch,check_osd_only
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert check_branch(R)=='opt/region-1019-osd-memory'
unchanged=check_osd_only(R)
base=R/'build/target_color_regions_refined_20261019_100417'
protected=[base/'target_color_regions.bit',base/'color_video_refined_source.zip',
           R/'td_project/target_color_regions.al',R/'reports/refined/delivery_20261019_100417.json',
           R/'reports/refined/最终验证报告.md',R/'docs/颜色视频显示改进_上板一页.md']
before={p.relative_to(R).as_posix():sha(p) for p in protected}
assert before[(base/'target_color_regions.bit').relative_to(R).as_posix()]=='fe6029bb4fd343df1e7757418c1b2540e2c9884d93f27206a9464509bc3586fe'
assert before[(base/'color_video_refined_source.zip').relative_to(R).as_posix()]=='84711c7f21cb0f5d025d3842c9cb52cc62028695356b4442e9f5b5981ec5502e'
compiled=json.loads((R/'build/refined_route_20261019_100156_645532/inputs.json').read_text())
compiled.update({f'rtl/color_regions/{n}.v':'0'*64 for n in ('refined_english_font_rom','refined_english_text_rom')})
canonical_build_inputs(compiled)
for altered in ({**compiled,'rtl/color_regions/unexpected.v':'0'*64}, {n:v for n,v in compiled.items() if not n.endswith('stable_capture.v')}):
    try:canonical_build_inputs(altered)
    except AssertionError:pass
    else:raise AssertionError('Compiler input boundary accepted an unexpected dependency set')
directories=set((R/'build').glob('target_color_regions_osd_memory_*'))
logs=[]
for attempt in ('build/refined_route_20261018_233608_631875','build/refined_route_20261019_100156_645532'):
    p=subprocess.run([sys.executable,str(R/'scripts/package_osd_memory.py'),'--attempt',attempt],cwd=R,capture_output=True,text=True,encoding='utf-8')
    assert p.returncode!=0,'Stale or failed Chinese attempt was packaged'
    logs.append(attempt+'\n'+p.stdout+p.stderr)
assert directories==set((R/'build').glob('target_color_regions_osd_memory_*'))
assert before=={p.relative_to(R).as_posix():sha(p) for p in protected}
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');target=R/'reports/osd_memory'/('guards_'+stamp)
target.with_suffix('.log').write_text('\n'.join(logs)+'\nOSD_MEMORY_GUARDS_PASS\n',encoding='utf-8')
target.with_suffix('.json').write_text(json.dumps(dict(passed=True,non_osd_inputs_preserved=unchanged,compiler_dependency_rejections=2,
     package_rejections=2,no_output_directory_created=True,protected=before,
     inputs={n:sha(R/n) for n in ('scripts/test_osd_memory_guards.py','scripts/package_osd_memory.py','scripts/audit_refined.py','scripts/osd_memory_branch.py')}),indent=2),encoding='utf-8')
print('OSD_MEMORY_GUARDS_PASS',target.relative_to(R))
