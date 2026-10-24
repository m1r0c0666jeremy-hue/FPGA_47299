"""Full RGB/sync comparison: delivered two-ROM UI vs one shared Chinese ROM."""
from refined_testlib import R,run
import hashlib,json,zipfile
b=json.loads((R/'reports/refined/osd_memory_baseline.json').read_text())
archive=R/b['archive'];assert hashlib.sha256(archive.read_bytes()).hexdigest()==b['archive_sha256']
out=R/'build/sim/osd_memory_chinese';out.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(archive) as z:
    data={n:z.read(n) for n in b['inputs']}
assert all(hashlib.sha256(data[n]).hexdigest()==h for n,h in b['inputs'].items())
manifest=json.loads(data['assets/osd/anlogic/refined_ui_manifest.json'])
chars=manifest['characters'];labels=' 红蓝黄紫色AB1'
source=data['rtl/color_regions/refined_osd.v'].decode().replace('\r\n','\n')
original=source.replace('module refined_osd(', 'module chinese_original(')
candidate=source.replace('module refined_osd(', 'module chinese_shared(')
candidate=candidate.replace(' stable_footer_glyph_rom footer_font(I_clk,footer_addr,footer_font_row);\n stable_glyph_rom label_font(I_clk,{label_glyph,label_gy},label_font_row);',
    ' function [7:0] label_id;input [3:0] n;begin label_id=0;case(n)\n'+
    ''.join(f"{i}:label_id=8'd{chars.index(c)};\n" for i,c in enumerate(labels))+
    'endcase end endfunction\n wire [11:0] shared_addr=footer_text?footer_addr:{label_id(label_glyph),label_gy};\n'+
    ' stable_footer_glyph_rom shared_font(I_clk,shared_addr,footer_font_row);\n assign label_font_row=footer_font_row;')
assert 'shared_font' in candidate and ' label_font(' not in candidate
modules=[]
for name,text in [('chinese_original',original),('chinese_shared',candidate)]:
    p=out/(name+'.v');p.write_text(text,encoding='utf-8');modules.append(p)
for name in ('stable_glyph_rom','stable_footer_glyph_rom','stable_footer_text_rom','refined_footer_program_rom','refined_logo_rom','refined_overlay_geometry'):
    p=out/(name+'.v');p.write_bytes(data['rtl/color_regions/'+name+'.v']);modules.append(p)
src=r'''module tb;
reg clk=0;always #5 clk=~clk;reg rst=0,de=0,vs=0,hs=0,rotate=0,pair=0,commit=0;
reg [767:0] meta=0;reg [23:0] rgb=0;wire [23:0] a,b;wire va,ha,da,vb,hb,db;
chinese_original original(clk,rst,vs,hs,de,rgb,meta,11'd0,10'd0,3'd0,2'd1,3'd2,1'b1,1'b1,1'b1,pair,1'b1,1'b1,va,ha,da,a,rotate,2'd0,32'h12345678,commit,1'b1,32'd12345,32'd2,128'd0,128'd0,39'd0,18'd0);
chinese_shared candidate(clk,rst,vs,hs,de,rgb,meta,11'd0,10'd0,3'd0,2'd1,3'd2,1'b1,1'b1,1'b1,pair,1'b1,1'b1,vb,hb,db,b,rotate,2'd0,32'h12345678,commit,1'b1,32'd12345,32'd2,128'd0,128'd0,39'd0,18'd0);
integer f,x,y,n=0;reg checking=0;
always @(posedge clk)begin #1;if(checking)begin
if({va,ha,da,a}!=={vb,hb,db,b})$fatal(1,"shared Chinese mismatch frame%0d xy%0d/%0d",f,x,y);n=n+1;end end
initial begin
meta[255]=1;meta[247]=1;meta[245]=1;meta[246]=1;meta[36:33]=3;meta[415:413]=4;meta[722:721]=1;
meta[141:100]={10'd620,10'd602,11'd1278,11'd1210};
meta[183:142]={10'd20,10'd0,11'd65,11'd0};
repeat(3)@(negedge clk);rst=1;
for(f=0;f<4;f=f+1)begin
pair=f[0];rotate=f[1];meta[567:565]=f==3?2:0;
commit=1;repeat(40)@(negedge clk);commit=0;checking=1;
for(y=0;y<720;y=y+1)for(x=0;x<1280;x=x+1)begin
@(negedge clk);de=1;hs=x<2;vs=0;rgb={8'(x),8'(y),8'(x^y)};
original.x=x;original.y=y;candidate.x=x;candidate.y=y;end
@(negedge clk);de=0;repeat(3)@(negedge clk);checking=0;
end
$display("OSD_SHARED_CHINESE_PASS four complete frames %0d cycles RGB/HS/VS/DE; two pairs, two orientations, labels at boundaries and calibration",n);$finish;
end endmodule'''
run('osd_shared_chinese_equivalence',src,modules,timeout=1800)
