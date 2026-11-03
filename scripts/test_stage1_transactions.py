"""Cancellation at each automatic-save edge and renderer snapshot atomicity."""
from refined_testlib import R,run
from test_stage1_rect import BASE
import hashlib,json

def main():
    src=BASE.replace('initial begin','integer phase,fault,before_revision;\ninitial begin',1)+r'''

for(phase=1;phase<=2;phase=phase+1)for(fault=0;fault<5;fault=fault+1)begin
 rst=0;@(negedge clk);rst=1;mode=1;cancel=0;session=1;meta[242:235]=1;meta[719:704]=7;meta[559:544]=16'h1234;
 repeat(5)@(negedge clk);record(100,100);before_revision=revision;
 frame(300,250);down=1;@(negedge clk);down=0;@(negedge clk);c2=1;@(negedge clk);c2=0;
 if(dut.edit_request!=1)$fatal(1,"missing point stage");
 commit=1;
 if(phase==2)begin @(negedge clk);if(dut.edit_request!=2)$fatal(1,"missing auto-save stage");end
 case(fault)0:cancel=1;1:mode=0;2:session=2;3:meta[719:704]=8;4:rst=0;endcase
 @(negedge clk);commit=0;cancel=0;repeat(4)@(negedge clk);
 if(nr!=0 || (fault==4?nd!=0:nd!=phase))$fatal(1,"cancel changed payload/count phase%0d fault%0d nr%0d nd%0d",phase,fault,nr,nd);
 if(fault!=4 && revision!=before_revision+phase-1)$fatal(1,"cancel published revision");
end
rst=0;@(negedge clk);rst=1;mode=1;session=1;meta[242:235]=1;meta[719:704]=7;meta[559:544]=16'h1234;
repeat(5)@(negedge clk);record(300,250);frame(100,100);down=1;@(negedge clk);down=0;@(negedge clk);c2=1;
@(negedge clk);c2=0;commit=1;@(negedge clk);@(negedge clk);@(negedge clk);commit=0;
if(nr!=1 || nd!=0 || saved[41:0]!={10'd250,11'd300,10'd100,11'd100})$fatal(1,"auto-save snapshot result");
$display("STAGE1_TRANSACTIONS_PASS ten-cancel-edges/three-save-snapshots/atomic-payload-count-revision");$finish;end endmodule'''
    source=R/'scripts/test_stage1_rect.py';before=hashlib.sha256(source.read_bytes()).hexdigest()
    out=run('stage1_transactions',src,[R/'rtl/color_regions'/n for n in ('stage1_regions.v','stage1_sequence.v','stage1_render.v')],timeout=120)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==before
    record=R/'reports/refined/regression'/(out.name+'.json');data=json.loads(record.read_text());data['fixture_inputs']['scripts/test_stage1_rect.py']=before
    record.write_text(json.dumps(data,indent=2),encoding='utf-8')

if __name__=='__main__':main()
