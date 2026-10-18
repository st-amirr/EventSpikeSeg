"""Native local beta feasibility: one PMOS auxiliary gate capacitor and resident MIM storage."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--state-plates',type=int,choices=[1,2],required=True);parser.add_argument('--beta',choices=['on','off'],required=True);a=parser.parse_args()
 stem=f'gf180_resident_beta_shorttracks_{a.beta}_plates{a.state_plates}_src{sha(Path(__file__))[:12]}';rp=BASE/'results'/(stem+'.json');assert not rp.exists();files={Path(__file__)};texts=[]
 cap='gf180_mim_5x5_ports_routed';tg='gf180_fixed_body_tg_quarter_shorttracks';pf='gf180_source_pf05_l1_fullroute';inv='gf180_phase_inverter_fullroute'
 for cell in [cap,tg,pf,inv]:
  directory=BASE/'layout'/cell;qp=directory/'qualification.json';q=json.loads(qp.read_text());files.add(qp);assert q['magic_drc_count']==0 and q['lvs_unique'] and not q['extraction_feedback']
  if cell!=cap:assert q['gds_roundtrip_drc_count']==0 and q['gds_roundtrip_lvs_unique']
  else:
   ap=BASE/'results/gf180_minimum_mim_routed_gds_integrity.json';audit=json.loads(ap.read_text());assert audit['audit_completed'] and audit['cases'][0]['physical_layout_accepted'];files.add(ap)
   for n,h in audit['sha256'].items():assert sha(ROOT/n)==h,n;files.add(ROOT/n)
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for name,h in q.get(key,{}).items():
    f=directory/name if key=='sha256' else ROOT/name;assert sha(f)==h,name;files.add(f)
  s=(directory/(cell+'_cap.spice')).read_text()
  for child in re.findall(r'(?m)^\.subckt (\S+)',s):
   if child!=cell:s=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(child)+r'(?![A-Za-z0-9_])',cell+'__'+child,s)
  texts.extend(s.splitlines())
 models=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix()
 lines=['Local native capacitive beta',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'.global VSUBS','Vsub VSUBS 0 0','Vdd vdd 0 3.3','Vcm vcm 0 1.65']
 phases={'write':'PWL(0 3.3 9.99u 3.3 10u 0 25u 0)','auxreset':'PWL(0 3.3 19.97u 3.3 19.98u 0 25u 0)','beta':'PWL(0 0 19.99u 0 20u 3.3 20.49u 3.3 20.5u 0 25u 0)' if a.beta=='on' else '0'}
 for phase,wave in phases.items():lines +=[f'V{phase} {phase}_command 0 {wave}',f'Xb_{phase} {phase}_command {phase}b vdd 0 {inv}',f'Xc_{phase} {phase}b {phase} vdd 0 {inv}']
 for tag,v in [('low',.75),('mid',1.65),('high',2.55)]:
  lines +=[f'Vtarget_{tag} target_{tag} 0 {v}',f'Xwrite_{tag} state_{tag} target_{tag} write writeb 0 vdd {tg}',f'Xauxreset_{tag} aux_{tag} vcm auxreset auxresetb 0 vdd {tg}',f'Xbeta_{tag} state_{tag} aux_{tag} beta betab 0 vdd {tg}',f'Xauxcap_{tag} vdd aux_{tag} vdd vdd {pf}',f'.ic v(state_{tag})=1.65 v(aux_{tag})=1.65']
  for i in range(a.state_plates):lines.append(f'Xstate{i}_{tag} state_{tag} vcm 0 {cap}')
 lines +=['.control','set numdgt=15','tran .01u 25u 0 .1u uic']
 for tag in ['low','mid','high']:
  for node in ['state','aux']:
   for label,t in [('acquired',9.5),('held',19),('sharing',20.45),('after',21.5),('final',24.5)]:lines.append(f'meas tran {tag}_{node}_{label} find v({node}_{tag}) at={t}u')
 data=BASE/'results'/(stem+'.dat');vectors=[f'v({node}_{tag})' for tag in ['low','mid','high'] for node in ['state','aux']]
 lines +=['set wr_singlescale','set wr_vecnames','wrdata /workspace/'+data.relative_to(ROOT).as_posix()+' '+' '.join(vectors),'quit','.endc','.end'];deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n',encoding='utf-8');files.add(deck);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log,encoding='utf-8');files.add(lp);values={k:float(v) for k,v in re.findall(r'(?m)^((?:low|mid|high)_[a-z_]+)\s*=\s*([-+0-9.eE]+)',log)}
 complete=run.returncode==0 and len(values)==30 and data.exists() and 'aborted' not in log.lower()
 if data.exists():files.add(data)
 summary={t:{'held_state_v':values.get(t+'_state_held'),'after_state_v':values.get(t+'_state_after')} for t in ['low','mid','high']}
 report={'simulation_completed':complete,'simulator_returncode':run.returncode,'settings':vars(a),'measurements':values,'summary':summary,'scope':'Native residentMIM gate-state charge sharing to one nativePF auxiliary gate capacitor. PMOS D/S/body allVDD, G=aux; qualified extracted0.5umW/1umL PF plus shorttracks quarterTG writer/reset/beta and inverter modules. Only TG physical routing package differs from original local-beta fixture; identical transistor dimensions, supply, timing, target, state MIM and auxiliary PF. No transfer of old calibration or mismatch claim. AuxprechargeVCM releases19.98us, betaTG connects20..20.5us, no shared readout/restore or forced heldSTATE. Bare plate variants1/2 use actual repaired minimumMIM modules; all inter-module connections schematic. Initial actual write from1.65V, measures actual heldstate; three voltage levels, nominal only, short15us hold. Effectivebeta includes deviceC(V), routing, switch junctions and injection; not learnedbeta coverage, calibrated neuron,5msretention/noise/layout/service/accuracy acceptance. Channel precision and physical per-state area remain to be budgeted; no QAT or digital state.','acceptance':{'resident_beta':False,'complete_PLIF':False,'original_float_accuracy':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 rp.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(rp),'simulation_completed':complete,'summary':summary},indent=2))
 if not complete:raise RuntimeError(log[-1800:])
if __name__=='__main__':main()
