"""Project RTL syntax/elaboration; unresolved vendor IP intentionally omitted.

This is not a vendor-IP simulation or a TD build. Functional tests run separately.
"""
from refined_testlib import R,run
modules=sorted(p for p in (R/'rtl/color_regions').glob('*.v') if p.name.startswith(('stable_','refined_','regions_divide.')))
modules += [R/'rtl/04_tracking/target_mailbox.v',R/'rtl/00_top_control/switch_mode_control.v',R/'rtl/09_osd_ui/scaling_logo_rom.v']
run('project_rtl_elaboration','module tb; endmodule',modules,top='criticalwork_top',compile_args=['-i'])
print('REFINED_RTL_ELABORATION_PASS vendor IP omitted; no claim of physical verification')
