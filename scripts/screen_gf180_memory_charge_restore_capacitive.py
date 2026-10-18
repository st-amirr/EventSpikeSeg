"""Native charge read and capacitively coupled autozero restore; frozen incremental calibration."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--transfer',choices=['on','off'],required=True);parser.add_argument('--seed',type=int,default=0);a=parser.parse_args()
 stem='gf180_memory_charge_restore_capacitive_'+a.transfer+'_seed'+str(a.seed)+'_src'+sha(Path(__file__))[:12]
 rp=BASE/'results'/(stem+'.json');assert not rp.exists()
 files={Path(__file__)};texts=[]
 calibration=BASE/'results/gf180_memory_charge_read_on_seed0_src5aba4580d681.json';c=json.loads(calibration.read_text());assert c['simulation_completed'];files.add(calibration)
 m=c['measurements'];low=m['low_out_read_late']-m['low_out_held'];high=m['high_out_read_late']-m['high_out_held'];gain=-(m['high_state_held']-m['low_state_held'])/(high-low);ref=m['low_state_held']+gain*low
 memory='gf180_isolated_memory_characterization_fullroute';acc='gf180_autozero_charge_integrator_fullroute_guarded';tg='gf180_fixed_body_tg_fullroute_half';inv='gf180_phase_inverter_fullroute'
 for cell in [memory,acc,tg,inv,'gf180_shared_ota_core_pmos_input_fullroute']:
  directory=BASE/'layout'/cell;qp=directory/'qualification.json';q=json.loads(qp.read_text());files.add(qp)
  assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'] and not q['extraction_feedback']
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for name,h in q.get(key,{}).items():
    f=directory/name if key=='sha256' else ROOT/name;assert sha(f)==h,str(f);files.add(f)
  s=(directory/(cell+'_cap.spice')).read_text()
  for child in re.findall(r'(?m)^\.subckt (\S+)',s):
   if child!=cell:s=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(child)+r'(?![A-Za-z0-9_])',cell+'__'+child,s)
  texts.extend(s.splitlines())
 models=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix()
 lines=['Native charge-read feasibility',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.lib {prefix}/sm141064.spice res_typical',f'.param sw_stat_global=0 sw_stat_mismatch={int(a.seed!=0)}','.temp 27','.options method=gear reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',*texts,'.global VSUBS','Vsubstrate VSUBS 0 0','Vdd vdd 0 3.3','Vcm vcm 0 1.65','Ibias bias 0 1u','Xbias bias bias vdd vdd pfet_03v3 w=20u l=2u ad=8.8p as=8.8p pd=40.88u ps=40.88u']
 enabled=a.transfer=='on'
 phases={
 'init':'PWL(0 3.3 19.99u 3.3 20u 0 90u 0)',
 'reset':'PWL(0 3.3 49.99u 3.3 50u 0 90u 0)',
 'write':'PWL(0 3.3 19.97u 3.3 19.98u 0 '+('60.01u 0 60.02u 3.3 109.97u 3.3 109.98u 0 115u 0)' if enabled else '90u 0)'),
 'outer':'PWL(0 3.3 19.99u 3.3 20u 0 '+('59.99u 0 60u 3.3 109.99u 3.3 110u 0 115u 0)' if enabled else '90u 0)'),
 'midclamp':'PWL(0 0 20.01u 0 20.02u 3.3 '+('59.93u 3.3 59.94u 0 110.01u 0 110.02u 3.3 115u 3.3)' if enabled else '90u 3.3)'),
 'buspark':'PWL(0 0 20.03u 0 20.04u 3.3 '+('59.93u 3.3 59.94u 0 110.01u 0 110.02u 3.3 115u 3.3)' if enabled else '90u 3.3)'),
 'restorereset':'PWL(0 3.3 59.89u 3.3 59.90u 0 115u 0)',
 'restore':'PWL(0 0 85.03u 0 85.04u 3.3 109.93u 3.3 109.94u 0 115u 0)',
 'transfer':'PWL(0 0 59.95u 0 59.96u 3.3 84.99u 3.3 85u 0 115u 0)' if enabled else '0'}
 lines.append(f'Vrestore_reference restore_ref 0 {ref:.16g}')
 for phase,wave in phases.items():
  lines +=[f'V{phase} {phase}_command 0 {wave}',f'Xb_{phase} {phase}_command {phase}b vdd 0 {inv}',f'Xc_{phase} {phase}b {phase} vdd 0 {inv}']
 targets={'low':.75,'mid':1.65,'high':2.55}
 for tag,v in targets.items():
  lines +=[f'Vtarget_{tag} target_{tag} 0 {v}',f'Xinit_{tag} bus_{tag} target_{tag} init initb 0 vdd {tg}',f'Xbuspark_{tag} bus_{tag} vcm buspark busparkb 0 vdd {tg}',f'Xtransfer_{tag} bus_{tag} sum_{tag} transfer transferb 0 vdd {tg}',f'Xmemory_{tag} state_{tag} vcm middle_{tag} column_{tag} drain_{tag} write writeb outer outerb midclamp midclampb 0 vdd vdd 0 0 vdd bus_{tag} {memory}',f'Rcolumn_{tag} column_{tag} 0 10000',f'Xacc_{tag} vcm out_{tag} vdd 0 bias reset resetb reset resetb sum_{tag} cmp_{tag} azin_{tag} {acc}',f'Cload_{tag} out_{tag} 0 50f',f'.ic v(state_{tag})=1.65 v(out_{tag})=1.65 v(sum_{tag})=1.65']
  lines +=[f'Xrestore_acc_{tag} restore_ref restore_out_{tag} vdd 0 bias restorereset restoreresetb restorereset restoreresetb restore_sum_{tag} restore_cmp_{tag} restore_azin_{tag} {acc}',f'Xrestore_switch_{tag} bus_{tag} restore_out_{tag} restore restoreb 0 vdd {tg}',f'.ic v(restore_out_{tag})={ref} v(restore_sum_{tag})={ref}']
  # Ten nine-MIM banks plus five unit MIMs give nominal95/9 capacitive inversion.
  for i in range(10):
   lines.append(f'Xrestore_input_bank{i}_{tag} out_{tag} restore_sum_{tag} 0 {acc}__gf180_mim_bank_7x7_n9')
  for i in range(5):
   lines.append(f'Xrestore_input_unit{i}_{tag} out_{tag} restore_sum_{tag} cap_mim_2f0_m4m5_noshield c_width=7u c_length=7u')
 lines+=['.control','set numdgt=15']
 if a.seed:lines +=[f'setseed {a.seed}','reset']
 lines+=['tran .1u 115u 0 .5u uic']
 vectors=[]
 for tag in targets:
  for node in ['state','out','sum','bus','restore_out']:
   for label,t in [('acquired',19.5),('held',59),('read_early',61),('read_five',65),('read_late',84.5),('restoring',109.5),('restored',114)]:
    lines.append(f'meas tran {tag}_{node}_{label} find v({node}_{tag}) at={t}u')
  for statistic in ['min','max']:
   lines.append(f'meas tran {tag}_out_window_{statistic} {statistic} v(out_{tag}) from=80u to=84.5u')
  vectors.extend([f'v({n}_{tag})' for n in ['state','out','sum','bus','restore_out']])
 data=BASE/'results'/(stem+'.dat');lines+=['set wr_singlescale','set wr_vecnames','wrdata /workspace/'+data.relative_to(ROOT).as_posix()+' '+' '.join(vectors),'quit','.endc','.end']
 deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n',encoding='utf-8');files.add(deck)
 snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log,encoding='utf-8');files.add(lp)
 values={k:float(v) for k,v in re.findall(r'(?m)^((?:low|mid|high)_[a-z_]+)\s*=\s*([-+0-9.eE]+)',log)}
 complete=run.returncode==0 and len(values)==111 and 'aborted' not in log.lower() and data.exists()
 if data.exists():files.add(data)
 summary={tag:{'held_v':values.get(tag+'_state_held'),'state_after_v':values.get(tag+'_state_read_late'),'restore_error_v':values.get(tag+'_state_restored',0)-values.get(tag+'_state_held',0),'output_increment_v':values.get(tag+'_out_read_late',0)-values.get(tag+'_out_held',0),'late_output_window_v':values.get(tag+'_out_window_max',0)-values.get(tag+'_out_window_min',0)} for tag in targets}
 report={'simulation_completed':complete,'simulator_returncode':run.returncode,'settings':vars(a),'targets_v':targets,'measurements':values,'summary':summary,'calibration_report':calibration.relative_to(ROOT).as_posix(),'frozen_restore_reference_v':ref,'feedback_ratio':95/9,'scope':'Native destructive read followed by capacitively coupled autozero integrator restore.95unitMIM input coupling to9unitMIM feedback nominalgain95/9; input samples reader baseline while restoreSUM is clamped to frozen external1.397268V reference. Reader AZ ends50us; restoreAZ ends59.9us; transfer60us, opens85us; restoreTG closes85.04us, memory isolated110us. Reference from prior nominal incremental endpoint calibration, not a new per-lane fit. No arithmetic state correction or digital capture. Qualified extracted children plus schematic coupling/restore connection; no new combinedlayout/noise/RPEX/PVT/leakage,40us hold only. Actual coupling loads reader, so donor transfer is not assumed unchanged. Real restore measured114us. Seed29 uses new native hierarchy, not prior draws.95inputMIMs per shared restore lane area/service remain to be budgeted','readout_accepted':False,'complete_PLIF_accepted':False,'original_float_accuracy_accepted':False,'full_5ms_population_service_accepted':False,'full_chip_accepted':False,'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 rp.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(rp),'simulation_completed':complete,'summary':summary},indent=2))
 if not complete:raise RuntimeError(log[-1800:])
if __name__=='__main__':main()
