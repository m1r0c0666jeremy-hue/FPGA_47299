"""Counterexample: an image aborted in row 622 must not show valid latency."""
import argparse
from refined_testlib import R
ap=argparse.ArgumentParser();ap.add_argument('--after',action='store_true');ap.add_argument('--row624',action='store_true');a=ap.parse_args()
out=R/'build/refined_footer_abort';out.mkdir(exist_ok=True)
candidate=R/'rtl/color_regions/refined_osd.v' if a.after else out/('row624.v' if a.row624 else 'before.v')
if a.after:assert 'I_de && y==625 && x==0' in candidate.read_text(encoding='utf-8')
elif not candidate.exists():
 text=(R/'rtl/color_regions/refined_osd.v').read_text(encoding='utf-8')
 if a.row624:text=text.replace('I_de && y==625 && x==0','I_de && y==624 && x==0')
 else:text=text.replace('I_de && y==625 && x==0','I_de && y==620 && x==0').replace('I_de && y==624 && x==0','I_de && y==620 && x==0')
 candidate.write_bytes(text.encode('utf-8'))
path=R/'scripts/test_refined_v4_ui.py';s=path.read_text(encoding='utf-8')
s=s.replace('palette=[', "cases += [(name,0,0,['色彩高亮 2X   红蓝 180 状态:跟踪中      材料已学习','板内延迟 ----.-ms 落后 ---帧 F:12345678 V:00AF']) for name in ('late_abort','last_pixel_abort')]\npalette=[")
s=s.replace('reg clk=0;', 'reg latency_valid=1;reg clk=0;')
s=s.replace("1'b1,32'd12345,32'd2", "latency_valid,32'd12345,32'd2")
s=s.replace('rst=1;diag=d;', 'rst=1;latency_valid=1;diag=d;')
s=s.replace('@(negedge clk);de=1;end', '@(negedge clk);de=1;if((c==11 && y==622 && x==0)||(c==12 && y==624 && x==2))latency_valid=0;end')
s=s.replace("run('refined_v4_ui_pixels'",f"run('footer_late_abort_{'after' if a.after else 'row624' if a.row624 else 'before'}'")
s=s.replace('PASS 11 states','PASS 13 states')
s=s.replace("[R/'rtl/color_regions'/f'{n}.v' for n in", "[candidate if n=='refined_osd' else R/'rtl/color_regions'/f'{n}.v' for n in")
s=s.replace("'refined_overlay_geometry')])", "'refined_overlay_geometry')],expected_failure=expected_failure)")
exec(compile(s,str(path),'exec'),dict(__file__=str(path),__name__='__main__',candidate=candidate,expected_failure=not a.after))
