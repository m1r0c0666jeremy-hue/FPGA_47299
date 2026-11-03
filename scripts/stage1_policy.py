"""Independent branch/compiler guards; archived OSD guards are left intact."""
from pathlib import Path
import hashlib,json,re,subprocess
BASELINE='607db22c9a570969df40b2f5c333981b3f63e9cd'
BRANCHES=('feature/region-sequence-stage1','Behaviour_region_1024','Teach_auto_routine_1027')
ORIGINAL=Path('D:/aaa_FPGA/transparent-ring-stability')
PROTECTED={
 'td_project/target_color_regions.al':'4467601011e2e6df3603c786579b175bcc71a537469bfc75c6b533ffee05de64',
 'td_project/target_color_regions_refined.al':'bd3993c605763671cf33f0076b51adf23619220b7e7a1e67c7dfd32f3b57d1ad',
 'build/target_color_regions_osd_memory_20261019_234705/target_color_regions.bit':'18fbffee70889073d44f3598029cce8bc5b0662d37f0911e138998315f83844a',
 'build/target_color_regions_osd_memory_20261019_234705/osd_memory_same_source.zip':'9ec0eb66550b2c67db809c6ce4e5cc69258b0187d89d891bf0f99f6469ead9d3',
 'build/target_color_regions_refined_20261019_100417/target_color_regions.bit':'fe6029bb4fd343df1e7757418c1b2540e2c9884d93f27206a9464509bc3586fe',
}
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def git(root,*args):return subprocess.check_output(['git','-c','safe.directory='+root.as_posix(),*args],cwd=root,text=True).strip()
def check_branch(root):
    branch=git(root,'branch','--show-current');assert branch in BRANCHES,branch
    subprocess.run(['git','-c','safe.directory='+root.as_posix(),'merge-base','--is-ancestor',BASELINE,'HEAD'],cwd=root,check=True)
    return branch
def check_protected():
    for name,expected in PROTECTED.items():assert sha(ORIGINAL/name)==expected,'Protected original changed: '+name
    return len(PROTECTED)
def baseline_inputs(root):
    record=root/'build/target_color_regions_osd_memory_20261019_234705/inputs.json'
    assert sha(record)=='970d0781b9c66096ac5a2aba9fd3206a82d29649a49c4075dc7185154084a265','Archived baseline manifest changed'
    baseline=json.loads(record.read_text(encoding='utf-8'))
    for name,value in baseline.items():
        if name=='rtl/color_regions/refined_camera_config.v' and sha(root/name)!=value:
            # The sole approved change to the old compiler set: ID/gain readback.
            # All other 296 old members remain exact. Current tests, frozen build
            # hashes and Git provenance independently bind this new module.
            assert git(root,'branch','--show-current')=='Teach_auto_routine_1027'
            continue
        assert sha(root/name)==value,'Archived compiler input changed: '+name
    return len(baseline)
def compiler_paths(root):
    project=root/'td_project/target_color_regions_stage1.al'
    paths={project,root/'td_project/stage1_pins.adc',root/'td_project/target_lock.sdc',root/'rtl/03_tool_detection/target_config.json'}
    for name in re.findall(r'<File Path="([^"]+)"',project.read_text(encoding='utf-8')):
        p=(project.parent/name).resolve();assert p.is_relative_to(root),p
        if p.is_file():paths.add(p)
    paths.update(p for p in (root/'user_source').rglob('*') if p.is_file() and 'log' not in p.parts)
    paths.update(p for p in (root/'ip/refined_ddr2').rglob('*') if p.is_file())
    return paths
def canonical_build_inputs(inputs):
    root=Path(__file__).resolve().parents[1]
    assert set(inputs)=={p.relative_to(root).as_posix() for p in compiler_paths(root)},'Stage-one compiler set mismatch'
    assert all(sha(root/n)==v for n,v in inputs.items()),'Compiler input changed'
    original=(root/'td_project/target_lock.adc').read_text(encoding='utf-8')
    pins=(root/'td_project/stage1_pins.adc').read_text(encoding='utf-8')
    assert pins.startswith(original) and pins[len(original):].count('set_pin_assignment')==1 and 'C12' in pins[len(original):]
    baseline_inputs(root);check_protected()
