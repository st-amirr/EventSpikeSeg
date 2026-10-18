"""Bounded categorical interlock tests; analog durations are not qualified."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/analog_asic/results/page_access_control_v1'
TB=r'''
`timescale 1ns/1ps
module tb;
reg clk=0;always #5 clk=~clk;reg reset=1,valid=0,compute_done=1,dr=0;
reg [1:0] command=0;reg [6:0] row=0;reg [2:0] col=0;
wire ready,done,fault,busy;wire [6:0] address;wire [7:0] sel,cap,capb,mask;
wire rd,re,wr,restore,restoreb,init,initb,cwrite,cwriteb;
gf180_analog_page_access_control_v1 #(.QUIET_CYCLES(2),.ADDRESS_CYCLES(2),.READ_SETUP_CYCLES(2),
.READER_CYCLES(2),.RESTORE_SETUP_CYCLES(2),.COPY_CYCLES(2),.RELEASE_CYCLES(2),.CAPTURE_CYCLES(2),.COMMIT_CYCLES(2)) dut(
.clk(clk),.reset(reset),.command_valid_i(valid),.command_ready_o(ready),.command_i(command),.row_address_i(row),
.column_i(col),.compute_done_i(compute_done),.done_o(done),.done_ready_i(dr),.fault_o(fault),
.page_address_o(address),.page_select_o(sel),.page_read_o(rd),.page_read_enable_o(re),.page_write_o(wr),
.page_restore_o(restore),.page_restoreb_o(restoreb),.compute_init_o(init),.compute_initb_o(initb),
.compute_write_o(cwrite),.compute_writeb_o(cwriteb),.capture_o(cap),.captureb_o(capb),.captured_columns_o(mask),.busy_o(busy));
integer cycles=0,writes=0,captures=0,reads=0;reg [6:0] old_address=0;reg was_active=0;
always @(negedge clk) if(!reset) begin
 cycles=cycles+1;
 if(wr && (rd||re||restore||cwrite||cap!=0)) $fatal(1,"write overlaps read/restore/capture");
 if((address!=old_address) && (rd||re||restore||wr||cap!=0||was_active)) $fatal(1,"unsafe address transition");
 if(re && !rd || restore && !re || cwrite && !restore) $fatal(1,"phase dependency");
 if(restoreb!==!restore || initb!==!init || cwriteb!==!cwrite || capb!==~cap) $fatal(1,"complementary gate");
 if(cap!=0 && ((cap & (cap-1))!=0 || rd||wr||restore)) $fatal(1,"capture isolation");
 if(wr && mask!=8'hff) $fatal(1,"partial row committed");
 if(fault && (wr||rd||re||restore||cwrite||cap!=0||ready||done)) $fatal(1,"fault not closed");
 old_address=address;was_active=rd||re||restore||wr||cap!=0;
 if(wr) writes=writes+1;if(cap!=0) captures=captures+1;if(rd) reads=reads+1;
end
task send(input [1:0] op,input [6:0] target,input [2:0] column);
begin
 @(posedge clk);#1;command=op;row=target;col=column;valid=1;
 while(!ready) begin @(posedge clk);#1;end
 @(posedge clk);#1;valid=0;
end endtask
task finish;
integer n;begin
 while(!done) begin @(posedge clk);#1;if(fault) $fatal(1,"unexpected fault");end
 repeat(3) begin @(posedge clk);#1;if(!done || ready || rd||wr||restore||cap!=0) $fatal(1,"done backpressure");end
 dr=1;@(posedge clk);#1;dr=0;
end endtask
task qualify_compute;
begin
 compute_done=0;repeat(2) begin @(posedge clk);#1;end
 compute_done=1;repeat(2) begin @(posedge clk);#1;end
end endtask
task reset_case;
begin
 valid=0;dr=0;reset=1;@(posedge clk);#1;reset=0;old_address=0;was_active=0;
end endtask
integer c;integer before_writes;
initial begin
 repeat(3) @(posedge clk);#1;reset=0;
 before_writes=writes;
 for(c=0;c<8;c=c+1) begin
   compute_done=1;send(0,7,c);finish();
   // Stale high cannot qualify capture.
   command=1;repeat(3) begin @(posedge clk);#1;if(ready || cap!=0) $fatal(1,"stale compute acknowledgment");end
   qualify_compute();send(1,7,c);finish();
   if(mask!==((1<<(c+1))-1)) $fatal(1,"capture mask");
 end
 if(writes!=before_writes) $fatal(1,"early write");
 send(2,7,0);finish();if(mask!=0 || writes-before_writes!=2) $fatal(1,"row commit width/mask");
 // Read-only operation explicitly discards its working copy, without writes.
 send(0,127,7);finish();send(3,127,7);finish();send(0,8,0);finish();
 qualify_compute();send(1,8,0);finish();
 send(0,9,1);if(!fault) $fatal(1,"row mixing accepted");
 reset_case();send(2,0,0);if(!fault) $fatal(1,"partial commit accepted");
 reset_case();send(0,0,0);finish();send(0,0,1);if(!fault) $fatal(1,"working copy silently overwritten");
 reset_case();send(0,0,0);finish();qualify_compute();send(1,0,1);if(!fault) $fatal(1,"wrong capture column accepted");
 reset_case();send(0,0,0);repeat(5) @(posedge clk);reset_case();
 if(fault || rd||wr||restore||cap!=0 || mask!=0 || !ready) $fatal(1,"reset safety");
 $display("PAGE_ACCESS_INTERLOCK_PASS full_row=8 read_only=1 fault_cases=4");$finish;
end
initial begin #100000;$fatal(1,"timeout");end
endmodule
'''

def main():
    assert not OUT.exists();OUT.mkdir();tb=OUT/'tb.sv';tb.write_text(TB)
    source=ROOT/'asic/analog/gf180_analog_page_access_control_v1.sv'
    shell='apt-get update -qq && apt-get install -y -qq iverilog >/dev/null && iverilog -g2012 -s tb -o /tmp/access /workspace/'+source.relative_to(ROOT).as_posix()+' /workspace/'+tb.relative_to(ROOT).as_posix()+' && vvp /tmp/access'
    p=subprocess.run(['docker','run','--rm','--memory','1g','--cpus','1','--volume',f'{ROOT}:/workspace:ro','--entrypoint','bash','eventspikeseg:analog-ngspice47','-lc',shell],capture_output=True,text=True,timeout=180)
    (OUT/'simulation.log').write_text(p.stdout+p.stderr)
    passed=p.returncode==0 and 'PAGE_ACCESS_INTERLOCK_PASS' in p.stdout
    report=dict(simulation_pass=passed,returncode=p.returncode,
                cases=['safe address changes','read-before-restore-before-copy','no simultaneous read/write/capture','complementary switches','eight isolated analog-holder captures','complete-row commit only','fresh compute completion','done backpressure','read-only discard','row mixing rejected','partial commit rejected','working copy overwrite rejected','wrong capture column rejected','reset abort'],
                scope='Categorical controller using two-clock test durations. Native analog settle/hold/charge accuracy, loaded timings, parallel interference and5ms are not tested. Trained numerical parameters and state are never digital.',
                sha256={f.relative_to(ROOT).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in [source,tb,Path(__file__)]})
    (OUT/'simulation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    if not passed:raise SystemExit(1)

if __name__=='__main__':main()
