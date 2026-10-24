"""Register frozen-bank history eligibility before the existing grid start."""
def history_asset(source):
    assert source.count('wire history_for_bank=')==1
    result=source.replace('wire history_for_bank=','wire history_for_bank_now=',1)
    anchor=' stable_grid grid(clk,rst_n,'
    assert result.count(anchor)==1
    result=result.replace(anchor,''' // state 0 selects wb; state 1 freezes its history predicate and issues gs.
 // The grid samples both on the next edge. Its candidate/result cycles do not
 // change, and the history command/revision/frame/lifetime checks stay intact.
 reg history_for_bank;
'''+anchor,1)
    declaration=' reg [2:0] state;reg [767:0] packet,waiting_packet;reg waiting_result;'
    assert result.count(declaration)==1
    return result.replace(declaration,declaration+'''
 always @(posedge clk or negedge rst_n)
 if(!rst_n)history_for_bank<=0;
 else if(state==1)history_for_bank<=history_for_bank_now;''',1)
