"""Additional real-command snapshot overlap/reset proof; no formal modifications."""
from pathlib import Path
import hashlib,json,sys
O=Path(__file__).resolve().parent;R=O.parents[1];sys.path.insert(0,str(R/'scripts'))
from refined_testlib import run
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=json.loads((O/'source.json').read_text());assert all(sha(O/n)==h for n,h in source['candidates'].items());assert all(sha(R/n)==h for n,h in source['unchanged_formal_inputs'].items())
fixture=R/'build/sim/refined/private_serial_snapshot_v2_stage1_regions_20261024_072320_249298/tb.sv'
s=fixture.read_text();header=s[:s.index('integer comparison_samples=')].replace('stage1_regions_reference #','stage1_regions_frozen #',1)
start=header.index('stage1_render_reference #');end=header.index(';',start)+1;ref=header[start:end]
for name in ('private_saved','counts','closed','state','completed','expected','actual','private_draft','nr','nd'):ref=ref.replace(name+'_ref',name)
header=header[:start]+ref+header[end:]
start=s.index('task frame;');end=s.index('initial begin',start);tasks=s[start:end]
extra=r'''
integer checked=0,pixels=0,windows=0,max_hold=0,hold_cycles=0,i,b,v,old_nd;
reg [839:0] hold_payload;reg pre_check;
always @(posedge clk)begin
 pre_check=rst && dut.snapshot_lock;
 if(rst && commit)begin hold_payload={private_saved,private_draft};hold_cycles=0;if(counts!=0)windows=windows+1;end
 if(pre_check)hold_cycles=hold_cycles+1;
 #1;
 if(pre_check && rst)begin
 if({private_saved,private_draft}!==hold_payload)$fatal(1,"payload changed inside serial snapshot window");
 if(hold_cycles>41)$fatal(1,"copy lock exceeded41 edges since latest commit");
 if(hold_cycles>max_hold)max_hold=hold_cycles;
 checked=checked+1;end
end
always @(posedge clk)begin #2;if(rst && rde)begin
 if({pmask,pcolor,lon,glyph,gx,gy,lcolor,rready,under}!=={mask_ref,pixel_ref,label_ref,glyph_ref,gx_ref,gy_ref,label_color_ref,ready_ref,under_ref})$fatal(1,"snapshot overlap active pixels differ %0d/%0d",rx,ry);
 if(!rready || under)$fatal(1,"overlap missed active row deadline");pixels=pixels+1;end end

task equivalent;begin
 if({nr,nd,revision,counts,closed,state,completed,occupied,expected,actual,muted,alarm,trend,distance,dwell,ee,se,busy,live,metrics_valid}!=={nr_ref,nd_ref,revision_ref,counts_ref,closed_ref,state_ref,completed_ref,occupied_ref,expected_ref,actual_ref,muted_ref,alarm_ref,trend_ref,distance_ref,dwell_ref,ee_ref,se_ref,busy_ref,live_ref,metrics_valid_ref})$fatal(1,"deferred transaction did not converge to F");
 for(b=0;b<nr;b=b+1)for(v=0;v<counts[b*4+:4];v=v+1)if(private_saved[b*168+v*21+:21]!==private_saved_ref[b*168+v*21+:21])$fatal(1,"saved transaction data differ");
 for(v=0;v<nd;v=v+1)if(private_draft[v*21+:21]!==private_draft_ref[v*21+:21])$fatal(1,"draft transaction data differ");
 end endtask

task snapshot_words;begin
 if(picture.fc!==reference_picture.fc)$fatal(1,"committed counts differ");
 for(b=0;b<4;b=b+1)for(v=0;v<reference_picture.fc[b*4+:4];v=v+1)begin
 if(reference_picture.fd_visible && b==reference_picture.fd_region)begin
 if(picture.state_line_mem[672+v][20:0]!==reference_picture.fd[v*21+:21])$fatal(1,"snapshot draft word differs");end
 else if(picture.state_line_mem[640+b*8+v][20:0]!==reference_picture.fv[b*168+v*21+:21])$fatal(1,"snapshot saved word differs");end
 end endtask

task begin_snapshot;begin
 // Actual stage1_osd resets x/y at VS before frame_commit.
 rx=0;ry=0;rde=0;commit=1;geometry_commit=1;@(posedge clk);#2;
 if(dut.snapshot_count!=40 || picture.snapshot_index!=0)$fatal(1,"snapshot was not started atomically");
 @(negedge clk);commit=0;geometry_commit=0;
 end endtask

task finish_snapshot;begin
 for(i=0;i<40;i=i+1)begin @(posedge clk);#2;if(dut.snapshot_count!=39-i)$fatal(1,"copy hold length differs");end
 @(negedge clk);@(posedge clk);#2;equivalent;snapshot_words;@(negedge clk);
 end endtask

task scan;integer yy,xx;begin
 repeat(10000)@(negedge clk);if(!rready || under)$fatal(1,"10000-clock first-row deadline failed");
 for(yy=0;yy<624;yy=yy+1)for(xx=0;xx<1650;xx=xx+1)begin @(negedge clk);rx=xx<1280?xx:0;ry=yy;rde=xx<1280;end
 @(negedge clk);rde=0;end endtask

task clean;begin
 @(negedge clk);rst=0;commit=0;geometry_commit=0;rde=0;down=0;c2=0;c3=0;c4=0;cancel=0;mode=1;
 repeat(3)@(negedge clk);rst=1;repeat(3)@(negedge clk);end endtask

task close_until_done;begin
 @(negedge clk);c3=1;@(negedge clk);c3=0;wait(dut.validated);@(negedge clk);
 if(!reference_controller.validated)$fatal(1,"pre-deferral genuine validation engines differ");
 end endtask

initial begin
 meta[255]=1;meta[247]=1;meta[32]=1;meta[415:413]=4;meta[242:235]=1;meta[244]=1;meta[559:544]=16'h1234;
 clean;record(100,100);frame(300,100);down=1;@(negedge clk);down=0;
 @(negedge clk);c2=1;@(negedge clk);c2=0;old_nd=nd;begin_snapshot;
 if(nd!=old_nd || nd_ref!=old_nd+1)$fatal(1,"point request was not deferred");finish_snapshot;
 if(nd!=2 || private_draft[41:21]!={10'd100,11'd300})$fatal(1,"press-locked point changed while deferred");scan;
 $display("SERIAL_OVERLAP_CASE_PASS pending_point");
 clean;record(100,100);record(300,100);record(200,250);close_until_done;
 if(!dut.passed)$fatal(1,"expected successful real validation");begin_snapshot;
 if(!dut.validation_pending || !busy || nr!=0 || nr_ref!=1)$fatal(1,"successful validation was not retained");finish_snapshot;
 if(nr!=1 || nd!=0 || counts!=3)$fatal(1,"deferred save lost");scan;
 $display("SERIAL_OVERLAP_CASE_PASS successful_validation");
 record(140,140);record(160,140);record(150,160);close_until_done;
 if(dut.passed || dut.validation_error!=3)$fatal(1,"expected contained-region failure");begin_snapshot;
 if(!dut.validation_pending || !busy)$fatal(1,"failure not retained");finish_snapshot;
 if(nr!=1 || nd!=3 || ee!=3)$fatal(1,"deferred validation failure changed semantics");
 $display("SERIAL_OVERLAP_CASE_PASS failed_validation");
 @(negedge clk);c4=1;@(negedge clk);c4=0;old_nd=nd;begin_snapshot;
 if(nd!=old_nd || nd_ref!=old_nd-1)$fatal(1,"undo not deferred");finish_snapshot;
 key(4);key(4);if(nd!=0)$fatal(1,"clear draft setup failed");
 @(negedge clk);c4=1;@(negedge clk);c4=0;begin_snapshot;
 if(nr!=1 || nr_ref!=0)$fatal(1,"delete not deferred");finish_snapshot;if(nr!=0)$fatal(1,"delete lost");
 $display("SERIAL_OVERLAP_CASE_PASS undo_delete");
 clean;record(100,100);frame(300,100);down=1;@(negedge clk);down=0;
 @(negedge clk);c2=1;@(negedge clk);c2=0;begin_snapshot;
 repeat(7)@(negedge clk);begin_snapshot;finish_snapshot;
 if(nd!=2)$fatal(1,"recommit lost queued point");
 $display("SERIAL_OVERLAP_CASE_PASS recommit");
 clean;record(100,100);begin_snapshot;repeat(7)@(negedge clk);rst=0;repeat(3)@(negedge clk);rst=1;repeat(80)@(negedge clk);
 if(nr!=0 || nd!=0 || dut.snapshot_count!=0 || dut.validation_pending || busy || pmask!=0)$fatal(1,"reset in copy did not clear controls");
 record(500,300);@(negedge clk);begin_snapshot;finish_snapshot;
 if(nd!=1 || private_draft[20:0]!={10'd300,11'd500})$fatal(1,"copy reset recovery lost new point");
 $display("SERIAL_OVERLAP_CASE_PASS copy_reset_recovery");
 clean;record(100,100);record(300,100);record(200,250);close_until_done;begin_snapshot;
 if(!dut.validation_pending)$fatal(1,"pending reset setup failed");repeat(5)@(negedge clk);rst=0;repeat(3)@(negedge clk);rst=1;repeat(80)@(negedge clk);
 if(nr!=0 || nd!=0 || dut.validation_pending || busy || alarm || pmask!=0)$fatal(1,"reset replayed old pending validation");
 $display("SERIAL_OVERLAP_CASE_PASS pending_validation_reset");
 if(pixels!=1597440 || max_hold!=41 || windows<8)$fatal(1,"coverage incomplete pixels%0d hold%0d windows%0d",pixels,max_hold,windows);
 $display("SERIAL_SNAPSHOT_OVERLAP_PASS cases=7 pixels=%0d checks=%0d windows=%0d max_hold=%0d",pixels,checked,windows,max_hold);$finish;
 end
endmodule
'''
bench=header+tasks+extra
modules=[R/'rtl/color_regions'/(n+'.v') for n in ('stage1_arith','stage1_point','stage1_segment','stage1_validate','stage1_sequence')]+[O/n for n in ('stage1_regions.v','stage1_render.v','stage1_regions_frozen.v','stage1_render_reference.v')]
out=run('private_serial_snapshot_overlap_v2',bench,modules,timeout=1800)
rp=R/'reports/refined/regression'/(out.name+'.json');d=json.loads(rp.read_text());assert d['exit_code']==0
assert all(sha(R/n)==h for n,h in source['unchanged_formal_inputs'].items())
with (O/'overlap_validation_v2.json').open('x',encoding='utf-8') as f:json.dump(dict(status='PRIVATE_OVERLAP_PROTOCOL_PASSED_NOT_ADOPTED',record=rp.relative_to(R).as_posix(),record_sha256=sha(rp),log_sha256=sha(rp.with_suffix('.log')),producer_sha256=sha(Path(__file__)),fixture=fixture.relative_to(R).as_posix(),fixture_sha256=sha(fixture),frame_coordinate_source='rtl/color_regions/stage1_osd.v:261',frame_coordinate_source_sha256=sha(R/'rtl/color_regions/stage1_osd.v'),inputs=d['inputs'],bench=(out/'tb.sv').relative_to(R).as_posix(),bench_sha256=sha(out/'tb.sv'),scope='Real key/editor and genuine validator completion; at most41 blocked edges including commit,40 subsequent copy clocks. Queued point/undo/delete and success/failure validation converge to frozen F. Snapshot bytes match frozen F renderer over1597440 active pixels. Recommit and mid-copy/pending reset recover. Preparation timing differs; no formal/resource/physical credit.'),f,indent=2)
print('PRIVATE_SERIAL_SNAPSHOT_ADVERSARIAL_PROTOCOL_PASS',flush=True)
