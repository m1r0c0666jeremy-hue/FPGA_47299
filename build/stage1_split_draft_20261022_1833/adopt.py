"""Adopt the archived, pixel-verified routing alternatives once, with old hashes checked."""
from pathlib import Path
import hashlib,json,re
O=Path(__file__).resolve().parent;R=O.parents[1];P=R/'build/stage1_shared_vertex_20261022'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=json.loads((R/'build/stage1_route_20261022_171017_601880/inputs.json').read_text())
assert all(sha(R/n)==h for n,h in before.items()),'Formal source changed before adoption'
for report in ('stamp_validation.json','private_validation.json'):
    proof=json.loads((O/report).read_text())
    for entry in proof['checks'].values():
        assert sha(R/entry['record'])==entry['record_sha256']
        assert sha((R/entry['record']).with_suffix('.log'))==entry['log_sha256']
        assert sha(R/entry['bench'])==entry['bench_sha256']
        assert all(sha(R/n)==h for n,h in entry['inputs'].items())
    assert all(sha(R/n)==h for n,h in proof['reference_oracle_fixtures'].items())
def edit(s,a,b):
    assert s.count(a)==1,(a,s.count(a))
    return s.replace(a,b)
def change(name,fn):
    path=R/name;old=path.read_text(encoding='utf-8');new=fn(old)
    assert old!=new,name
    path.write_text(new,encoding='utf-8')
for source,name in ((P/'stage1_point.v','stage1_point'),(P/'stage1_validate.v','stage1_validate'),
                    (O/'stage1_regions_shared.v','stage1_regions'),(O/'stage1_render_stamp.v','stage1_render')):
    candidate=source.read_text()
    if name=='stage1_render':candidate=edit(candidate,' wire [10:0] span_lo[0:31],span_hi[0:31];wire [31:0] span_valid=0;\n','')
    change('rtl/color_regions/'+name+'.v',lambda old,candidate=candidate:candidate)

def generator(s):
    s=edit(s,'wire [671:0] area_vertices;','wire [671:0] area_vertices,area_saved_vertices;wire [167:0] area_draft_vertices;')
    s=edit(s,'.metrics_valid(area_metrics_valid));','.metrics_valid(area_metrics_valid),.saved_vertices(area_saved_vertices),.draft_vertices(area_draft_vertices));')
    s=edit(s,'.I_region_vertices(area_vertices)', '.I_region_vertices(area_saved_vertices),.I_region_draft(area_draft_vertices)')
    s=edit(s,'input wire [671:0] I_region_vertices,input wire [15:0]', 'input wire [671:0] I_region_vertices,input wire [167:0] I_region_draft,input wire [15:0]')
    s=edit(s,'stage1_render region_render(', 'stage1_render #(.SPLIT_DRAFT(1)) region_render(')
    return edit(s,'region_label_color,region_ready,region_underrun);','region_label_color,region_ready,region_underrun,I_region_draft,I_area_count,I_draft_count!=0);')
change('scripts/generate_stage1.py',generator)

def geometry(s):
    s=edit(s,"stage1_point dut(clk,rst,start,nr,counts,vertices,px,py,busy,done,im,nm,ds,1'b0,21'd0,21'd0,21'd0,,);",'''wire [4:0] address;wire [20:0] value=vertices>>(address*21);
stage1_point #(.SHARED_VERTEX(1)) dut(.clk(clk),.rst_n(rst),.start(start),.region_count(nr),.counts(counts),.vertices(vertices),
.px(px),.py(py),.busy(busy),.done(done),.inside_mask(im),.near_mask(nm),.distances(ds),.orientation_start(1'b0),.oa(21'd0),.ob(21'd0),.oc(21'd0),.vertex_address(address),.vertex_data(value));''')
    return edit(s,'stage1_validate #(.SHARED(1)) dut(clk,rst,start,nr,counts,vertices,nd,draft,busy,done,passed,error_code,os,oa,ob,oc,od,oq);', '''wire [4:0] address;wire [20:0] value=vertices>>(address*21);
stage1_validate #(.SHARED(1),.SHARED_VERTEX(1)) dut(clk,rst,start,nr,counts,vertices,nd,draft,busy,done,passed,error_code,os,oa,ob,oc,od,oq,address,value);''')
change('scripts/test_stage1_geometry.py',geometry)

def render(s):
    context=next(line for line in s.splitlines() if line.startswith('reg [732:0] contexts'))
    s=edit(s,context+'\n','')
    decl=context+'''\nwire [1:0] split_region=c[1:0];
wire [167:0] split_draft=vertices>>(split_region*168);
wire [671:0] split_mask={{504{1'b0}},{168{1'b1}}}<<(split_region*168);
wire [671:0] split_saved=vertices & ~split_mask;
'''
    s=edit(s,'stage1_render dut(clk,rst,commit,vertices,',decl+'stage1_render #(.SPLIT_DRAFT(1)) dut(clk,rst,commit,split_saved,')
    s=edit(s,'x,y,de,mask,color,label_on,glyph,gx,gy,label_color,ready,underrun);',"x,y,de,mask,color,label_on,glyph,gx,gy,label_color,ready,underrun,split_draft,{1'b0,split_region},1'b1);")
    old=next(line for line in s.splitlines() if '$display("EDGE%0d span' in line)
    new='$display("EDGE%0d cur%d rem%0d q%d r%0d den%0d ys%0d..%0d end%d flags%b",dbg,$signed(ew[15:0]),ew[29:16],$signed(ew[45:30]),ew[59:46],ew[73:60],ew[83:74],ew[93:84],$signed(ew[109:94]),ew[114:110]);end'
    return edit(edit(s,old,new),'dut.bank_row[yy%2]','dut.bank_row[yy%8]')
change('scripts/test_stage1_render.py',render)

def guards(s):
    s=edit(s,'stage1_render dut(clk,rst,commit,vertices,',"reg [2:0] split_region=0;reg split_visible=1;wire [671:0] split_saved={vertices[671:168],168'd0};\nstage1_render #(.SPLIT_DRAFT(1)) dut(clk,rst,commit,split_saved,")
    s=edit(s,'x,y,de,mask,color,label_on,glyph,gx,gy,label_color,ready,underrun);','x,y,de,mask,color,label_on,glyph,gx,gy,label_color,ready,underrun,vertices[167:0],split_region,split_visible);')
    s=edit(s,"initial begin vertices[20:0]", "initial begin vertices[189:168]={10'd77,11'd88};vertices[20:0]")
    s=edit(s,'vertices=0;repeat(5)', 'vertices=0;split_region=3;split_visible=0;repeat(5)')
    return edit(s,'if(dut.fv[20:0]!==',"if(dut.fv[189:168]!=={10'd77,11'd88} || !dut.fd_visible || dut.fd_region!==0 || dut.fd[20:0]!==")
change('scripts/test_stage1_render_guards.py',guards)

coupled=json.loads((O/'coupled_stamp_validation.json').read_text())
tb=R/coupled['output']/'tb.sv';assert sha(tb)==coupled['bench_sha256']
source=tb.read_text().replace('PRIVATE_EDIT_RENDER_POINT_PASS pixels=134400','STAGE1_EDIT_RENDER_PASS point_pixels=134400')
def regions(s):
    start=s.index("    src=r'''")+len("    src=r'''");end=s.index("'''",start)
    s=s[:start]+source+s[end:]
    return edit(s,"'stage1_sequence.v','stage1_regions.v']","'stage1_sequence.v','stage1_regions.v','stage1_render.v']")
change('scripts/test_stage1_regions.py',regions)
change('scripts/test_stage1_footer.py',lambda s:edit(s,"'stage1_osd dut('+OSD_ZERO_ARGS",'''"stage1_osd dut("+OSD_ZERO_ARGS.replace("672'd0,","672'd0,168'd0,",1)'''))
change('scripts/test_stage1_video.py',lambda s:edit(s,'repr(OSD_ZERO_NAMED)', '''repr(".I_region_draft(168'd0),"+OSD_ZERO_NAMED)'''))
def live(s):
    s=edit(s,'wire [671:0] avs;', 'wire [671:0] avs,asaved;wire [167:0] adraft;')
    s=edit(s,'aerr,aserr,ab,at,amv);','aerr,aserr,ab,at,amv,asaved,adraft);')
    return edit(s,'extra="2\'d1,avs,anc,','extra="2\'d1,asaved,adraft,anc,')
change('scripts/test_stage1_live.py',live)
change('scripts/test_stage1_overlay.py',lambda s:edit(s,"stage1_osd dut(2'd2,672'hVERTICES,16'h3333", "stage1_osd dut(2'd2,672'hVERTICES,168'd0,16'h3333"))
change('scripts/test_stage1_region_footer.py',lambda s:edit(s,"stage1_osd dut(umode,672'd0,16'd0", "stage1_osd dut(umode,672'd0,168'd0,16'd0"))
def audit(s):
    s=edit(s,"'stage1_regions':('STAGE1_REGIONS_PASS',('stage1_regions','stage1_point','stage1_validate','stage1_sequence'))", "'stage1_regions':('STAGE1_EDIT_RENDER_PASS point_pixels=134400',('stage1_regions','stage1_point','stage1_validate','stage1_sequence','stage1_render'))")
    return edit(s,"            if prefix=='stage1_ui'", "            if prefix=='stage1_regions' and 'STAGE1_REGIONS_PASS' not in p.with_suffix('.log').read_text():continue\n            if prefix=='stage1_ui'")
change('scripts/audit_stage1.py',audit)
print('ADOPTED_ARCHIVED_ALTERNATIVES; run generator, current-source tests and fresh physical build before delivery')
