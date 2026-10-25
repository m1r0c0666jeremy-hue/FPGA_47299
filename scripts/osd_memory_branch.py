"""Explicit branch policy for the archived release and the OSD-only successor."""
import subprocess

BASELINE = '7df95aabb9fedc7927d03aa6013aa6a9346eb962'
OPT_BRANCH = 'opt/region-1019-osd-memory'

def check_branch(root):
    def git(*args):
        return subprocess.check_output(['git', '-c', 'safe.directory='+root.as_posix(), *args], cwd=root, text=True).strip()
    branch = git('branch', '--show-current')
    assert branch in ('release/transparent-ring-stability-20261015', 'Region_Recognition_1019', OPT_BRANCH), branch
    if branch != 'release/transparent-ring-stability-20261015':
        git('merge-base', '--is-ancestor', BASELINE, 'HEAD')
    return branch

def check_osd_only(root):
    """All original non-OSD compiler inputs retain their delivered bytes."""
    import hashlib,json
    source=root/'build/refined_route_20261019_100156_645532/inputs.json'
    baseline=json.loads(source.read_text(encoding='utf-8'))
    allowed={'rtl/color_regions/refined_osd.v','rtl/color_regions/refined_footer_program_rom.v',
             'td_project/target_color_regions_refined.al'}
    for name,expected in baseline.items():
        if name not in allowed:
            assert hashlib.sha256((root/name).read_bytes()).hexdigest()==expected,'Non-OSD input changed: '+name
    return len(baseline)-len(allowed)
