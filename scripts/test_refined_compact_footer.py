"""Compare the compact formatter with the preserved pre-change overview."""
from refined_testlib import R,run
import hashlib,json,zipfile

baseline=R/'build/refined_compact_osd_baseline_20261019_091444'
reference=R/'build/sim/refined_compact_footer_reference'
reference.mkdir(parents=True,exist_ok=True)
manifest=json.loads((baseline/'inputs.json').read_text(encoding='utf-8'))
with zipfile.ZipFile(baseline/'before.zip') as archive:
    for name,module in [('refined_osd','compact_reference_osd'),
                        ('refined_footer_program_rom','compact_reference_program_rom')]:
        path=f'rtl/color_regions/{name}.v'
        data=archive.read(path)
        assert hashlib.sha256(data).hexdigest()==manifest[path]
        text=data.decode('utf-8').replace('refined_osd','compact_reference_osd').replace('refined_footer_program_rom','compact_reference_program_rom')
        target=reference/(module+'.v')
        if target.exists():assert target.read_bytes()==text.encode('utf-8')
        else:target.write_bytes(text.encode('utf-8'))
    for name in ('stable_footer_glyph_rom','stable_footer_text_rom','stable_glyph_rom','refined_logo_rom'):
        path=f'rtl/color_regions/{name}.v'
        assert archive.read(path)==(R/path).read_bytes(),path

src=r'''module tb;
reg clk=0;always #5 clk=~clk;
reg rst=0,de=0;reg [767:0] meta=0;reg [31:0] id=0,latency=0,age=0;
reg [2:0] zoom=0,state=0;reg [1:0] mode=0,diag=0;
reg rotate=0,tracking=0,video=0,pair=0,valid=0,lv=0;
wire [23:0] rgb_a,rgb_b;wire va,ha,da,vb,hb,db;
compact_reference_osd original(clk,rst,1'b0,1'b0,de,24'h123456,meta,11'd320,10'd204,zoom,mode,state,tracking,1'b1,video,pair,valid,1'b1,va,ha,da,rgb_a,rotate,2'd0,id,1'b0,lv,latency,age,128'd0,128'd0,39'd0,18'd0);
refined_osd candidate(clk,rst,1'b0,1'b0,de,24'h123456,meta,11'd320,10'd204,zoom,mode,state,tracking,1'b1,video,pair,valid,1'b1,vb,hb,db,rgb_b,rotate,diag,id,1'b0,lv,latency,age,128'd0,128'd0,39'd0,18'd0);
integer n,j,k;reg [31:0] rng=32'h47299;
task randomize_word;begin rng=rng*32'd1664525+32'd1013904223;end endtask
initial begin
repeat(3)@(negedge clk);rst=1;
for(n=0;n<240;n=n+1)begin
 for(j=0;j<24;j=j+1)begin randomize_word;meta[j*32+:32]=rng;end
 randomize_word;id=rng;randomize_word;latency=rng;randomize_word;age=rng;
 case(n%8)
 0:begin latency=0;age=0;end
 1:begin latency=9999999;age=999;end
 2:begin latency=10000000;age=1000;end
 3:begin latency=12345;age=2;end
 endcase
 zoom=n%5;mode=n%4;diag=n%4;state=n%8;
 rotate=n[0];pair=n[1];tracking=n[2];video=n[3];valid=n[4];lv=n[5];
 meta[567:565]=(n%3==0)?0:1+n%4;
 meta[564]=n[1];meta[563:560]=(n%4==0)?0:n%13;
 @(negedge clk);original.x=0;original.y=625;candidate.x=0;candidate.y=625;de=1;
 @(negedge clk);de=0;
 repeat(2400)@(negedge clk);
 if(!original.footer_ready || !candidate.footer_ready)$fatal(1,"formatter deadline case%0d",n);
 for(k=0;k<128;k=k+1)if(original.characters[k]!==candidate.characters[k])
 $fatal(1,"formatter mismatch case%0d char%0d original%h candidate%h",n,k,original.characters[k],candidate.characters[k]);
end
$display("COMPACT_FOOTER_EQUIVALENCE_PASS 240 contexts, 30720 characters; default overview and calibration identical; diagnostic selector ignored; five zooms, states, decimal clamp and invalid latency");$finish;
end endmodule'''
run('compact_footer_equivalence',src,
    [reference/'compact_reference_osd.v',reference/'compact_reference_program_rom.v']+
    [R/'rtl/color_regions'/f'{n}.v' for n in ('refined_osd','stable_glyph_rom','stable_footer_glyph_rom','stable_footer_text_rom','refined_footer_program_rom','refined_logo_rom','refined_overlay_geometry')])
