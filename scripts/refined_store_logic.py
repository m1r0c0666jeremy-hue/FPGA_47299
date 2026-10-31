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
    return fixed_bank_asset(s)

def fixed_bank_asset(s):
    """Unroll actual-address bank updates without changing clock semantics."""
    replacements=[
      (' wire [1:0] committing=I_addr>=21000000?3:I_addr>=14000000?2:I_addr>=7000000?1:0;',
       ' wire [3:0] committing_each={I_addr>=21000000,\n  I_addr>=14000000 && I_addr<21000000,\n  I_addr>=7000000 && I_addr<14000000,I_addr<7000000};'),
      ('''  if(I_write && known[committing])begin
   if(I_addr!=expected[committing] || count[committing]>=WORDS)co[committing]=0;
   else if(count[committing]==WORDS-1 && !write_bad[committing])co[committing]=1;
  end''','''  for(i=0;i<4;i=i+1)if(I_write && known[i] && committing_each[i])begin
   if(I_addr!=expected[i] || count[i]>=WORDS)co[i]=0;
   else if(count[i]==WORDS-1 && !write_bad[i])co[i]=1;
  end'''),
      ('''   if(I_write && known[committing])begin
    if(I_addr!=expected[committing] || count[committing]>=WORDS)write_bad[committing]<=1;
    else begin expected[committing]<=expected[committing]+8;count[committing]<=count[committing]+1'b1;end
   end''','''   for(j=0;j<4;j=j+1)if(I_write && known[j] && committing_each[j])begin
    if(I_addr!=expected[j] || count[j]>=WORDS)write_bad[j]<=1;
    else begin expected[j]<=expected[j]+8;count[j]<=count[j]+1'b1;end
   end'''),
      ('I_write && committing==I_bank','I_write && committing_each[I_bank]')]
    for old,new in replacements:
        assert s.count(old)==1,old
        s=s.replace(old,new,1)
    return s
