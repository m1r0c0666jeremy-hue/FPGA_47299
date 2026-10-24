"""Frozen, timestamped TD build. Only final routed passes can produce a test bit."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,re,shutil,subprocess,sys
from create_fhd_project import R,create,load,save
from refined_build_report import assess
SHA=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--stage',choices=['elaborate','synth','place','full'],default='synth')
    ap.add_argument('--td',default='E:/TD 6.2.1/bin/td_commands_prompt.exe');a=ap.parse_args()
    project=create();root=load(project)
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    out=R/'build'/f'fhd_{a.stage}_{stamp}';out.mkdir(parents=True,exist_ok=False)
    frozen=out/'compiled_source';frozen.mkdir()
    paths={project,R/'td_project/target_lock.adc',R/'td_project/target_1080p30.sdc'}
    for node in root.findall('./Source_Files/*/File'):
        p=(project.parent/node.attrib['Path']).resolve()
        if p.is_file():paths.add(p)
    for directory in ['user_source','ip/refined_ddr2','rtl/color_regions']:
        paths.update(p for p in (R/directory).rglob('*') if p.is_file() and p.suffix not in ('.log',))
    before={p.relative_to(R).as_posix():SHA(p) for p in sorted(paths)}
    for name in before:
        p=frozen/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/name,p)
    (out/'inputs.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
    for node in root.findall('./Source_Files/*/File'):
        old=(project.parent/node.attrib['Path']).resolve();node.set('Path',(frozen/old.relative_to(R)).as_posix())
    root.set('Path',out.as_posix());fp=out/'target_color_regions_1080p30.al';save(root,fp)
    # TD resolves Verilog includes relative to the project/current directory.
    for dest in (out/'fhd_metadata.vh',frozen/'td_project/fhd_metadata.vh'):
        h=R/'rtl/color_regions/fhd_metadata.vh'
        if h.exists():shutil.copyfile(h,dest)
    f=frozen.as_posix();o=out.as_posix()
    lines=[f'set out {{{o}}}',f'cd {{{o}}}','if {[catch {',
      ' import_device ph1_35p.db -package PH1P35MDG324 -speed 3',f' open_project {{{fp.as_posix()}}} -single_run',
      ' elaborate -top criticalwork_top',f' read_adc {{{f}/td_project/target_lock.adc}}',
      f' read_ip_adc -ip ddr2 -file {{{f}/ip/refined_ddr2/src/adc/ddr2.adc}}',
      f' read_sdc {{{f}/td_project/target_1080p30.sdc}}',f' read_sdc -ip ddr2 {{{f}/ip/refined_ddr2/src/sdc/ddr2.sdc}}',
      f' read_sdc -ip w128_d512_fifo {{{f}/user_source/ip_source/w128_d512_fifo/w128_d512_fifo.tcl}}']
    if a.stage!='elaborate':
        lines+=[' optimize_rtl',' set_param gate map_mode area_prior',' set_param gate pack_effort high',
                ' optimize_gate -packarea target_color_regions_gate.area',
                ' report_timing_summary -file target_color_regions_gate.timing']
    if a.stage in ('place','full'):
        lines+=[' set_param place pr_strategy 5',' set_param place max_fanout 128',' set_param route effort normal',
                ' legalize_phy_inst',' place',' report_area -io_info -file target_color_regions_phy.area']
    if a.stage=='full':
        lines+=[' route',' report_area -io_info -file target_color_regions_phy.area',' update_timing -mode final',
                ' report_timing_status -file target_color_regions_phy.ts',' report_timing_summary -file target_color_regions_pr.timing',
                ' report_timing_exception -file target_color_regions_exception.timing',' report_clock_utilization -file fhd_clocks.txt',
                ' set tf [open target_color_regions_phy.ts r]',' set timing [read $tf]',' close $tf',
                ' foreach key {SWNS HWNS} {',r'  if {![regexp [format {%s:\s*([-0-9.]+)ns} $key] $timing whole slack] || $slack < 0} {error "Final timing failed: $key"}',
                ' }',' bitgen -bit target_color_regions_1080p30.bit']
    lines+=[' puts "FHD_BUILD_COMPLETED"','} message]} {puts stderr "FHD_BUILD_FAILED: $message";puts stderr $::errorInfo;exit 1}','exit','']
    script=out/'run.tcl';script.write_text('\n'.join(lines),encoding='utf-8')
    print('FHD_ATTEMPT',out,flush=True)
    env=os.environ.copy();env['PATH']=str(Path(a.td).parent)+os.pathsep+env.get('PATH','')
    with (out/'td.log').open('w',encoding='utf-8') as log:
        p=subprocess.run([a.td,script.as_posix()],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT)
    summary=dict(stage=a.stage,exit_code=p.returncode,inputs_unchanged=all(SHA(frozen/n)==v for n,v in before.items()),
                 working_tree_matches=all((R/n).is_file() and SHA(R/n)==v for n,v in before.items()),td=a.td)
    try:
        if a.stage!='elaborate':summary.update(assess(out,a.stage))
    except Exception as e:summary['assessment_error']=str(e)
    log=(out/'td.log').read_text(encoding='utf-8',errors='replace')
    summary['completed']='FHD_BUILD_COMPLETED' in log and not p.returncode
    summary['deliverable']=bool(a.stage=='full' and summary['completed'] and summary.get('resource_pass') and summary.get('timing_pass') and summary['inputs_unchanged'] and summary['working_tree_matches'])
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print('FHD_RESULT',json.dumps(summary),flush=True)
    if not summary['completed'] or not summary['inputs_unchanged'] or (a.stage!='elaborate' and not summary.get('resource_pass')) or (a.stage=='full' and not summary['deliverable']):return 3
    return 0
if __name__=='__main__':sys.exit(main())
