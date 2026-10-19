"""Equivalent repeat schedule without a run-time constant modulus circuit."""
def control_asset(source):
    s=source.replace('module stable_controls #','module refined_controls #')
    s=s.replace('reg [15:0] held;', '''reg [9:0] repeat_age;
 localparam GAIN_SAT_FIRE=((65535-CHORD_WINDOW_MS)%150)==0;
 localparam ZOOM_SAT_FIRE=((65535-CHORD_WINDOW_MS)%600)==0;
 reg [15:0] held;''')
    s=s.replace('ms<=0;held<=0;', 'ms<=0;repeat_age<=0;held<=0;')
    key=' if(tick)begin'
    assert key in s
    s=s.replace(key,''' if(tick)begin
 // Old held is sampled by the action logic on this same edge. After the
 // initial action at CHORD_WINDOW_MS, age149/599 gives precisely150/600 ms.
 if(pressed!=previous || pressed==0 || chord!=0 || consumed ||
    (gesture!=1 && gesture!=4) || held<=CHORD_WINDOW_MS)repeat_age<=0;
 else if(held<65535)begin
 if((gesture==1 && repeat_age==149) || (gesture==4 && repeat_age==599))repeat_age<=0;
 else repeat_age<=repeat_age+1'b1;end''',1)
    old='(held>CHORD_WINDOW_MS && (held-CHORD_WINDOW_MS)%150==0)'
    assert old in s
    s=s.replace(old,'(held>CHORD_WINDOW_MS && (held==65535?GAIN_SAT_FIRE:repeat_age==149))')
    old='(held>CHORD_WINDOW_MS && (held-CHORD_WINDOW_MS)%600==0)'
    assert old in s
    s=s.replace(old,'(held>CHORD_WINDOW_MS && (held==65535?ZOOM_SAT_FIRE:repeat_age==599))')
    old="3:if(!cal_ui)O_diag<=O_diag+1'b1;"
    assert s.count(old)==1
    # Continue consuming the complete chord so it cannot leak brightness,
    # selection or annotation actions, but keep the sole overview selected.
    return s.replace(old,'3:begin end // diagnostic paging removed; consume chord only')
