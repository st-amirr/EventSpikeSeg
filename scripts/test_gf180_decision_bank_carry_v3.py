"""Exercise real RTL bank carries at actual25actor boundary configurations."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
OUT=BASE/'results/decision_bank_carry_v3'

def main():
    assert not OUT.exists();OUT.mkdir()
    metadata=BASE/'assembly/full25_decision_control_v2/status.json'
    records=json.loads(metadata.read_text())['actors'];blocks=[]
    for i,r in enumerate(records):
        c,h,w=r['shape_chw'];holes=r['membrane_exceptions']
        literal=f"380'h{sum(v<<(20*k) for k,v in enumerate(holes)):095x}"
        blocks.append(f'''module check_{i}(output reg done=0);
localparam C={c},H={h},W={w},NX=(W+7)/8,NY=(H+7)/8;
reg clk=0;always #5 clk=~clk;reg reset=1;
wire [19:0] bank;wire [6:0] ch;wire [8:0] y;wire [9:0] x;
gf180_analog_decision_scan_v3 #(.CHANNELS(C),.HEIGHT(H),.WIDTH(W),.LOCAL_BANKS({literal})) dut(
.clk(clk),.reset(reset),.start_i(1'b0),.bin_tag_i(24'b0),.service_ready_i(1'b0),.service_done_i(1'b0),
.result_ready_i(1'b1),.done_ready_i(1'b0),.linear_bank_o(bank),.channel_o(ch),.y_o(y),.x_o(x));
integer xs[0:5],ys[0:5],cs[0:3];integer a,b,d,ex,ey,ec,expected,checked=0;
initial begin
 xs[0]=0;xs[1]=6;xs[2]=7;xs[3]=8;xs[4]=W-2;xs[5]=W-1;
 ys[0]=0;ys[1]=6;ys[2]=7;ys[3]=8;ys[4]=H-2;ys[5]=H-1;
 cs[0]=0;cs[1]=1;cs[2]=C-2;cs[3]=C-1;
 repeat(3) @(negedge clk);reset=0;
 for(a=0;a<6;a=a+1) for(b=0;b<6;b=b+1) for(d=0;d<4;d=d+1) begin
   @(negedge clk);
   // Seed a legal publication boundary to exercise carries without a dense
   // whole-population scan. This is explicitly a boundary fixture.
   dut.state=3;dut.channel=cs[d];dut.y=ys[b];dut.x=xs[a];
   dut.channel_base_bank=cs[d]*NY*NX;
   dut.row_base_bank=(cs[d]*NY+(ys[b]>>3))*NX;
   dut.bank=(cs[d]*NY+(ys[b]>>3))*NX+(xs[a]>>3);
   ec=cs[d];ey=ys[b];ex=xs[a];
   if(!(ec==C-1 && ey==H-1 && ex==W-1)) begin
     if(ex==W-1) begin ex=0;if(ey==H-1) begin ey=0;ec=ec+1;end else ey=ey+1;end
     else ex=ex+1;
   end
   @(posedge clk);#1;expected=(ec*NY+(ey>>3))*NX+(ex>>3);
   if(ch!==ec || y!==ey || x!==ex || bank!==expected)
     $fatal(1,"actor{i} carry failed from ch%0d y%0d x%0d",cs[d],ys[b],xs[a]);
   checked=checked+1;
 end
 if(checked!=144) $fatal(1,"coverage");done=1;
end
endmodule
''')
    tb='`timescale 1ns/1ps\n'+''.join(blocks)+'module tb;wire [24:0] done;\n'
    tb+='\n'.join(f'check_{i} actor_{i}(.done(done[{i}]));' for i in range(25))
    tb+='\ninitial begin wait(&done);$display("ALL25_BANK_CARRY_PASS cases=3600");$finish;end\ninitial begin #100000;$fatal(1,"timeout");end\nendmodule\n'
    path=OUT/'tb.sv';path.write_text(tb)
    source=ROOT/'asic/analog/gf180_analog_decision_scan_v3.sv'
    command='apt-get update -qq && apt-get install -y -qq iverilog >/dev/null && iverilog -g2012 -s tb -o /tmp/check /workspace/'+source.relative_to(ROOT).as_posix()+' /workspace/'+path.relative_to(ROOT).as_posix()+' && vvp /tmp/check'
    run=subprocess.run(['docker','run','--rm','--memory','1g','--cpus','1','--volume',f'{ROOT}:/workspace:ro','--entrypoint','bash','eventspikeseg:analog-ngspice47','-lc',command],capture_output=True,text=True,timeout=180)
    (OUT/'simulation.log').write_text(run.stdout+run.stderr)
    passed=run.returncode==0 and 'ALL25_BANK_CARRY_PASS' in run.stdout
    # Keep a frozen parameter snapshot; live job status can change later.
    snapshot=OUT/'actor_parameters.json';snapshot.write_text(json.dumps(records,indent=2)+'\n')
    result=dict(simulation_pass=passed,returncode=run.returncode,actor_configurations=25,boundary_cases=3600,
                scope='Real RTL coordinate/bank carry at legal seeded publication boundaries; covers8-column/8-row carries, partial last rows, channel rollover and final result across all25actual actors. Not full-population runtime, analog service or5ms validation.',
                sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,path,snapshot,Path(__file__)]})
    (OUT/'simulation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    if not passed:raise SystemExit(1)

if __name__=='__main__':main()
