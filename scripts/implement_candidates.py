"""One-time migration from dualcolor to independent candidate diagnostics."""
from pathlib import Path
r=Path(__file__).resolve().parents[1]
def edit(rel,changes):
 p=r/rel;s=p.read_text(encoding='utf-8')
 for old,new in changes:
  assert old in s,(rel,old)
  s=s.replace(old,new)
 p.write_text(s,encoding='utf-8',newline='\n')
edit('rtl/10_memory_video_out/memory_video_out.v',[
 ('wire active_pair,active_show,tip_valid,video_ok','wire detection_valid;\n    wire active_pair,active_show,tip_valid,video_ok'),
 ('.O_meta(active_meta),.O_show(active_show)', '.O_detection_valid(detection_valid),.O_meta(active_meta),.O_show(active_show)'),
 ('.I_pair(active_pair),.I_state(active_status)', '.I_detection_valid(detection_valid),.I_pair(active_pair),.I_state(active_status)')])
edit('scripts/target_osd_template.v.txt',[
 ('output reg O_vs,O_hs,O_de,output reg [23:0] O_rgb','output reg O_vs,O_hs,O_de,output reg [23:0] O_rgb,input wire I_detection_valid'),
 ('wire overlay=I_show&&I_tip_valid&&I_video_ok&&y<624;','wire overlay=I_show&&I_detection_valid&&I_video_ok&&y<624;\n wire panel=I_show&&I_video_ok&&(I_state==1||I_state==2||I_state==3);'),
 ('wire av= ax1', 'wire av=I_meta[247]&&I_meta[245]&& ax1'),
 ('wire bv= bx1', 'wire bv=I_meta[247]&&I_meta[246]&& bx1'),
 ('wire tv=tx>=0','wire tv=I_tip_valid&&tx>=0'),
 (',600)',',518)'),(',576)',',494)'),
 ('reg text_on,brand,label_bg;','reg text_on,brand,label_bg;\n wire [23:0] count_a,count_b;wire [11:0] fill_a,fill_b;\n target_diagnostics u_diag(I_clk,I_rst_n,I_meta[203:184],I_meta[223:204],I_meta[230:224],I_meta[254:248],count_a,count_b,fill_a,fill_b);\n reg [23:0] count_digits;reg [11:0] fill_digits;reg [2:0] color_status;\n wire [3:0] diagnosis=!I_detection_valid?4\'d9:!I_meta[247]?4\'d1:I_tip_valid?4\'d11:I_meta[36:33]!=0?I_meta[36:33]:4\'d10;'),
 ('glyph=@SPACE@;gx=0;','count_digits=0;fill_digits=0;color_status=0;\n  glyph=@SPACE@;gx=0;'),
 ('end else if(overlay) begin', '''end else if(panel&&x>=8&&x<848&&y>=544&&y<616) begin
   text_on=1;label_bg=1;column=(x-8)/24;gx=(x-8)%24;gy=(y-544)%24;
   if(y<592) begin
    count_digits=y<568?count_a:count_b;fill_digits=y<568?fill_a:fill_b;
    if(!I_detection_valid) color_status=0;
    else if(!I_meta[247]) color_status=1;
    else if((y<568?I_meta[203:184]:I_meta[223:204])==0) color_status=2;
    else if((y<568?I_meta[203:184]:I_meta[223:204])<@AREA_MIN@ || (y<568?I_meta[203:184]:I_meta[223:204])>@AREA_MAX@) color_status=3;
    else if(y<568?I_meta[245]:I_meta[246]) color_status=5;
    else color_status=4;
    case(column) @DIAG_ROW@ 0:glyph=y<568?@A@:@B@;endcase
    if(column>=4&&column<=9) glyph=I_detection_valid?@ZERO@+((count_digits>>((9-column)*4))&24'hf):@DASH@;
    if(column>=14&&column<=16) glyph=I_detection_valid?@ZERO@+((fill_digits>>((16-column)*4))&12'hf):@DASH@;
    if(column>=19&&column<=22) begin column=column-19;@COLOR_STATUS@ end
   end else begin
    case(column) @DIAG_TITLE@ endcase
    if(column>=3&&column<=10) begin
     column=column-3;
     if(diagnosis==2) begin
      if(I_meta[203:184]==0&&I_meta[223:204]==0) begin case(column) @MISSING_BOTH@ endcase end
      else if(I_meta[203:184]==0) begin case(column) @MISSING_A@ endcase end
      else begin case(column) @MISSING_B@ endcase end
     end else begin @DIAG_REASONS@ end
    end
   end
  end else if(overlay) begin'''),
 ('overlay&&cross_on','overlay&&I_tip_valid&&cross_on'),('overlay&&outline','overlay&&I_tip_valid&&outline'),
 ('overlay&&red','overlay&&av&&red'),('overlay&&blue','overlay&&bv&&blue')])
edit('scripts/generate_target.py',[
 ("static=labels+", "diagnoses=['','帧无效','缺少双色','面积不符','填充不足','间距不符','尖端越界','位移或帧号异常','采集溢出','等待结果','确认中','已锁定']\ncolor_states=['待结果','帧无效','无像素','面积不符','填充不足','候选']\nstatic=diagnoses+color_states+['诊断：A像素： 填充：%缺少A缺少B']+labels+"),
 ("replacements={'@SPACE@'", "replacements={'@AREA_MIN@':str(cfg['area_min']),'@AREA_MAX@':str(cfg['area_max']),\n'@DIAG_ROW@':case_text('像素：',1)+'\\n'+case_text('填充：',11)+'\\n'+case_text('%',17),'@DIAG_TITLE@':case_text('诊断：'),\n'@COLOR_STATUS@':multi(color_states,'color_status'),'@DIAG_REASONS@':multi(diagnoses,'diagnosis'),\n'@MISSING_A@':case_text('缺少A'),'@MISSING_B@':case_text('缺少B'),'@MISSING_BOTH@':case_text('缺少双色'),\n'@SPACE@'")])
# Independent project preserves the user's TD-saved dualcolor project as-is.
project=(r/'td_project/target_lock_dualcolor.al').read_text(encoding='utf-8')
project=project.replace('<Name>target_lock_dualcolor</Name>','<Name>target_lock_candidates</Name>')
project=project.replace('<Verilog>','<Verilog>\n<File Path="../rtl/09_osd_ui/target_diagnostics.v"><FileInfo><Attr Name="UsedInSyn" Val="true"/><Attr Name="UsedInP&amp;R" Val="true"/><Attr Name="BelongTo" Val="design_1"/><Attr Name="CompileOrder" Val="130"/></FileInfo></File>',1)
(r/'td_project/target_lock_candidates.al').write_text(project,encoding='utf-8')
s=(r/'scripts/build_target_lock_dualcolor.tcl').read_text().replace('target_lock_dualcolor','target_lock_candidates').replace('TARGET_LOCK_DUALCOLOR','TARGET_LOCK_CANDIDATES')
(r/'scripts/build_target_lock_candidates.tcl').write_text(s,encoding='utf-8')
