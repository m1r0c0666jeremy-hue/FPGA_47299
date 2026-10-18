"""Private cycle-preserving candidate-storage experiment, not production RTL."""
def tracker_asset(s):
    substitutions={
      'reg [127:0] olda,oldb,besta,bestb;':'reg [127:0] olda,oldb;',
      'reg diagnostic_found;reg [127:0] diagnostic_a,diagnostic_b;':'reg diagnostic_found;',
      'besta<=0;bestb<=0;':'',
      'diagnostic_a<=0;diagnostic_b<=0;':'',
      'diagnostic_a<=ca;diagnostic_b<=cb;':'',
      'besta<=ca;bestb<=cb;':'',
    }
    for old,new in substitutions.items():
        assert s.count(old)==1,old;s=s.replace(old,new)
    old='if(pair_index==15)state<=3;else begin pair_index<=pair_index+1\'b1;state<=2;end'
    assert s.count(old)==1
    s=s.replace(old,'''if(pair_index==15)begin
 // stable_capture holds the published candidate bus through tracker done.
 // Select the existing read port instead of retaining four 128-bit copies.
 if(match && (!found || score<bestscore || (score==bestscore && pair_quality>best_quality)))pair_index<=15;
 else if(found)pair_index<=chosen_indices;
 else if(ca[120] && cb[120] && (!diagnostic_found || score<diagnostic_score || (score==diagnostic_score && pair_quality>diagnostic_quality)))pair_index<=15;
 else pair_index<=diagnostic_indices;
 state<=3;
 end else begin pair_index<=pair_index+1'b1;state<=2;end''')
    import re
    for old,new in (('besta','ca'),('bestb','cb'),('diagnostic_a','ca'),('diagnostic_b','cb')):
        s=re.sub(r'\b'+old+r'\b',new,s)
    return s
