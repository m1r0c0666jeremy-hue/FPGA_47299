"""Retimed ACK for the low-rate recovery telemetry mailbox only."""
CHANGES = [('module target_mailbox #', 'module refined_recovery_mailbox #'),
 ('reg ack1,ack2,req1,req2,req3;', 'reg ack1,ack_mid,ack2,req1,req2,req3;'),
 ('request<=0;payload<=0;ack1<=0;ack2<=0;', 'request<=0;payload<=0;'),
 ('            ack1<=ack;ack2<=ack1;', ''),
 ('    assign S_ready=request==ack2;',
  '    // Two full source-clock periods resolve ACK metastability before use.\n'
  '    // First two samples use falling edges; final rising-edge stage preserves\n'
  '    // source-side payload/request updates and prevents an opposite-edge hold path.\n'
  '    always @(negedge S_clk or negedge S_rst_n)begin\n'
  '        if(!S_rst_n)begin ack1<=0;ack_mid<=0;end\n'
  '        else begin ack1<=ack;ack_mid<=ack1;end\n'
  '    end\n'
  '    always @(posedge S_clk or negedge S_rst_n)\n'
  '        if(!S_rst_n)ack2<=0;else ack2<=ack_mid;\n'
  '    assign S_ready=request==ack2;')]

def recovery_mailbox_asset(source):
    for before,after in CHANGES:
        assert source.count(before)==1,before
        source=source.replace(before,after)
    source=source.replace('Two full source-clock periods resolve ACK metastability before use.', 'A full source-clock period plus a half period resolve ACK before use.')
    source=source.replace('source-side payload/request updates and prevents an opposite-edge hold path.', 'the original source-side request/payload update edge.')
    return source

def recovery_video_asset(source,mailbox):
    needle='target_mailbox #(.WIDTH(39)) recovery_telemetry'
    assert source.count(needle)==1
    return source.replace(needle,'refined_recovery_mailbox #(.WIDTH(39)) recovery_telemetry')+'\n'+recovery_mailbox_asset(mailbox)
