"""Native connected resident-age/buffered-triangle advance/reset/overwrite sequence."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_six_class_readout_v1';inv='gf180_phase_inverter_fullroute';texts=[];files={Path(__file__)}
 for name in [cell,inv]:
  folder=BASE/'layout'/name;qp=folder/'qualification.json';q=json.loads(qp.read_text());files.add(qp);assert q['magic_drc_count']==0 and q['lvs_unique']
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for n,h in q.get(key,{}).items():
    pp=folder/n if key=='sha256' else ROOT/n
    if pp.suffix!='.ext':assert sha(pp)==h,n
    files.add(pp)
  if name==cell:
   fp=folder/'flat_cap_qualification.json';fq=json.loads(fp.read_text());files.add(fp);assert fq['flat_lvs_unique'] and not fq['negative_aggregate_branches']
   for n,h in fq['sha256'].items():
    if Path(n).suffix!='.ext':assert sha(ROOT/n)==h,n
    files.add(ROOT/n)
   txt=(folder/(fq['flat_subcircuit']+'_cap.spice')).read_text().replace(fq['flat_subcircuit'],name)
  else:txt=(folder/(name+'_cap.spice')).read_text()
  for ch in re.findall(r'(?m)^\.subckt (\S+)',txt):
   if ch!=name:txt=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(ch)+r'(?![A-Za-z0-9_])',name+'__'+ch,txt)
  texts.append(txt)
 stem=cell+'_nominal_src'+sha(Path(__file__))[:12];rp=BASE/'results'/(stem+'.json');assert not rp.exists();dp=BASE/'results'/(stem+'.dat');models=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix()
 lines=['Native six-class analog accumulation bank',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.lib {prefix}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vreset vreset 0 1.65','Ireference bias 0 21u','Vresetcommand resetcommand 0 PWL(0 3.3 999.99u 3.3 1000u 0 51000u 0)',f'Xresetb resetcommand resetb vdd 0 {inv}',f'Xreset resetb reset vdd 0 {inv}'];cases=[('class1_dominant',[0,100,-50,25,0,75]),('all_negative',[-10,-100,-80,-60,-40,-20]),('class5_dominant',[20,-30,10,0,40,100])];nodes=[]
 for tag,currents in cases:
  for ch,current in enumerate(currents):
   points=['0 0']
   for i in range(10):
    start=1200+5000*i;points.extend([f'{start-.01}u 0',f'{start}u {current*1e-12}',f'{start+9.99}u {current*1e-12}',f'{start+10}u 0'])
   points.append('51000u 0');lines.append(f'Iclass_{tag}_{ch} 0 state_{tag}_{ch} PWL('+ ' '.join(points)+')')
  pins=[f'state_{tag}_{ch}' for ch in range(6)]+[f'output_{tag}_{ch}' for ch in range(6)]+[f'win_{tag}_{ch}' for ch in range(6)];lines.append(f'Xbank_{tag} '+ ' '.join(pins)+f' vreset reset resetb bias vdd 0 {cell}');nodes.extend('v('+p+')' for p in pins)
 lines+=['.control','set numdgt=15','tran .01u 51000u 0 20u','set wr_singlescale','set wr_vecnames','wrdata /workspace/'+dp.relative_to(ROOT).as_posix()+' '+' '.join(nodes),'quit','.endc','.end'];deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135);log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);files.add(lp)
 r={'module_simulation_completed':False,'simulator_returncode':run.returncode,'scope':'Native340MOS18MIM connected six-class analog current bank and native categorical winner selector, one output location, actual extracted interconnect and native reset drivers. Three50ms fixture records, initial1ms reset, ten signed10us current pulses at5ms intervals; external21uA master for21references across3fixture instances. No ideal score output or argmax. Current sources are ideal projection fixtures, not learned16-to6 injectors. State/output values, native one-hot winners and software diagnostic ranking recorded. Reset offsets, routing gain/coupling, near/exact ties and calibrated score accuracy remain unqualified. Native record-done capture, full-frame dense layout/model/population5ms/full-chip acceptance unfinished','native_argmax_implemented':True,'complete_readout_accepted':False}
 try:
  w=np.loadtxt(dp,skiprows=1);files.add(dp);ok=bool(run.returncode==0 and w.shape[1]==55 and np.isfinite(w).all() and abs(w[-1,0]-.051)<1e-12 and 'aborted' not in log.lower());r['module_simulation_completed']=ok
  if ok:
   sample=lambda k,us:float(np.interp(us*1e-6,w[:,0],w[:,k]));r['cases']=[]
   for j,(tag,currents) in enumerate(cases):
    col=18*j+1;initial=[sample(col+i,1100) for i in range(6)];states=[sample(col+i,50999) for i in range(6)];outputs=[sample(col+6+i,50999) for i in range(6)];expected=int(np.argmax(currents));measured=int(np.argmax(outputs));r['cases'].append({'case':tag,'pulse_currents_pa':currents,'record_ms':50,'pulse_count_each_class':10,'initial_post_reset_states_v':initial,'final_states_v':states,'record_state_changes_v':[v-x for v,x in zip(states,initial)],'final_outputs_v':outputs,'expected_current_fixture_winner':expected,'software_measured_output_winner':measured,'fixture_ranking_matches':expected==measured,'final_buffer_errors_v':[v-x for v,x in zip(outputs,states)]})
   
   for j,c in enumerate(r['cases']):
    v=[sample(18*j+13+i,50999) for i in range(6)];expected=c['expected_current_fixture_winner'];c['native_win_voltages_v']=v;c['native_winner_matches_fixture']=bool(v[expected]>2.97 and all(x<.33 for i,x in enumerate(v) if i!=expected))
   r['all_native_readout_fixture_winners_pass']=all(c['native_winner_matches_fixture'] for c in r['cases'])
 except Exception as e:r['postprocess_error']=str(e)
 r['sha256']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)};rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'report':str(rp),**{k:v for k,v in r.items() if k!='sha256'}},indent=2));assert r['module_simulation_completed']
if __name__=='__main__':main()
