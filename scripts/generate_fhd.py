"""Reproduce/check the reviewed FHD RTL from its independent source templates.

This is one fixed, reviewed profile. Geometry changes require editing the
templates and rerunning validation; changing JSON alone cannot silently change
the HDL. Historical generators target other releases and must not be invoked.
"""
from pathlib import Path
import argparse,hashlib,json,shutil
R=Path(__file__).resolve().parents[1]
T=R/'templates/fhd'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');ap.add_argument('--capture',action='store_true',help='maintainer: update templates after reviewed RTL changes');a=ap.parse_args()
    manifest=R/'reports/fhd/template_manifest.json'
    if a.capture:
        paths=[R/'profile_1080p30.json',R/'td_project/target_1080p30.sdc',R/'td_project/target_color_regions_1080p30.al']
        paths+=list((R/'rtl/color_regions').glob('*.v'))+list((R/'rtl/color_regions').glob('*.vh'))
        paths+=[R/'user_source/hdl_source/hdmi_tx.v']
        data={}
        for p in sorted(paths):
            name=p.relative_to(R).as_posix();target=T/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target);data[name]=sha(p)
        manifest.parent.mkdir(parents=True,exist_ok=True);manifest.write_text(json.dumps(data,indent=2),encoding='utf-8')
        print('FHD_TEMPLATES_CAPTURED',len(data));return
    data=json.loads(manifest.read_text(encoding='utf-8'))
    assert all(sha(T/n)==h for n,h in data.items()),'template manifest stale'
    if a.check:
        errors=[n for n,h in data.items() if not (R/n).is_file() or sha(R/n)!=h]
        if errors:raise SystemExit('FHD generated sources differ: '+', '.join(errors))
        print('FHD_GENERATION_CHECK_PASS',len(data));return
    for n in data:
        p=R/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(T/n,p)
    print('FHD_GENERATED',len(data))
if __name__=='__main__':main()
