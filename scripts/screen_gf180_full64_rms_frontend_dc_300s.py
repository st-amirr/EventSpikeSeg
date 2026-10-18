"""Three native operating points of physically wired full64 RMS/frontend source."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_full64_rms_frontend_v1';d=B/'layout'/cell;src=d/(cell+'.spice');proof=d/'source_exact_graph_qualification.json'
 assert json.loads(proof.read_text())['all_subcircuits_compositionally_equivalent']
 files={Path(__file__),src,proof,d/'reference.spice',d/'first_pass_recovered.log'}
 calibration=B/'results/gf180_formatted_two_channel_energy_v1_nominal_srcd0887bd0b827.json'
 buffer_calibration=B/'results/gf180_high_common_mode_buffer_v1_nominal_src13f24e93708a.json'
 cal=json.loads(calibration.read_text());bc=json.loads(buffer_calibration.read_text())
 assert cal['module_simulation_completed'] and bc['module_simulation_completed']
 rootref=float(np.interp(cal['cases'][0]['root_v'],[c['amplitude_v'] for c in bc['cases']],[c['buffer_v'] for c in bc['cases']]))
 assert abs(rootref-2.412488477821002)<1e-12
 files.update([calibration,buffer_calibration])
 assert re.search(r'Total DRC errors found:\s*0\b',(d/'first_pass_recovered.log').read_text())
 ports=re.search(r'(?m)^\.subckt '+cell+r' ([^\n]+)',src.read_text().replace('\n+',' '))[1].split()
 nodes=[('ca' if int(p[9:])<32 else 'cb') if p.startswith('CANDIDATE') else p for p in ports]
 models=B/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(R).as_posix()
 stem=cell+'_three_native_DC_src'+sha(Path(__file__))[:12];rp=B/'results'/(stem+'.json');assert not rp.exists()
 outputs=[B/'results'/(stem+'_'+s+'.dat') for s in ['zero','half','all']]
 lines=['Connected full64 RMS frontend native DC',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.lib {prefix}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',src.read_text(),'.global VSUBS','Vsub VSUBS 0 0']
 values={'VDD':3.3,'VSS':0,'VBASE':.9,'VZERO':1.2,'PENALTY':1.2,'ROOT_REF':2.412488477821002,'STRENGTH':1.4,'VMIN':1.2,'VMAX':1.8}
 lines +=[f'V_{n} {n} 0 {v}' for n,v in values.items()]
 lines +=['Ireduce REDUCER_BIAS 0 64u','Ifront FRONTEND_BIAS 0 4u','Inf VDD NF_BIAS 1u','Vca ca 0 1.2','Vcb cb 0 1.2','Xparent '+' '.join(nodes)+' '+cell,'.control','set numdgt=15','set wr_singlescale','set wr_vecnames']
 for i,p in enumerate(outputs):
  if i==1:lines+=['alter Vca 2.0']
  if i==2:lines+=['alter Vcb 2.0']
  lines+=['op','wrdata /workspace/'+p.relative_to(R).as_posix()+' v(ROOT) v(RMS_RAW) v(RMS_CLIP) v(ADAPT_AMP) i(V_VDD)']
 lines+=['quit','.endc','.end'];deck=B/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck)
 snap=B/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 p=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','300','ngspice','-b','/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=315)
 log=p.stdout+p.stderr;lp=B/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 r={'module_simulation_completed':False,'simulator_returncode':p.returncode,'simulation_level':'native_actual_source_hierarchy_DC','native_mos_count':2397,'full_physical_qualification_complete':(d/'qualification.json').exists(),'connected_native_RMS_frontend_response_observed':False,'analog_precision_accepted':False,'full_chip_layout_complete':False,'scope':'One300s runtime extension after the initial120s run completed zero and half-active native operating points but timed out during the third point. Same actual geometry, models, bias domains, solver tolerances, three fixtures and frozen reference; no calibration change. Actual extracted physical parent source hierarchy:64 candidate-minus-penalty formatters,64 energy/root receivers, native high-common-mode isolation buffer, offset conversion, clip and strength product. No ideal internal ROOT source. Three DC external candidate fixtures: all1.2V,half2V,all2V; PENALTY1.2V,STRENGTH1.4V,ROOT_REF2.412488477821002V from frozen independent frontend calibration. Separate64uA/4uA/1uA reference domains. Native typical27C/noise disabled, unchanged1e-6 tolerance. DC omits linear routing capacitors; their zero DC current does not alter operating points. This is not a transient, calibrated model amplitude, resident write/sequencing, noise/PVT, full-population5ms or full-chip result. Known gain/offset/settling errors retained.'}
 try:
  rows=[np.loadtxt(p,skiprows=1).reshape(-1) for p in outputs];files.update(outputs)
  r['module_simulation_completed']=bool(p.returncode==0 and all(len(v)==6 and np.isfinite(v).all() for v in rows) and 'aborted' not in log.lower())
  r['cases']=[dict(case=s,root_v=float(v[1]),rms_raw_v=float(v[2]),rms_clip_v=float(v[3]),adapt_amp_v=float(v[4]),supply_power_w=float(-3.3*v[5])) for s,v in zip(['zero','half','all'],rows)]
  r['connected_native_RMS_frontend_response_observed']=bool(r['module_simulation_completed'] and rows[0][1]>rows[1][1]>rows[2][1] and rows[0][3]<rows[1][3]<rows[2][3])
 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(R).as_posix():sha(p) for p in files};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='sha256'},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
