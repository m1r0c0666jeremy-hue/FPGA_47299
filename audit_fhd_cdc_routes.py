"""Read-only physical CDC net report from the saved routed checkpoint."""
from pathlib import Path
import argparse,hashlib,json,subprocess
R=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--attempt',type=Path,required=True)
ap.add_argument('--td',default='E:/TD 6.2.1/bin/td_commands_prompt.exe');a=ap.parse_args()
out=a.attempt.resolve();db=out/'target_color_regions_pr.db'
assert db.is_file(),'routed checkpoint is not available'
script=out/'audit_cdc_routes.tcl';log=out/'cdc_routes.log'
script.write_text('''cd {%s}
if {[catch {
import_device ph1_35p.db -package PH1P35MDG324 -speed 3
open_project {%s} -single_run
import_db {%s}
update_timing -mode final
puts FHD_CDC_NET_REPORT_BEGIN
foreach name {rd_gray desc_wr_gray desc_rd_gray abort_gray} {
 set pattern "u_camera/u_raw_bridge/$name*"
 puts "FHD_CDC_GROUP $pattern"
 report_nets [get_nets $pattern] -connection -pin_display_limit 100 -timing -mode final
}
puts FHD_CDC_GROUP_VENDOR_GRAY
report_nets [get_nets -hier {primary_addr_gray_reg*}] -connection -pin_display_limit 100 -timing -mode final
puts FHD_CDC_NET_REPORT_END
} message]} {puts stderr $message;exit 1}
exit
'''%(out.as_posix(),(out/'target_color_regions_1080p30.al').as_posix(),db.as_posix()),encoding='utf-8')
with log.open('w',encoding='utf-8') as f:
    result=subprocess.run([a.td,script.as_posix()],cwd=out,stdout=f,stderr=subprocess.STDOUT)
text=log.read_text(encoding='utf-8',errors='replace')
ok=result.returncode==0 and 'FHD_CDC_NET_REPORT_END' in text
record=dict(report_created=ok,exit_code=result.returncode,log=str(log),log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
            note='Physical net diagnostics; not a substitute for CDC protocol reasoning or board validation.')
(R/'reports/fhd/cdc_routes.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print('FHD_CDC_PHYSICAL_REPORT',ok,log)
if not ok:raise SystemExit(1)
