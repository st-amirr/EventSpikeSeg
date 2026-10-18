"""Bounded event fanout and settled-completion test for analog actor ingress."""
from pathlib import Path
import hashlib,json,subprocess

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/analog_asic/results/actor_ingress_v2'
TB=r'''
`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;
reg reset=1,enable=0,iv=0,ic=0,sdone=1,bready=0;
reg [31:0] ip=0;reg [23:0] itag=7;
wire ir,gv,bc,busy,terr,ierr;wire [19:0] base,stride;
wire [7:0] channel,lanes;wire [9:0] x,y;wire [23:0] ctag,btag;
integer cycle=0;always @(posedge clk) cycle<=cycle+1;
wire gr=(cycle%5)!=0;
gf180_analog_actor_ingress_v2 dut(
.clk(clk),.reset(reset),.accumulate_enable_i(enable),.graph_valid_i(iv),.graph_ready_o(ir),
.graph_payload_i(ip),.graph_completion_i(ic),.graph_bin_tag_i(itag),
.group_valid_o(gv),.group_ready_i(gr),.group_settled_done_i(sdone),
.weight_address_base_o(base),.weight_lane_stride_o(stride),.output_channel_base_o(channel),
.output_lane_count_o(lanes),.output_x_o(x),.output_y_o(y),.contribution_bin_tag_o(ctag),
.bin_complete_valid_o(bc),.bin_complete_ready_i(bready),.bin_complete_tag_o(btag),
.busy_o(busy),.tag_error_o(terr),.input_error_o(ierr));
integer requests=0,settled=0,ack_count=-1,tap,inch,expect_x,expect_y;
always @(posedge clk) begin
 if(reset) begin requests=0;settled=0;ack_count=-1;end
 else begin
  if(gv && gr) begin
   if(ack_count>=0) $fatal(1,"more than one unsettled group");
   if(requests<18) begin tap=requests%9;inch=0;expect_x=2-tap%3;expect_y=2-tap/3;end
   else if(requests<22) begin
    case(requests-18) 0:tap=0;1:tap=1;2:tap=3;3:tap=4;endcase
    inch=1;expect_x=1-tap%3;expect_y=1-tap/3;
   end else begin tap=(requests-22)%9;inch=0;expect_x=2-tap%3;expect_y=2-tap/3;end
   if(base!==inch*9+tap || stride!==18 || channel!==0 || lanes!==4 || x!==expect_x || y!==expect_y)
     $fatal(1,"bad convolution group %d base%0d tap%0d x%0d y%0d",requests,base,tap,x,y);
   requests=requests+1;ack_count=4;
  end
  if(bc && (requests!=settled)) $fatal(1,"completion passed unsettled analog group");
 end
end
always @(negedge clk) begin
 if(reset) sdone=1;
 else if(ack_count>=0) begin
  if(ack_count==4) sdone=1; // stale high must not finish this group
  if(ack_count==3 || ack_count==2) sdone=0;
  if(ack_count==1) begin sdone=1;settled=settled+1;end
  ack_count=ack_count-1;
 end
end
task send(input [31:0] payload,input completion,input [23:0] tag);
begin
 @(negedge clk);iv=1;ip=payload;ic=completion;itag=tag;
 while(!ir) @(negedge clk);
 @(negedge clk);iv=0;
end endtask
task drain(input [23:0] tag);
begin
 while(!bc) @(negedge clk);
 repeat(5) begin
  @(negedge clk);if(!bc || btag!==tag || ir) $fatal(1,"completion backpressure");
 end
 bready=1;@(negedge clk);bready=0;
 if(busy || terr || ierr) $fatal(1,"bad completed bin");
end endtask
initial begin
 repeat(3) @(negedge clk);reset=0;
 iv=1;ip=32'h401;repeat(3) begin @(negedge clk);if(ir||gv) $fatal(1,"accumulation phase gate");end
 iv=0;enable=1;
 send(32'h401,0,7);send(32'h401,0,7); // two identical events must both contribute
 send(32'h80000,0,7); // channel1 boundary, only four spatial taps
 send(0,1,7);drain(7);
 if(requests!=22 || settled!=22) $fatal(1,"lost repeated/boundary events");
 send(0,1,9);drain(9);if(requests!=22) $fatal(1,"empty bin produced contribution");
 send(32'h401,0,10);send(0,1,11);
 if(!terr || ir || gv || bc) $fatal(1,"tag mismatch did not fail closed");
 @(negedge clk);reset=1;@(negedge clk);reset=0;
 send(32'h4,0,12); // x==INPUT_WIDTH is invalid
 if(!ierr || ir || gv || bc) $fatal(1,"range mismatch did not fail closed");
 $display("ACTOR_INGRESS_PASS groups=22 plus_tag_fault_case");$finish;
end
initial begin #200000;$fatal(1,"timeout");end
endmodule
'''

def main():
    OUT.mkdir(parents=True,exist_ok=True);dest=OUT/'simulation.json';assert not dest.exists()
    tb=OUT/'tb.sv';tb.write_text(TB)
    files=[ROOT/'asic/analog/gf180_analog_weight_event_scatter_parallel_v2.sv',ROOT/'asic/analog/gf180_analog_actor_ingress_v2.sv',tb]
    shell='apt-get update -qq && apt-get install -y -qq iverilog >/dev/null && iverilog -g2012 -s tb -o /tmp/ingress '+' '.join('/workspace/'+p.relative_to(ROOT).as_posix() for p in files)+' && vvp /tmp/ingress'
    run=subprocess.run(['docker','run','--rm','--memory','1g','--cpus','1','--volume',f'{ROOT}:/workspace:ro','--entrypoint','bash','eventspikeseg:analog-ngspice47','-lc',shell],capture_output=True,text=True,timeout=180)
    log=run.stdout+run.stderr;(OUT/'simulation.log').write_text(log)
    passed=run.returncode==0 and 'ACTOR_INGRESS_PASS' in log
    result={'simulation_pass':passed,'returncode':run.returncode,'cases':['accumulation-phase gate','duplicate presynaptic packet preservation','all spatial convolution taps','boundary padding mask','weight lane stride and addresses','fresh analog settled acknowledgment','completion after all analog groups settle','completion backpressure','empty bin','bin-tag mismatch fail closed','input-range error fail closed'],
            'scope':'Categorical unit-event to parallel analog-weight group requests. Each group requires all its connected output-channel contributions; their actual native weight read/injection producer remains unbound. No numerical state/weights digitized and no physical/fullmodel/5ms proof.',
            'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    dest.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    if not passed:raise SystemExit(run.returncode or 1)

if __name__=='__main__':main()
