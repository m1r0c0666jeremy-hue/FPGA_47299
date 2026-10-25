"""Freeze the delivered Chinese UI before changing its generated successor."""
from pathlib import Path
import datetime, hashlib, json, subprocess, zipfile
R=Path(__file__).resolve().parents[1]
names=['scripts/generate_refined_ui.py','scripts/refined_osd.v.txt',
       'assets/osd/anlogic/refined_ui_manifest.json']
names += ['rtl/color_regions/'+n+'.v' for n in ('refined_osd','stable_osd','stable_glyph_rom',
          'stable_footer_glyph_rom','stable_footer_text_rom','refined_footer_program_rom',
          'stable_footer_program_rom','refined_logo_rom','refined_overlay_geometry')]
out=R/'build'/('osd_memory_baseline_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
out.mkdir(exist_ok=False)
hashes={n:hashlib.sha256((R/n).read_bytes()).hexdigest() for n in names}
with zipfile.ZipFile(out/'before.zip','x',zipfile.ZIP_DEFLATED) as z:
    for n in names:z.write(R/n,n)
data=dict(baseline_commit='7df95aabb9fedc7927d03aa6013aa6a9346eb962',
          archive=(out/'before.zip').relative_to(R).as_posix(),inputs=hashes,
          archive_sha256=hashlib.sha256((out/'before.zip').read_bytes()).hexdigest(),
          delivered_bit_sha256='fe6029bb4fd343df1e7757418c1b2540e2c9884d93f27206a9464509bc3586fe')
target=R/'reports/refined/osd_memory_baseline.json'
with target.open('x',encoding='utf-8') as f:json.dump(data,f,indent=2)
print(out)
