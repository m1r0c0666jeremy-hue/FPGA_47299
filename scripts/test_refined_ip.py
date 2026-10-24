"""Audit cloned IP, constraints, independent project and active v4 topology."""
from pathlib import Path
import hashlib,json,re
R=Path(__file__).resolve().parents[1]
old=R/'user_source/hdl_source/ph1p35_ddr/ddr2';new=R/'ip/refined_ddr2';differences=[]
for p in sorted(old.rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(old);q=new/rel;assert q.is_file(),rel
 expected=p.read_bytes()
 if rel.as_posix()=='ddr2.v':expected=expected.replace(b'.MC_REORDER("NORMAL")',b'.MC_REORDER("STRICT")');differences.append(rel.as_posix())
 assert q.read_bytes()==expected,rel
assert differences==['ddr2.v']
project=(R/'td_project/target_color_regions_refined.al').read_text(encoding='utf-8')
assert '../ip/refined_ddr2/ddr2.xml' in project and '../user_source/hdl_source/ph1p35_ddr/ddr2/ddr2.xml' not in project
memory=(R/'rtl/color_regions/stable_memory_video_out.v').read_text(encoding='utf-8')
assert 'refined_line_reader u_scaler' in memory and '.I_frame_commit(frame_commit && image_time_valid)' in memory
for text in ('stable_capture #(.V4(1))','stable_frame_store #(.V4(1))','stable_display #(.V4(1))','.WIDTH(768)','.WIDTH(852)'):
 assert text in memory,text
for p in old.rglob('*'):
 if p.suffix.lower() in ('.sdc','.adc'):assert p.read_bytes()==(new/p.relative_to(old)).read_bytes()
report=dict(cloned_files=sum(p.is_file() for p in old.rglob('*')),only_changed_ip_file='ddr2.v',change='MC_REORDER NORMAL -> STRICT',original_and_cloned_constraints_identical=True,production_result_bits=768,production_snapshot_bits=852,reader='refined_line_reader',no_invalid_snapshot_read=True,
 official_reference=dict(path='D:/26_software/TangDynasty/doc/IPUG/IPUG034_PH1P_MIS_IP_Guide.pdf',sha256=hashlib.sha256(Path('D:/26_software/TangDynasty/doc/IPUG/IPUG034_PH1P_MIS_IP_Guide.pdf').read_bytes()).hexdigest(),pages=[17,23,29]))
(R/'reports/refined/ip_and_protocol_audit.json').write_bytes((json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print('REFINED_IP_AND_V4_AUDIT_PASS',report['cloned_files'],'files; only supported reorder configuration changed; all constraints identical')
