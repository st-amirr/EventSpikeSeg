"""Bounded categorical tests for sequential analog decision packetization."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/analog_asic/results/scalar_result_packet_v1'
RTL = ROOT / 'asic/analog/gf180_analog_scalar_result_packet_v1.sv'
TB = r'''
`timescale 1ns/1ps
module tb;
reg clk=0; always #10 clk=~clk;
reg reset=1, rv=0, spike=0, last=0, ready=0;
reg [25:0] addr=0; reg [23:0] tag=0;
wire rr, ev, complete, mismatch, order_error;
wire [31:0] payload; wire [23:0] etag;
gf180_analog_scalar_result_packet_v1 dut(
.clk(clk),.reset(reset),.result_valid_i(rv),.result_ready_o(rr),
.result_spike_i(spike),.result_address_i(addr),.result_bin_tag_i(tag),
.result_last_i(last),.event_valid_o(ev),.event_ready_i(ready),
.event_payload_o(payload),.event_completion_o(complete),
.event_bin_tag_o(etag),.tag_mismatch_o(mismatch),.address_order_error_o(order_error));
task rst; begin
 @(negedge clk); reset=1; rv=0; ready=0;
 repeat(2) @(negedge clk); reset=0;
end endtask
task send(input [25:0] a,input s,input l,input [23:0] t); begin
 @(negedge clk); if(!rr) $fatal(1,"result not ready");
 rv=1; addr=a; spike=s; last=l; tag=t;
 @(negedge clk); rv=0;
end endtask
task consume(input [25:0] a,input c,input [23:0] t); begin
 if(!ev || payload!={6'b0,a} || complete!==c || etag!==t)
   $fatal(1,"packet mismatch");
 repeat(5) begin
   @(negedge clk);
   if(!ev || payload!={6'b0,a} || complete!==c || etag!==t || rr)
     $fatal(1,"unstable backpressure");
 end
 ready=1; @(negedge clk); ready=0;
end endtask
integer i;
initial begin
 rst();
 send(0,0,0,7); if(ev) $fatal(1,"nonspike emitted");
 send(1,1,0,7); consume(1,0,7);
 send(2,0,0,7); if(ev) $fatal(1,"nonspike emitted");
 send(3,1,1,7); consume(3,0,7); consume(3,1,7);
 if(!rr || mismatch || order_error) $fatal(1,"bin did not close");
 // A wholly silent bin still emits exactly one completion.
 for(i=0;i<8;i=i+1) send(i,0,i==7,8);
 consume(7,1,8);
 // Single-neuron bin, including the final address bit pattern.
 send(26'h3ffffff,1,1,24'hffffff);
 consume(26'h3ffffff,0,24'hffffff); consume(26'h3ffffff,1,24'hffffff);
 send(0,0,1,0); consume(0,1,0);
 // Changing tag mid-bin fails closed.
 send(0,0,0,20); send(1,1,1,21);
 if(!mismatch || ev || rr) $fatal(1,"tag fault not closed");
 rst(); send(3,0,0,2); send(3,1,1,2);
 if(!order_error || ev || rr) $fatal(1,"duplicate address not closed");
 rst(); send(3,0,0,2); send(2,1,1,2);
 if(!order_error || ev || rr) $fatal(1,"descending address not closed");
 $display("SCALAR_RESULT_PACKET_PASS"); $finish;
end
initial begin #20000; $fatal(1,"timeout"); end
endmodule
'''

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tb = OUT / 'tb.sv'
    assert not (OUT / 'simulation.json').exists(), 'Preserve prior evidence.'
    tb.write_text(TB)
    command = ['docker','run','--rm','--memory','1g','--cpus','1',
               '--volume',f'{ROOT}:/workspace:ro','--entrypoint','bash',
               'eventspikeseg:analog-ngspice47','-lc',
               'apt-get update -qq && apt-get install -y -qq iverilog >/dev/null && '
               'iverilog -g2012 -s tb -o /tmp/result_sim '
               '/workspace/asic/analog/gf180_analog_scalar_result_packet_v1.sv '
               '/workspace/artifacts/analog_asic/results/scalar_result_packet_v1/tb.sv && '
               'vvp /tmp/result_sim']
    run = subprocess.run(command, capture_output=True, text=True, timeout=240)
    log = run.stdout + run.stderr
    (OUT / 'simulation.log').write_text(log)
    passed = run.returncode == 0 and 'SCALAR_RESULT_PACKET_PASS' in log
    report = {'simulation_pass':passed,'returncode':run.returncode,
              'cases':['sparse decisions','backpressure stability','final spike before completion',
                       'all-silent bin completion','single-neuron bin','tag wrap between bins',
                       'tag mismatch fail closed','duplicate address fail closed',
                       'descending address fail closed'],
              'scope':'RTL categorical protocol only. Sampled comparator result, canonical address, full-bin last marker and control producers still require physical binding. No analog accuracy or full-chip service proof.',
              'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [RTL,tb]}}
    (OUT / 'simulation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if not passed: raise SystemExit(run.returncode or 1)

if __name__ == '__main__': main()
