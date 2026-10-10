from pathlib import Path
r=Path(__file__).resolve().parents[1]
for name in ['controls','display','store','mailbox','detector','tracker','pipeline','osd']:
 s=(r/f'sim/tb_dualcolor_{name}.sv').read_text().replace('tb_dualcolor','tb_candidate')
 if name=='detector':s=s.replace('repeat(200)','repeat(300)')
 if name=='display':
  s=s.replace('wire displayed_pair;', 'wire detection_valid;wire displayed_pair;').replace('pair,displayed_pair);','pair,displayed_pair,detection_valid);')
  s=s.replace('live=0;#1;', '''// A-only matching result must draw candidates but never move the viewport.
  tracking=1;frame(20,3,50,50,0,20);
  if(!detection_valid||tip||cx!=820)$fatal(1,"single candidate moved window or disappeared");
  session=4;#1;if(detection_valid)$fatal(1,"old diagnostic survived session switch");
  frame(21,4,50,50,0,21);if(!detection_valid||tip||cx!=820)$fatal;
  repeat(16)frame(21,4,50,50,0,21);if(detection_valid)$fatal(1,"stale candidate remained visible");
  frame(22,4,50,50,0,22);tracking=0;#1;if(detection_valid)$fatal(1,"stopped candidate visible");
  live=0;#1;''')
 if name=='osd':
  s=s.replace('ode,rgb);','ode,rgb,meta[255]);')
 (r/f'sim/tb_candidate_{name}.sv').write_text(s,encoding='utf-8')
for name in ['unit','detection','full','video','osd','regression']:
 s=(r/f'scripts/test_dualcolor_{name}.py').read_text(encoding='utf-8').replace('dualcolor','candidate').replace('DUALCOLOR','CANDIDATE')
 if name in ['unit','detection','full']:s='from candidate_reference import candidate_meta\n'+s
 if name=='unit':
  s=s.replace("   e.write(f'{meta:064x}","   meta=candidate_meta(groups,w,h,seq,1,0,1,count,fault)\n   e.write(f'{meta:064x}")
 if name=='detection':
  s=s.replace("  n=pack(n,32,1,valid);", "  n=candidate_meta(groups,W,H,seq,stamp,pair,enabled,pixels,fault);valid=bool((n>>32)&1);reason=(n>>33)&15\n  n=pack(n,32,1,valid);")
 if name=='full':
  s=s.replace("  e.write(f'{n:064x}","  n=candidate_meta([a,b],1280,720,seq,1,1,1,1280*720,0)\n  e.write(f'{n:064x}")
 if name in ['video','osd']:
  s=s.replace("'rtl/09_osd_ui/target_osd.v'","'rtl/09_osd_ui/target_diagnostics.v','rtl/09_osd_ui/target_osd.v'")
 if name=='video':s=s.replace(".I_pair(1'b0)",".I_detection_valid(1'b0),.I_pair(1'b0)")
 (r/f'scripts/test_candidate_{name}.py').write_text(s,encoding='utf-8')
