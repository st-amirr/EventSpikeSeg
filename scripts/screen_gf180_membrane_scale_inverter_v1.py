"""Extracted-scale-control test using the routed GF180 inverse OTA, resistor network, and scale-current PFET."""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT/'artifacts/analog_asic'
CELL=BASE/'layout/gf180_inverse_amplifier_rf126_guarded'
AMP=CELL/'gf180_inverse_amplifier_rf126_guarded_cap.spice'
MANIFEST=BASE/'results/gf180_membrane_scale_hardware_requirements_v1.json'
SCRIPT=Path(__file__); NAME='gf180_membrane_scale_inverter_screen_v1'
DECK=BASE/'benches'/(NAME+'.spice'); LOG=BASE/'results'/(NAME+'.log'); OUT=BASE/'results'/(NAME+'.json')
VMID=1.6973421760170977; VBIAS=1.35654; VREF=1.6491

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not OUT.exists() and not DECK.exists() and not LOG.exists()
 q=json.loads((CELL/'qualification.json').read_text());assert q['magic_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_drc_count']==0 and q['gds_roundtrip_lvs_unique']
 m=json.loads(MANIFEST.read_text());target=m['all_bank_scale_v_per_model_unit']['dynamic_ratio']
 model=BASE/'pdk/gf180_primitive_source/models/ngspice';prefix='/workspace/'+model.relative_to(ROOT).as_posix()
 lines=[f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.lib {prefix}/sm141064.spice res_typical',f'.include /workspace/{AMP.relative_to(ROOT).as_posix()}','.temp 27','.options method=gear reltol=1e-6 abstol=1e-19 vntol=1e-10 gmin=1e-18','.param sw_stat_global=0 sw_stat_mismatch=0','Vdd vdd 0 3.3','Ireference bias 0 1u','Xreference bias bias vdd vdd pfet_03v3 w=20u l=2u ad=8.8p as=8.8p pd=40.88u ps=40.88u',
       'Vlog vlog 0 PWL(0 0.75 9.99u 0.75 10u '+str(VMID)+' 19.99u '+str(VMID)+' 20u 2.55 35u 2.55)',f'Vbias vbias 0 {VBIAS}',f'Vref ref 0 {VREF}']
 # Real high-poly divider: 18*123um+30um in series against one123um bias leg.
 prev='vlog'
 for i in range(17):
  nxt=f'vin{i}'
  lines.append(f'Xscale_in_{i} {prev} {nxt} 0 ppolyf_u_1k r_width=1u r_length=123u');prev=nxt
 lines.append(f'Xscale_in_17 {prev} buf 0 ppolyf_u_1k r_width=1u r_length=153u')
 lines.append('Xscale_bias vbias buf 0 ppolyf_u_1k r_width=1u r_length=123u')
 lines += ['Xamp buf ref sum gate vdd 0 bias cmp r1 r2 r3 gf180_inverse_amplifier_rf126_guarded','Vdrain drain 0 1.65','Vmeter scale_current drain 0','Mscale scale_current gate vdd vdd pfet_03v3 w=0.42u l=10u','.control','set numdgt=15','tran 2n 30u 0 2n uic']
 for name,t in [('min',5),('median',15),('max',25)]:
  lines += [f'meas tran scale_gate_{name} find v(gate) at={t}u',f'meas tran scale_buf_{name} find v(buf) at={t}u',f'meas tran scale_current_{name} find i(Vmeter) at={t}u']
 lines += ['quit','.endc','.end','']
 DECK.write_text('\n'.join(lines),encoding='utf-8')
 cmd=['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+DECK.relative_to(ROOT).as_posix()]
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=135); log=r.stdout+r.stderr;LOG.write_text(log,encoding='utf-8')
 vals={k:float(v) for k,v in re.findall(r'(?m)^(scale_(?:gate|buf|current)_(?:min|median|max))\s*=\s*([-+0-9.eE]+)',log)}
 complete=r.returncode==0 and len(vals)==9 and all(vals[f'scale_current_{n}']>0 for n in ['min','median','max'])
 ratios={}
 if complete:
  imin,imed,imax=(vals[f'scale_current_{n}'] for n in ['min','median','max'])
  ratios={'min_to_median':imed/imin,'median_to_max':imax/imed,'min_to_max':imax/imin}
 exp=m['all_bank_scale_v_per_model_unit'];want={'min_to_median':exp['p50']/exp['min'],'median_to_max':exp['max']/exp['p50'],'min_to_max':target}
 result={'simulation_completed':complete,'returncode':r.returncode,'simulator':'ngspice 47; typical 27C GF180 models; extracted routed inverse OTA and resistor amplifier with native parasitic capacitance; external extracted resistor primitives in scale divider','target_scale_ratios':want,'measured_current_ratios':ratios,'relative_error_percent':{k:100*(ratios[k]/want[k]-1) for k in ratios},'measurements':vals,'settings':{'scale_control_v':[0.75,VMID,2.55],'divider_bias_v':VBIAS,'opamp_ref_v':VREF,'divider_resistance_lengths_um':{'log_path':[123]*17+[153],'bias_path':[123]},'scale_pfet':'pfet_03v3 w=0.42um l=10um'},'physical_child_qualification':{'inverse_amplifier_gds_drc':q['gds_roundtrip_drc_count'],'inverse_amplifier_gds_lvs_unique':q['gds_roundtrip_lvs_unique']},'scope':'The inverting OTA and resistors come from a routed GDS-qualified extracted child; scale input divider uses native resistor models but is not laid out as a macro. The scale voltage is an ideal source, not a held bank coefficient. No current multiplier, weight injector, membrane update, mismatch/noise/PVT, full layout, original-float inference or 5ms service is qualified.','sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in [SCRIPT,DECK,LOG,AMP,CELL/'qualification.json',MANIFEST]}}
 OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'report':OUT.relative_to(ROOT).as_posix(),'completed':complete,'ratios':ratios,'targets':want,'errors':result['relative_error_percent'],'measurements':vals},indent=2))
 if not complete:raise RuntimeError(log[-3000:])
if __name__=='__main__':main()
