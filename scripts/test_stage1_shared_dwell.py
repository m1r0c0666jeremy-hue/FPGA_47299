"""Prove shared dwell against four-counter reference for valid disjoint areas."""
import re
from refined_testlib import R,run
from test_stage1_age_equivalence import BENCH

def main():
    bench=BENCH.replace('stage1_sequence_baseline #','stage1_sequence_gold #')
    bench=bench.replace('da,wa,ea);','da,wa,ea,hold);').replace("db,wb,eb,1'b0);",'db,wb,eb,hold);')
    bench=bench.replace('stage1_sequence #(.CYCLES_PER_MS(MS))','stage1_sequence #(.CYCLES_PER_MS(MS),.ONEHOT_DWELL(1))')
    bench=bench.replace('reg sk=0,pk=0,mk=0,can=1,live=1,changed=0,sample=0;',
       'reg hold=0;reg sk=0,pk=0,mk=0,can=1,live=1,changed=0,sample=0;')
    bench=bench.replace('if({sa,xa,aa,ca,oa,ma,ala,ta,da,wa,ea}!==',
       'if(oa!=0 && (oa & (oa-1))!=0)$fatal(1,"physical one-hot invariant lost");\nif({sa,xa,aa,ca,oa,ma,ala,ta,da,wa,ea}!==')
    bench=bench.replace('for(i=0;i<200000;i=i+1)','for(i=0;i<600000;i=i+1)')
    start=bench.index('mode=rng[1:0];nr=rng[4:2]%5;');end=bench.index('$display(',start)
    bench=bench[:start]+'''mode=rng[1:0]%3;nr=4;draft=rng[5]?0:3;sk=rng[6] && i%31==0;pk=rng[7] && i%37==0;mk=rng[8];can=rng[9];
live=rng[10];changed=rng[11] && rng[12];sample=rng[13] && !changed;
im=rng[16]?4'd0:(4'd1<<rng[15:14]);nm=rng[17]?(im!=0?im:(4'd1<<rng[19:18])):4'd0;
ds={12'd0,rng};hold=mode==2 && i%997<150;end
'''+bench[end:]
    bench=bench.replace('STAGE1_AGE_EQUIVALENCE_PASS','STAGE1_SHARED_DWELL_PASS')
    for period in (1,3):
        run('stage1_shared_dwell_'+str(period),re.sub(r'\bMS\b',str(period),bench),
            [R/'scripts/stage1_sequence_four_dwell_reference.v.txt',R/'rtl/color_regions/stage1_sequence.v'],timeout=300)

if __name__=='__main__':main()
