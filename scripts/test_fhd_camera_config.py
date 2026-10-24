"""FHD table and unchanged ACK/retry/gain contracts, including real I2C RTL."""
from refined_testlib import R,run,literal_fixture
source=R/'scripts/test_refined_camera.py'
s=literal_fixture(source,'src');stub=literal_fixture(source,'stub')
stub=stub.replace('begin O_iic_busy<=1;step<=0;end',"""begin
 if(!tb.dut.gain_table)case(tb.dut.index)
  30:if(I_wr_data!==32'h0708326c)$fatal(1,"FHD width high");
  31:if(I_wr_data!==32'h8009326c)$fatal(1,"FHD width low");
  32:if(I_wr_data!==32'h040a326c)$fatal(1,"FHD height high");
  33:if(I_wr_data!==32'h380b326c)$fatal(1,"FHD height low");
  120:if(I_wr_data!==32'h0100016c)$fatal(1,"FHD stream-on");
 endcase
 O_iic_busy<=1;step<=0;end""".replace('\n+','\n'))
mods=[R/'rtl/color_regions/refined_camera_config.v']+[R/'user_source/hdl_source/uics500_cfg'/n for n in ('uics500reg_1080p30.v','uics500regAE.v','SC500GainTbl.v')]
for mode in range(6):
 code=s.replace('(CPM)','(10)').replace('(DIV)','(1)').replace('ACK_DRIVER','').replace('STUB',stub)
 run(f'fhd_camera_supervisor_{mode}',code,mods,args=[f'+MODE={mode}'])
code=s.replace('(CPM)','(24000)').replace('(DIV)','(239)').replace('STUB','').replace('ACK_DRIVER',"assign sda=dut.bus.IIC_S==3?1'b0:1'bz;")
run('fhd_camera_real_i2c',code,[*mods,R/'user_source/hdl_source/uics500_cfg/uii2c.v'],args=['+MODE=0'])
