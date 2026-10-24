"""Two complete 1920x1080 RAW/demosaic/AWB/packing frames with 512-word RAMs."""
from refined_testlib import R,run,literal_fixture
s=literal_fixture(R/'scripts/test_stable_isp.py','s')
s=s.replace('y<720','y<1080').replace('x<320','x<480').replace('x==319','x==479')
s=s.replace('460800','1036800').replace('345600','777600')
s=s.replace('wire ready,rv',"reg [32:0] tag=33'h11000000f;wire [32:0] raw_tag,detect_tag;reg [32:0] exp_tag0=0,exp_tag1=0;integer rawheads=0;\nwire ready,rv")
s=s.replace('os,ov,ready);','os,ov,ready,tag,raw_tag,detect_tag);')
s=s.replace('if(rs)begin frozen_r=gr;',"if(rs)begin if(raw_tag!==(rawheads==0?33'h11000000f:33'h12000000f))$fatal(1,\"raw tag\");rawheads=rawheads+1;frozen_r=gr;")
s=s.replace('expected[1]=expected[0];','exp_tag1=exp_tag0;exp_tag0=raw_tag;expected[1]=expected[0];')
s=s.replace('#1;if(dv!==','#1;if(detect_tag!==exp_tag1)$fatal(1,"WB tag latency");if(dv!==')
s=s.replace('gr=f==0?1536:512;',"tag=f==0?33'h11000000f:33'h12000000f;gr=f==0?1536:512;")
s=s.replace('heads!=2)','heads!=2 || rawheads!=2)').replace('STABLE_ISP_PASS','FHD_ISP_PASS')
mods=[R/f'rtl/color_regions/{n}.v' for n in ('stable_isp','stable_awb','stable_packer','refined_demosaic','refined_raw_matrix_3x3_buffer','refined_zhenghe','fhd_line_buffer_demosaic','fhd_isp_line_ram')]
mods += [R/'user_source/hdl_source/isp/demosaic_4x_2_0'/f'{n}.v' for n in ('mipi_to_raw_converter','bilinear_interpolation')]
mods += [next((R/'user_source').rglob('data128_96.v'))]
run('fhd_actual_isp',s,mods,compile_args=['-DFHD_BEHAVIORAL_RAM'])
