"""Create branch-specific tests from previously verified oracles, retain old logs."""
from pathlib import Path
r=Path(__file__).resolve().parents[1]
def read(p):return (r/p).read_text(encoding='utf-8')
def write(p,s):(r/p).write_text(s,encoding='utf-8',newline='\n')
for n in ['detector','tracker','display','store','mailbox','osd']:
 s=read(f'sim/tb_target_{n}.sv').replace('tb_target_'+n,'tb_dualcolor_'+n)
 if n=='detector':s=s.replace('id,ov,om);',"id,ov,om,1'b0,1'b1,8'd1);")
 if n=='tracker':s=s.replace('iv,im,ov,om);',"iv,im,ov,om,1'b0);")
 if n=='display':
  s=s.replace('wire commit,shown,tip;', 'reg pair=0;wire displayed_pair;wire commit,shown,tip;')
  s=s.replace('meta,shown,tip,state);','meta,shown,tip,state,pair,displayed_pair);')
  s=s.replace('data[32]=valid_tip;', 'data[244]=1;data[243]=pair;data[32]=valid_tip;')
  s=s.replace('live=0;#1;', '''pair=1;session=3;#1;if(tip)$fatal(1,"pair stale tip");
  frame(14,2,100,100,1,14);if(tip||cx!=810)$fatal(1,"old session after pair");
  frame(15,3,820,420,1,15);if(!tip||!displayed_pair)$fatal(1,"new pair");
  // A forged matching-session but wrong-pair result must be rejected.
  @(negedge clk);vs=1;de=0;repeat(4)@(negedge clk);vs=0;
  data[243]=0;data[287:256]=16;data[31:0]=16;snapshot=1;
  @(negedge clk);snapshot=0;if(tip||cx!=820)$fatal(1,"wrong pair accepted");
  // Visibility commits at VS even without a DDR snapshot.
  show=1;@(negedge clk);vs=1;repeat(3)@(negedge clk);vs=0;
  if(!shown)$fatal(1,"visibility depends on snapshot");
  live=0;#1;''')
 if n=='osd':
  s=s.replace('state,show,tip,video_ok,ovs', 'state,show,tip,video_ok,meta[243],ovs')
 write(f'sim/tb_dualcolor_{n}.sv',s)
s=read('scripts/test_target_lock.py').replace("out=r/'build/sim/target_lock'","out=r/'build/sim/dualcolor'").replace('target_unit_simulation.log','dualcolor_unit_simulation.log').replace("top='tb_target_'","top='tb_dualcolor_'")
s=s.replace('meta=seq;reason=', 'meta=seq | (1<<235) | (1<<244);reason=')
s=s.replace('im=seq\n', 'im=seq | (session<<235) | (1<<244)\n')
s=s.replace('TARGET_UNIT_TESTS_PASSED','DUALCOLOR_UNIT_TESTS_PASSED')
s=s.replace('-Ptb_target_', '-Ptb_dualcolor_')
write('scripts/test_dualcolor_unit.py',s)
s=read('scripts/test_target_video.py').replace('build/sim/target_lock','build/sim/dualcolor').replace('target_video_simulation.log','dualcolor_video_simulation.log').replace('target_video_cases.json','dualcolor_video_cases.json').replace(".I_meta(256'd0)",".I_pair(1'b0),.I_meta(256'd0)")
write('scripts/test_dualcolor_video.py',s)
print('Prepared adapted legacy regressions in independent files')
