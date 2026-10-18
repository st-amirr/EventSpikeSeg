"""Compare bounded hardware arithmetic to prior addressing for all25 actors."""
from pathlib import Path
import hashlib,json,subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/analog_asic/results/scatter_fixed_kernel_v2b'

def main():
    assert not OUT.exists();OUT.mkdir()
    mapping=ROOT/'artifacts/analog_asic/assembly/full25_actor_ingress_v1/status.json'
    actors=json.loads(mapping.read_text())['actors']
    blocks=[]
    for i,a in enumerate(actors):
        p=a['parameters'];tw=max(1,(p['KERNEL_WIDTH']*p['KERNEL_HEIGHT']-1).bit_length())
        params={k:v for k,v in p.items() if k not in ['INPUT_WIDTH','INPUT_HEIGHT']}
        parameter_text=','.join(f'.{k}({v})' for k,v in params.items())
        blocks.append(f'''module check_{i}(output reg done=0);
reg clk=0;always #5 clk=~clk;
reg reset=1,ev=0,cr=0;reg [7:0] ch=0;reg [9:0] x=0,y=0;reg [1:0] mult=0;reg [23:0] tag=0;
wire [0:0] er[0:1],cv[0:1],ao[0:1],ce[0:1];
wire [7:0] cb[0:1],li[0:1];wire [{tw-1}:0] tap[0:1];
wire [9:0] ox[0:1],oy[0:1];wire [1:0] mo[0:1];wire [23:0] bt[0:1];
''')
        for j,cell in enumerate(['gf180_analog_weight_event_scatter_parallel','gf180_analog_weight_event_scatter_parallel_v2']):
            blocks.append(f'''{cell} #({parameter_text}) dut{j} (
.clk(clk),.reset(reset),.event_valid_i(ev),.event_ready_o(er[{j}]),
.input_channel_i(ch),.input_x_i(x),.input_y_i(y),.multiplicity_i(mult),.bin_tag_i(tag),
.contribution_valid_o(cv[{j}]),.contribution_ready_i(cr),.output_channel_base_o(cb[{j}]),
.input_channel_local_o(li[{j}]),.tap_index_o(tap[{j}]),.output_x_o(ox[{j}]),.output_y_o(oy[{j}]),
.multiplicity_o(mo[{j}]),.bin_tag_o(bt[{j}]),.address_overflow_o(ao[{j}]),.channel_error_o(ce[{j}]));
''')
        blocks.append(f'''integer n=0;integer seed={1701+i};
always @(negedge clk) if(!reset && !done) begin
  if({{er[0],cv[0],cb[0],li[0],tap[0],mo[0],bt[0],ao[0],ce[0]}} !==
     {{er[1],cv[1],cb[1],li[1],tap[1],mo[1],bt[1],ao[1],ce[1]}} ||
     (cv[0] && ({{ox[0],oy[0]}} !== {{ox[1],oy[1]}})))
      $fatal(1,"actor{i} mismatch cycle%0d x%0d y%0d tap%0d",n,x,y,tap[0]);
end
initial begin
 repeat(3) @(posedge clk);#1;reset=0;
 for(n=0;n<6000;n=n+1) begin
   @(posedge clk);#1;
   cr=($unsigned($random(seed))%5)!=0;
   ev=er[0] && ($unsigned($random(seed))%3)!=0;
   if(ev) begin
     ch=$unsigned($random(seed))%{p['INPUT_CHANNELS']};
     case(n%5)
       0:begin x=0;y=0;end
       1:begin x={p['INPUT_WIDTH']-1};y={p['INPUT_HEIGHT']-1};end
       2:begin x=1;y=1;end
       default:begin x=$unsigned($random(seed))%{p['INPUT_WIDTH']};y=$unsigned($random(seed))%{p['INPUT_HEIGHT']};end
     endcase
     mult=$unsigned($random(seed))%4;tag=n;
   end
 end
 @(posedge clk);#1;done=1;
end
endmodule
''')
    tb='`timescale 1ns/1ps\n'+''.join(blocks)+'module tb;wire [24:0] done;\n'
    tb+='\n'.join(f'check_{i} actor_{i}(.done(done[{i}]));' for i in range(25))
    tb+='\ninitial begin wait(&done);$display("ALL25_FIXED_KERNEL_EQUIVALENCE_PASS cycles=150000");$finish;end\ninitial begin #1000000;$fatal(1,"timeout");end\nendmodule\n'
    path=OUT/'tb.sv';path.write_text(tb)
    files=[ROOT/'asic/analog/gf180_analog_weight_event_scatter_parallel.sv',ROOT/'asic/analog/gf180_analog_weight_event_scatter_parallel_v2.sv',path]
    command='apt-get update -qq && apt-get install -y -qq iverilog >/dev/null && iverilog -g2012 -s tb -o /tmp/check '+' '.join('/workspace/'+p.relative_to(ROOT).as_posix() for p in files)+' && vvp /tmp/check'
    run=subprocess.run(['docker','run','--rm','--memory','1g','--cpus','1','--volume',f'{ROOT}:/workspace:ro','--entrypoint','bash','eventspikeseg:analog-ngspice47','-lc',command],capture_output=True,text=True,timeout=180)
    (OUT/'simulation.log').write_text(run.stdout+run.stderr)
    passed=run.returncode==0 and 'ALL25_FIXED_KERNEL_EQUIVALENCE_PASS' in run.stdout
    report=dict(simulation_pass=passed,actors=25,compared_cycles=150000,returncode=run.returncode,
                scope='Categorical arithmetic equivalence for all25 actual model configurations: random events, edges, stride, dilation, groups, multiplicity and backpressure. Not analog or full-model validation.',
                sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files+[mapping,Path(__file__)]})
    (OUT/'simulation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    if not passed:raise SystemExit(1)

if __name__=='__main__':main()
