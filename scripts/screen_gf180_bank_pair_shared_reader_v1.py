"""Native two-bank selected-row write/read through one physically shared replica reader."""
from pathlib import Path
import hashlib,json,re,subprocess
import numpy as np
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_bank_pair_shared_reader_v1';d=B/'layout'/cell;qp=d/'qualification.json';fp=d/'flat_cap_full_qualification.json';q=json.loads(qp.read_text());f=json.loads(fp.read_text());assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'] and f['all_flat_extraction_node_ground_caps_verified'];src=d/(f['flat_subcircuit']+'_fullcap.spice');assert sha(src)==f['sha256'][src.relative_to(R).as_posix()]
 stem=cell+'_native_two_bank_one_reader_v1';rp=B/'results'/(stem+'.json');assert not rp.exists();raw=rp.with_suffix('.raw');deck=B/'benches'/(stem+'.spice');models=B/'pdk/gf180_primitive_source/models/ngspice';pre='/workspace/'+models.relative_to(R).as_posix()
 lines=['Native shared128-state replica reader',f'.include {pre}/design.spice',f'.lib {pre}/sm141064.spice typical',f'.lib {pre}/sm141064.spice mimcap_typical',f'.lib {pre}/sm141064.spice res_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-4 vntol=1e-7 abstol=1e-16 gmin=1e-18',src.read_text(),'.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vss VSS 0 0','Vcm VCM 0 1.2','In0 0 B0_BIAS 1u','In1 0 B1_BIAS 1u','Ip PBIAS 0 1u']
 def wave(n,points):lines.append('V'+n+' '+n+' 0 PWL('+' '.join(f'{t}u {v}' for t,v in points)+')')
 address=[(0,0),(7.9,0),(8,3.3),(25.9,3.3),(26,0),(45.9,0),(46,3.3),(70,3.3)]
 for n in ['A0','A1','A2','BANK_SELECT']:wave(n,address)
 wave('WRITE_CMD',[(0,3.3),(5.9,3.3),(6,0),(9.9,0),(10,3.3),(15.9,3.3),(16,0),(70,0)])
 read=[(0,0),(29.9,0),(30,3.3),(39.9,3.3),(40,0),(49.9,0),(50,3.3),(59.9,3.3),(60,0),(70,0)]
 wave('READ_CMD',read);wave('READ_ENABLE',read)
 for c in range(8):
  wave('DATA'+str(c),[(0,1.4-.01*c),(8.9,1.4-.01*c),(9,1+.01*c),(70,1+.01*c)])
  if c in [0,7]:
   a=30 if c==0 else 50;wave('SEL'+str(c),[(0,0),(a-.1,0),(a,3.3),(a+9.9,3.3),(a+10,0),(70,0)])
  else:lines.append(f'Vsel{c} SEL{c} 0 0')
 states=[f'B{b}_STATE{r}{c}' for b in range(2) for r in range(8) for c in range(8)];nodes=states+['RECOV','SELECTED_BIAS','B0_BIAS','B1_BIAS']+[f'READOUT{c}' for c in range(8)]+['BANK_SELECT','READ_CMD','WRITE_CMD'];lines+=['Xbank '+' '.join(q['ports'])+' '+f['flat_subcircuit'],'.save '+' '.join('v('+n+')' for n in nodes)+' i(Vdd)','.tran .02u 70u 0 1u','.end'];deck.write_text('\n'.join(lines)+'\n')
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','-r','/workspace/'+raw.relative_to(R).as_posix(),'/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135);lp=rp.with_suffix('.log');lp.write_text(run.stdout+run.stderr)
 o=dict(module_simulation_completed=False,simulator_returncode=run.returncode,two_bank_one_reader_recovery_observed=False,full_chip_layout_complete=False,original_float_accuracy_accepted=False,full_5ms_population_service_accepted=False,native_capacitance_branches=f['linear_branch_count'],scope='Actual852MOS133MIM qualified native physical128state bank pair,bank readout/bias TGselection,8column mux and one replica feedback reader. Native write atDC programsbank0row0;bank1row7 written10..16us,then selectedbank0col0/bank1col7 readsequentially throughsamephysicalreader. No IC/UIC or idealinverse. Other112states useunforcedoperatingpoints;notallbankinitialization or5msretentionproof. BothbankBIASreferences1uA,readerPBIAS1uA;externalidealvoltageDATA/categoricalcommands with100nsedges. Active numericalbudget reltol1e-4/vntol1e-7 disclosed;prior64readercheck is not128state accuracyproof. All nativeflatCretained;no noisestatistics/mismatch/PVT/trainedaccuracy/globalservice acceptance.')
 if raw.exists():
  h,b=raw.read_bytes().split(b'Binary:\n',1);nv=int(re.search(rb'No. Variables:\s*(\d+)',h)[1]);names=[l.split()[1] for l in h.decode().split('Variables:\n')[1].splitlines() if l.strip()];w=np.frombuffer(b[:len(b)//(8*nv)*(8*nv)],dtype='<f8').reshape(-1,nv);t=w[:,0];assert np.isfinite(w).all() and np.all(np.diff(t)>=0);np.savez_compressed(rp.with_suffix('.npz'),waveforms=w,variables=np.array(names));o['last_saved_time_s']=float(t[-1]);o['module_simulation_completed']=bool(run.returncode==0 and abs(t[-1]-70e-6)<1e-12 and 'aborted' not in (run.stdout+run.stderr).lower())
  if o['module_simulation_completed']:
   at=lambda n,us:float(np.interp(us*1e-6,t,w[:,names.index('v('+n.lower()+')')]));cases=[]
   for state,us,target in [('B0_STATE00',39,1.4),('B1_STATE77',59,1.07)]:
    actual=at(state,us);rec=at('RECOV',us);cases.append(dict(selected_state=state,at_us=us,actual_state_v=actual,recovered_v=rec,recovery_error_v=rec-actual,write_error_v=actual-target,selected_bias_v=at('SELECTED_BIAS',us)))
   err=max(abs(c['recovery_error_v']) for c in cases);dist=max(abs(at(n,69.9)-at(n,18)) for n in states);o.update(cases=cases,max_recovery_error_v=err,max_state_change_after_write_v=dist,two_bank_one_reader_recovery_observed=bool(err<.01 and dist<.03),VDD_energy_j_excludes_external_references=float(np.trapezoid(-3.3*w[:,names.index('i(vdd)')],t)))
 o['sha256']={p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),qp,fp,src,deck,lp]+([raw] if raw.exists() else [])};rp.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps({k:v for k,v in o.items() if k!='sha256'},indent=2))
if __name__=='__main__':main()
