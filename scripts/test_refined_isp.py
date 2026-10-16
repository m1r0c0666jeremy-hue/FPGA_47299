"""Numerical RAW/ISP equivalence and full-width SOF tag alignment."""
from refined_testlib import R,run,literal_fixture
import ast
O=R/'build/sim/refined_isp_models';O.mkdir(parents=True,exist_ok=True)
legacy=R/'scripts/test_stable_isp.py';s=literal_fixture(legacy,'s')
s=s.replace("wire ready,rv", "reg [32:0] tag=33'h11000000f;wire [32:0] raw_tag,detect_tag;reg [32:0] exp_tag0=0,exp_tag1=0;integer rawheads=0;\nwire ready,rv")
s=s.replace('os,ov,ready);','os,ov,ready,tag,raw_tag,detect_tag);')
s=s.replace('if(rs)begin frozen_r=gr;', '''if(rs)begin
if(raw_tag!==(rawheads==0?33'h11000000f:33'h12000000f))$fatal(1,"SOF identity mismatch %h",raw_tag);rawheads=rawheads+1;
frozen_r=gr;''')
s=s.replace('expected[1]=expected[0];','exp_tag1=exp_tag0;exp_tag0=raw_tag;expected[1]=expected[0];')
s=s.replace('#1;if(dv!==', '#1;if(detect_tag!==exp_tag1)$fatal(1,"WB tag latency");if(dv!==')
s=s.replace('gr=f==0?1536:512;', "tag=f==0?33'h11000000f:33'h12000000f;gr=f==0?1536:512;")
s=s.replace('heads!=2)', 'heads!=2 || rawheads!=2)')
ram_text=None
for node in ast.walk(ast.parse(legacy.read_text(encoding='utf-8'))):
 if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='ram' and node.func.attr=='write_text':ram_text=ast.literal_eval(node.args[0])
assert ram_text
ram=O/'line_ram_models.sv';ram.write_text(ram_text,encoding='utf-8')
mods=[R/f'rtl/color_regions/{n}.v' for n in ('stable_isp','stable_awb','stable_packer','refined_demosaic','refined_raw_matrix_3x3_buffer','refined_zhenghe')]
mods += [R/'user_source/hdl_source/isp/demosaic_4x_2_0'/f'{n}.v' for n in ('mipi_to_raw_converter','bilinear_interpolation','line_buffer_demosaic')]
mods += [next((R/'user_source').rglob('data128_96.v')),ram]
run('actual_isp_sof_tags',s,mods,timeout=1800)
