"""Bounded decision/address protocol test with the existing scalar adapter."""
from pathlib import Path
import hashlib,json,subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/analog_asic/results/decision_scan_v1'
TB=r'''
`timescale 1ns/1ps
module tb;
localparam C=2,H=17,W=40,N=C*H*W;
reg clk=0; always #10 clk=~clk;
reg reset=1,start=0,sready=0,sdone=1,silent=0;
reg [23:0] tag=17;
wire startready,sv,rv,rr,last,hold_result,busy,done;
wire [6:0] channel,page; wire [8:0] y;wire [9:0] x;
wire [19:0] bank;wire [1:0] kind;wire [21:0] forest,aux;
wire bs;wire [2:0] row;wire [7:0] columns;
wire [25:0] addr;wire [23:0] rtag;
integer tick=0;always @(posedge clk) tick<=tick+1;
wire eready=(tick%7)>=3;
wire ev,complete,tag_error,order_error;wire [31:0] payload;wire [23:0] etag;
wire spike=!silent && (((channel*H*W+y*W+x)%11==0) || last);
gf180_analog_decision_scan_v1 #(.CHANNELS(C),.HEIGHT(H),.WIDTH(W)) scan(
.clk(clk),.reset(reset),.start_i(start),.start_ready_o(startready),.bin_tag_i(tag),
.service_valid_o(sv),.service_ready_i(sready),.service_done_i(sdone),
.channel_o(channel),.y_o(y),.x_o(x),.linear_bank_o(bank),.service_kind_o(kind),
.forest_address_o(forest),.auxiliary_forest_address_o(aux),.local_page_address_o(page),
.local_bank_select_o(bs),.local_row_o(row),.column_select_o(columns),
.result_valid_o(rv),.result_ready_i(rr),.result_address_o(addr),.result_bin_tag_o(rtag),
.result_last_o(last),.result_hold_o(hold_result),.busy_o(busy),.done_o(done),.done_ready_i(1'b1));
gf180_analog_scalar_result_packet_v1 packet(
.clk(clk),.reset(reset),.result_valid_i(rv),.result_ready_o(rr),.result_spike_i(spike),
.result_address_i(addr),.result_bin_tag_i(rtag),.result_last_i(last),
.event_valid_o(ev),.event_ready_i(eready),.event_payload_o(payload),.event_completion_o(complete),
.event_bin_tag_o(etag),.tag_mismatch_o(tag_error),.address_order_error_o(order_error));
integer emitted=0,completed=0,next_spike=0;reg [31:0] expected_address;
always @(posedge clk) if(!reset && ev && eready) begin
 if(etag!==tag) $fatal(1,"packet tag");
 if(complete) begin
  if(!silent && emitted!=((N-1)/11+1+(((N-1)%11!=0)?1:0))) $fatal(1,"missing spike before completion");
  if(silent && emitted!=0) $fatal(1,"silent bin emitted spike");
  completed=completed+1;
 end else begin
  if(silent) $fatal(1,"silent bin output");
  expected_address=((next_spike/(H*W))<<19)|(((next_spike/W)%H)<<10)|(next_spike%W);
  if(payload!==expected_address) $fatal(1,"unsorted/wrong spike %d %d",payload,expected_address);
  emitted=emitted+1;
  if(next_spike+11<N) next_spike=next_spike+11;else next_spike=N-1;
 end
end
task run_bin;
integer n,ec,ey,ex,eb,ek,fa,pa;
begin
 @(negedge clk);start=1;
 @(negedge clk);start=0;
 for(n=0;n<N;n=n+1) begin
  while(!sv) @(negedge clk);
  ec=n/(H*W);ey=(n/W)%H;ex=n%W;eb=(ec*((H+7)/8)+(ey/8))*((W+7)/8)+(ex/8);
  ek=(eb==0)?0:(eb<3)?1:(eb<19)?2:3;
  fa=(eb>=19)?((eb-19)*8+(ey%8)):0;pa=(eb>=3&&eb<19)?((eb-3)*8+ey%8):0;
  if(channel!==ec || y!==ey || x!==ex || bank!==eb || kind!==ek || forest!==fa || aux!==(eb*8+ey%8) || page!==pa || bs!==(eb==2) || row!==(ey%8) || columns!==(1<<(ex%8))) $fatal(1,"bad selector %d",n);
  // A done flag left high cannot finish the new service.
  sdone=1;sready=1;@(negedge clk);sready=0;
  repeat(2) begin @(negedge clk);if(rv) $fatal(1,"stale done skipped service");end
  sdone=0;repeat(2) @(negedge clk);sdone=1;
  while(!rv) @(negedge clk);
  if(!hold_result || last!==(n==N-1)) $fatal(1,"hold/last");
  while(!rr) begin
   @(negedge clk);
   if(addr!==((ec<<19)|(ey<<10)|ex)) $fatal(1,"address moved under backpressure");
  end
  @(negedge clk);
 end
 while(!done) @(negedge clk);
 if(tag_error||order_error) $fatal(1,"adapter error");
 @(negedge clk);
 if(!startready) $fatal(1,"scan did not finish");
end endtask
initial begin
 repeat(3) @(negedge clk);reset=0;
 run_bin();if(completed!=1) $fatal(1,"completion not drained");
 silent=1;tag=18;emitted=0;next_spike=0;
 run_bin();if(completed!=2) $fatal(1,"silent completion");
 // Reset aborts a service without emitting a completion.
 start=1;@(negedge clk);start=0;while(!sv) @(negedge clk);
 reset=1;@(negedge clk);reset=0;
 if(!startready || rv || ev) $fatal(1,"reset abort");
 $display("DECISION_SCAN_PASS valid_neurons=2720");$finish;
end
initial begin #2000000;$fatal(1,"timeout");end
endmodule
'''

def main():
    OUT.mkdir(parents=True,exist_ok=True);report=OUT/'simulation.json';assert not report.exists()
    tb=OUT/'tb.sv';tb.write_text(TB)
    sources=[ROOT/'asic/analog/gf180_analog_decision_scan_v1.sv',ROOT/'asic/analog/gf180_analog_scalar_result_packet_v1.sv',tb]
    shell='apt-get update -qq && apt-get install -y -qq iverilog >/dev/null && iverilog -g2012 -s tb -o /tmp/scan '+' '.join('/workspace/'+p.relative_to(ROOT).as_posix() for p in sources)+' && vvp /tmp/scan'
    run=subprocess.run(['docker','run','--rm','--memory','1g','--cpus','1','--volume',f'{ROOT}:/workspace:ro','--entrypoint','bash','eventspikeseg:analog-ngspice47','-lc',shell],capture_output=True,text=True,timeout=180)
    log=run.stdout+run.stderr;(OUT/'simulation.log').write_text(log)
    passed=run.returncode==0 and 'DECISION_SCAN_PASS' in log
    result={'simulation_pass':passed,'returncode':run.returncode,'valid_neuron_results_tested':2720,
            'cases':['partial edge banks','all four native storage service classes','forest rank excludes19local banks','auxiliary address has no exceptions','canonical channel/y/x order','fresh service acknowledgment','output backpressure','last spike then completion drain','all-silent bin','reset abort'],
            'scope':'Categorical selector and scan/result protocol with the existing scalar adapter. No analog service completion producer, physical binding, native recurrence or5ms/accuracy acceptance.',
            'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
    report.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    if not passed:raise SystemExit(run.returncode or 1)

if __name__=='__main__':main()
