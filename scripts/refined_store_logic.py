"""Keep bank-ID comparisons outside the actual-write-to-snapshot path."""
def store_asset(source):
    s=source.replace('module stable_frame_store #','module refined_frame_store #')
    key=' reg [3:0] co,hit,eligible;'
    assert key in s
    s=s.replace(key,''' reg [3:0] co,hit,eligible;
 // A bank cannot be selected until its ID comparison flags have settled.
 // Normal complete frames take 172800 writes, far longer than this one clock.
 reg [3:0] id_settled,newer[0:3],predecessor[0:3];wire [3:0] select_co=co & id_settled;
 integer ai,aj;
 always @(posedge I_clk or negedge I_rst_n)begin
 if(!I_rst_n)begin id_settled<=0;for(ai=0;ai<4;ai=ai+1)begin newer[ai]<=0;predecessor[ai]<=0;end end
 else begin
 id_settled<=known;if(I_begin)id_settled[I_bank]<=0;
 if(V4 && I_invalidate)id_settled<=0;
 for(ai=0;ai<4;ai=ai+1)for(aj=0;aj<4;aj=aj+1)begin
 newer[ai][aj]<=$signed(ids[ai]-ids[aj])>0;
 predecessor[ai][aj]<=ids[ai]+32'd1==ids[aj];
 end end end
 ''')
    s=s.replace('eligible[i]=co[i]', 'eligible[i]=select_co[i]')
    s=s.replace('co[1] && (!co[0] || $signed(ids[1]-ids[0])>0)', 'select_co[1] && (!select_co[0] || newer[1][0])')
    s=s.replace('co[3] && (!co[2] || $signed(ids[3]-ids[2])>0)', 'select_co[3] && (!select_co[2] || newer[3][2])')
    s=s.replace('co[hi] && (!co[lo] || $signed(ids[hi]-ids[lo])>0)', 'select_co[hi] && (!select_co[lo] || newer[hi][lo])')
    s=s.replace('found=|co;', 'found=|select_co;')
    s=s.replace("ids[i]+32'd1==ids[newest]",'predecessor[i][newest]')
    return s
