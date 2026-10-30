"""Inherited independent video oracle with the actual candidate OSD instantiated."""
from refined_testlib import R
from stage1_test_sources import OSD_ZERO_NAMED
s=(R/'scripts/test_refined_video.py').read_text(encoding='utf-8')
s=s.replace("s=s.replace('stable_osd osd','refined_osd osd')", "s=s.replace('stable_osd osd','stage1_osd osd')\ns=s.replace('stage1_osd osd(', 'stage1_osd osd('+"+repr(".I_region_draft(168'd0),"+OSD_ZERO_NAMED)+")")
# Independent expected palette is red/yellow and blue/purple in this release.
s=s.replace("s=s.replace('stable_osd osd','refined_osd osd')", "s=s.replace('stable_osd osd','refined_osd osd')")
s=s.replace("s=scope['s'];oracle_dir=scope['O']", "s=scope['s'];oracle_dir=scope['O']\ns=s.replace(\"parg?24'hffff40:24'hff6060\",\"parg?24'h6090ff:24'hff6060\").replace(\"parg?24'he080ff:24'h6090ff\",\"parg?24'he080ff:24'hffff40\")")
s=s.replace('rtl/color_regions/refined_osd.v','rtl/color_regions/stage1_osd.v')
s=s.replace('origins=[',"from stage1_test_sources import EXTRA_OSD\nmods += EXTRA_OSD\norigins=[")
s=s.replace("f'{a.reader}_video_","f'stage1_video_")
s=s.replace('build/sim/refined_video_{a.reader}','build/sim/stage1_video')
s=s.replace('REFINED_VIDEO_ALL_PASS','STAGE1_VIDEO_ALL_PASS')
s=s.replace("if d.get('exit_code')==0", "if d.get('fixture_inputs') and d.get('producer_inputs') and all((R/n).is_file() and hashlib.sha256((R/n).read_bytes()).hexdigest()==h for group in (d['fixture_inputs'],d['producer_inputs']) for n,h in group.items()) and d.get('exit_code')==0")
exec(compile(s,str(R/'scripts/test_refined_video.py'),'exec'),{'__name__':'__main__','__file__':__file__})
