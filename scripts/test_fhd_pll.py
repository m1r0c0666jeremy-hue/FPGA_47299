"""Ask TD STA to independently derive both generated PLL frequency sets."""
from pathlib import Path
import datetime,json,re,subprocess,sys
from create_fhd_project import R,load,save
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
out=R/'build'/('fhd_clock_probe_'+stamp);out.mkdir(parents=True)
v=out/'probe.v'
v.write_text('''module fhd_clock_probe(input refclk,reset,output [4:0] q);
wire [4:0] c;wire sl,hl;
fhd_system_pll u_system_pll(refclk,reset,sl,c[0],c[1],c[2]);
fhd_hdmi_pll u_hdmi_pll(c[2],reset || !sl,hl,c[3],c[4]);
genvar i;generate for(i=0;i<5;i=i+1)begin:each
reg [7:0] cnt;always @(posedge c[i] or posedge reset)if(reset)cnt<=0;else cnt<=cnt+1'b1;
assign q[i]=cnt[7];end endgenerate
endmodule
''',encoding='utf-8')
root=load(R/'td_project/target_color_regions_refined.al');root.set('Path',out.as_posix());root.find('Name').text='fhd_clock_probe'
sf=root.find('Source_Files');sf.clear()
import xml.etree.ElementTree as ET
group=ET.SubElement(sf,'Verilog')
for i,p in enumerate([v,R/'rtl/color_regions/fhd_system_pll.v',R/'rtl/color_regions/fhd_hdmi_pll.v',R/'user_source/ip_source/PLL/RTL/ph1p_phy_pll_wrapper_25a56e5ce2f9.v']):
    node=ET.SubElement(group,'File',Path=p.as_posix());info=ET.SubElement(node,'FileInfo')
    for k,val in [('UsedInSyn','true'),('UsedInP&R','true'),('BelongTo','design_1'),('CompileOrder',str(i))]:ET.SubElement(info,'Attr',Name=k,Val=val)
for n in root.find('TOP_MODULE'):n.text='fhd_clock_probe'
project=out/'fhd_clock_probe.al';save(root,project)
sdc=out/'probe.sdc';sdc.write_text('create_clock -name REF50 -period 20.0 [get_ports refclk]\nderive_clocks\n',encoding='utf-8')
t=out/'run.tcl';commands='''if {[catch {
import_device ph1_35p.db -package PH1P35MDG324 -speed 3
open_project {%s} -single_run
elaborate -top fhd_clock_probe
read_sdc {%s}
optimize_rtl
optimize_gate -packarea pll.area
report_timing_summary -file pll.timing
puts "FHD_PLL_STA_COMPLETED"
} message]} {puts stderr $message;exit 1}
exit
'''%(project.as_posix(),sdc.as_posix())
if '--physical' in sys.argv:
    commands=commands.replace('report_timing_summary -file pll.timing','legalize_phy_inst\nplace\nroute\nupdate_timing -mode final\nreport_clock_utilization -file pll_clocks.txt\nreport_timing_summary -file pll.timing')
t.write_text(commands,encoding='utf-8')
with (out/'td.log').open('w',encoding='utf-8') as f:
    p=subprocess.run(['E:/TD 6.2.1/bin/td_commands_prompt.exe',t.as_posix()],cwd=out,stdout=f,stderr=subprocess.STDOUT)
log=(out/'td.log').read_text(encoding='utf-8',errors='replace')
assert p.returncode==0 and 'FHD_PLL_STA_COMPLETED' in log,log[-2000:]
text=(out/'pll.timing').read_text(encoding='utf-8')
report=R/'reports/clocks/pll_sta.txt';report.write_text(text,encoding='utf-8')
print('FHD_PLL_STA_REPORT',report)
expected={'u_hdmi_pll/u_core/u_PH1P_PHY_PLL.clkc[0]':74.25,'u_hdmi_pll/u_core/u_PH1P_PHY_PLL.clkc[1]':371.25,
 'u_system_pll/u_core/u_PH1P_PHY_PLL.clkc[0]':100,'u_system_pll/u_core/u_PH1P_PHY_PLL.clkc[1]':24,
 'u_system_pll/u_core/u_PH1P_PHY_PLL.clkc[2]':60}
rows={name:float(freq) for freq,name in re.findall(r'^\s*clk\d+:\s+([0-9.]+)\s+\d+\s+(\S+)',text,re.M)}
for name,freq in expected.items():
    # STA rounds clock periods to ps, including the upstream derived 60 MHz.
    # Check the period in its reporting units, not a spurious frequency delta.
    assert name in rows and abs(1000/rows[name]-1000/freq)<0.002,(name,rows.get(name),freq)
print('FHD_PLL_STA_PASS',json.dumps(rows))
