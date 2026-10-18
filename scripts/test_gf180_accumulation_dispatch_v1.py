"""Bounded categorical mapping/handshake simulation for all physical actors."""
from pathlib import Path
import json,random,subprocess
from prepare_gf180_full25_accumulation_dispatch_v1 import PORTS,NAME
from assemble_gf180_accumulation_fabric_ingress_v1 import sha

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/analog_asic/results/accumulation_dispatch_v1'


def main():
    assert not OUT.exists();OUT.mkdir(parents=True)
    prepared_path=ROOT/'artifacts/analog_asic/assembly/full25_accumulation_dispatch_v1/prepared.json'
    prepared=json.loads(prepared_path.read_text())
    source=ROOT/'asic/analog/gf180_analog_accumulation_dispatch_v1.sv'
    rtl=ROOT/'asic/analog'/(NAME+'.sv')
    text='`timescale 1ns/1ps\nmodule tb;\nreg clk=0;always #5 clk=~clk;reg reset=1;\n'
    for direction,width,name in PORTS:
        if name in ['clk','reset']:continue
        total=25*width;kind='reg' if direction=='input' else 'wire'
        text+=kind+' '+(f'[{total-1}:0] ' if total>1 else '')+name+('=0' if kind=='reg' else '')+';\n'
    text+=NAME+' dut(\n'+',\n'.join(f'.{n}({n})' for _,_,n in PORTS)+'\n);\n'
    text+='task tick;begin @(posedge clk);#1;end endtask\n'
    text+='integer requests=0,groups=0,faults=0;\ninitial begin repeat(3) tick();reset=0;\n'
    vectors=[];rng=random.Random(8726)
    for a in prepared['actors']:
        c,h,w=a['shape_chw']; nx=(w+7)//8;ny=(h+7)//8
        cases=[]
        for bank in sorted(set(a['excluded_linear_banks']+[9,19,20,c*ny*nx-1])):
            channel,spatial=divmod(bank,ny*nx);by,bx=divmod(spatial,nx)
            if channel>=c:continue
            cases.append((channel,1,min(w-1,bx*8+7),min(h-1,by*8+3)))
        cases += [(0,c,w-1,h-1),(0,1,0,0),(0,1,0,0)]
        for _ in range(32):
            base=rng.randrange(c);count=rng.randrange(1,min(4,c-base)+1)
            cases.append((base,count,rng.randrange(w),rng.randrange(h)))
        i=a['actor_index'];holes=a['excluded_linear_banks']
        for base,count,x,y in cases:
            tag=groups_tag=len(vectors)+1
            text+=f'while(!group_ready_o[{i}]) tick();\n'
            text+=f'channel_base_i[{i*8} +: 8]={base};lane_count_i[{i*8} +: 8]={count};x_i[{i*10} +: 10]={x};y_i[{i*10} +: 10]={y};bin_tag_i[{i*24} +: 24]={tag};service_done_i[{i}]=1;group_valid_i[{i}]=1;tick();group_valid_i[{i}]=0;\n'
            for lane in range(count):
                channel=base+lane;bank=channel*ny*nx+(y//8)*nx+x//8
                local=holes.index(bank) if bank in holes else -1
                kind=0 if local==0 else 1 if 0<local<3 else 2 if local>=3 else 3
                rank=bank-sum(b<bank for b in holes)
                forest=(rank*8+y%8) if local<0 else 0
                page=(local-3)*8+y%8 if local>=3 else 0
                expected=dict(channel_o=(7,channel),x_o=(10,x),y_o=(9,y),
                              contribution_lane_o=(8,lane),service_bin_tag_o=(24,tag),
                              linear_bank_o=(20,bank),service_kind_o=(2,kind),
                              forest_address_o=(22,forest),local_page_address_o=(7,page),
                              local_bank_select_o=(1,int(local==2)),local_row_o=(3,y%8),
                              column_select_o=(8,1<<(x%8)))
                text+=f'while(!service_valid_o[{i}]) begin tick();if(fault_o[{i}]) $fatal(1,"unexpected fault");end\n'
                for name,(width,value) in expected.items():
                    expr=f'{name}[{i}]' if width==1 else f'{name}[{i*width} +: {width}]'
                    text+=f'if({expr} !== {width}\'d{value}) $fatal(1,"mapping actor={i} lane={lane} field={name}");\n'
                text+=f'repeat(3) begin tick();if(!service_valid_o[{i}] || group_settled_done_o[{i}] || group_ready_o[{i}]) $fatal(1,"request backpressure");end\n'
                text+=f'service_ready_i[{i}]=1;tick();service_ready_i[{i}]=0;\n'
                text+=f'repeat(3) begin tick();if(service_valid_o[{i}] || group_settled_done_o[{i}]) $fatal(1,"stale service done accepted");end\n'
                text+=f'service_done_i[{i}]=0;tick();service_done_i[{i}]=1;tick();requests=requests+1;\n'
                text+=f'if(group_settled_done_o[{i}] !== 1\'b{int(lane==count-1)}) $fatal(1,"early/missing group completion");\n'
            text+='groups=groups+1;tick();\n'
            vectors.append(dict(actor_index=i,channel_base=base,lane_count=count,x=x,y=y,tag=tag))
        # All invalid inputs fail closed, with independent resets between cases.
        invalid=[(0,0,0,0),(0,c+1,0,0),(c,1,0,0),(0,1,w,0),(0,1,0,h)]
        for base,count,x,y in invalid:
            text+=f'reset=1;tick();reset=0;channel_base_i[{i*8} +: 8]={base};lane_count_i[{i*8} +: 8]={count};x_i[{i*10} +: 10]={x};y_i[{i*10} +: 10]={y};group_valid_i[{i}]=1;tick();group_valid_i[{i}]=0;\n'
            text+=f'if(!fault_o[{i}] || service_valid_o[{i}] || group_ready_o[{i}] || group_settled_done_o[{i}]) $fatal(1,"invalid destination did not fail closed");faults=faults+1;reset=1;tick();reset=0;\n'
        text+=f'if(fault_o[{i}] || !group_ready_o[{i}] || service_valid_o[{i}] || group_settled_done_o[{i}]) $fatal(1,"reset safety");\n'
    text+='$display("ACCUMULATION_DISPATCH_V1_PASS groups=%0d requests=%0d faults=%0d",groups,requests,faults);$finish;end\n'
    text+='initial begin #10000000;$fatal(1,"timeout");end\nendmodule\n'
    tb=OUT/'tb.sv';tb.write_text(text,encoding='utf-8')
    vectors_path=OUT/'vectors.json';vectors_path.write_text(json.dumps(vectors,indent=2)+'\n')
    shell='apt-get update -qq && apt-get install -y -qq iverilog >/dev/null && iverilog -g2012 -s tb -o /tmp/dispatch '+ ' '.join('/workspace/'+p.relative_to(ROOT).as_posix() for p in [source,rtl,tb])+' && vvp /tmp/dispatch'
    command=['docker','run','--rm','--memory','1g','--cpus','1','--volume',f'{ROOT}:/workspace:ro','--entrypoint','bash','eventspikeseg:analog-ngspice47','-lc',shell]
    p=subprocess.run(command,capture_output=True,text=True,timeout=180)
    (OUT/'simulation.log').write_text(p.stdout+p.stderr,encoding='utf-8')
    passed=p.returncode==0 and 'ACCUMULATION_DISPATCH_V1_PASS' in p.stdout
    report=dict(simulation_pass=passed,returncode=p.returncode,actors=25,groups=len(vectors),
                service_requests=sum(v['lane_count'] for v in vectors),invalid_input_cases=125,
                cases=['All native local-bank exceptions','Gapped bank9 and forest boundary','Valid image edges',
                       'All-channel groups','Repeated identical destinations','Stable request/backpressure',
                       'Fresh analog completion required','No early group completion','Invalid destinations fail closed','Reset safety'],
                scope='RTL categorical address and handshake simulation for the actual25 actor dimensions; external service completion is a test fixture. Does not simulate analog charge, physical membrane access controls, loaded timing or5ms acceptance.',
                sha256={f.relative_to(ROOT).as_posix():sha(f) for f in [Path(__file__),source,rtl,tb,vectors_path,prepared_path]})
    (OUT/'simulation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['sha256','cases','scope']}))
    if not passed:print((p.stdout+p.stderr)[-5000:]);raise SystemExit(1)


if __name__=='__main__':main()
