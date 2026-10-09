"""Native segmented resistor-bank DC reachability, not autonomous calibration."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
import probe_gf180_mos_gate_cap as flow
ROOT=flow.ROOT;BASE=flow.BASE;LENGTHS=[2,4,8,16,32,64,128]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mos-corner',choices=['typical','ff','ss'],default='typical');p.add_argument('--resistor-corner',choices=['res_typical','res_ff','res_ss'],default='res_typical');p.add_argument('--temp-c',type=int,choices=[0,27,85],default=27);p.add_argument('--two-ended-isolation',action='store_true');p.add_argument('--park-bank',action='store_true');a=p.parse_args();
 if a.park_bank and not a.two_ended_isolation:raise ValueError('Parking requires two-ended bank isolation')
 src=Path(__file__);sha=digest(src);sources=[];qualified=[]
 names=[f'gf180_writeback_resistor_{n}x1' for n in [60]+LENGTHS]+['gf180_fixed_body_tg','gf180_phase_inverter','gf180_mim_22x22'];definitions=[]
 for name in names:
  folder=BASE/'layout'/name;qp=folder/'qualification.json';q=json.loads(qp.read_text())
  if q['magic_drc_count'] or not q['lvs_unique'] or q['extraction_feedback']:raise ValueError('Native layout unqualified')
  for n,h in q['sha256'].items():
   f=folder/n
   if digest(f)!=h:raise ValueError('Native provenance differs')
   sources.append(f)
  sources.append(qp);qualified.append(q);definitions+= (folder/(name+'_cap.spice')).read_text().splitlines()
 md=BASE/'pdk/gf180_primitive_source/models/ngspice';prefix='/workspace/'+md.relative_to(ROOT).as_posix();stem=f'gf180_trim_bank_{a.mos_corner}_{a.resistor_corner}_{a.temp_c}_isolation{int(a.two_ended_isolation)}_park{int(a.park_bank)}_src{sha[:12]}'
 lines=['Native segmented resistor bank reachability',f'.include {prefix}/design.spice','.param sw_stat_global=0 sw_stat_mismatch=0',f'.lib {prefix}/sm141064.spice {a.mos_corner}',f'.lib {prefix}/sm141064.spice {a.resistor_corner}',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.temp {a.temp_c}','.options gmin=1e-18 reltol=1e-7 vntol=1e-10 abstol=1e-18']+definitions
 lines+=['Vdd vdd 0 3.3','Va a 0 1.7','Vb b 0 1.5','Vcft cft 0 1.5','Vcfref cfref 0 1.5','Xcf cft cfref 0 gf180_mim_22x22','Xbase p0 p1 0 gf180_writeback_resistor_60x1']
 for phase in ['restore']+[f'bit{i}' for i in range(7)]:
  lines.append('V'+phase+'command '+phase+'command 0 3.3')
  lines+=['X'+phase+'preA '+phase+'command '+phase+'preb vdd 0 gf180_phase_inverter','X'+phase+'preB '+phase+'preb '+phase+'pre vdd 0 gf180_phase_inverter','X'+phase+'outP '+phase+'preb '+phase+' vdd 0 gf180_phase_inverter','X'+phase+'outN '+phase+'pre '+phase+'b vdd 0 gf180_phase_inverter']
 for j in range(4):lines.append(f'Xrestore{j} a p0 restore restoreb 0 vdd gf180_fixed_body_tg')
 for i,length in enumerate(LENGTHS):
  start=f'p{i+1}';end=('bankout' if a.two_ended_isolation else 'b') if i==6 else f'p{i+2}';lines.append(f'Xsegment{i} {start} {end} 0 gf180_writeback_resistor_{length}x1')
  for j in range(4):lines.append(f'Xbypass{i}_{j} {start} {end} bit{i} bit{i}b 0 vdd gf180_fixed_body_tg')
 if a.two_ended_isolation:
  for j in range(4):lines.append(f'Xrestoreout{j} bankout b restore restoreb 0 vdd gf180_fixed_body_tg')
 if a.park_bank:
  for j in range(4):lines.append(f'Xbankpark{j} bankout b restoreb restore 0 vdd gf180_fixed_body_tg')
 lines+=['.control','set numdgt=15','reset']
 for code in range(128):
  for i in range(7):lines.append(f'alter Vbit{i}command = '+('0' if code&(1<<i) else '3.3'))
  for voltage in [1.3,1.7]:
   lines += [f'alter Va = {voltage}',f'echo SAMPLE {code} {voltage}','op','let resistance_actual=(v(a)-v(b))/(-i(va))','let cf_actual=32*(@c.xcf.x0.c_cap[capacitance]+@c.xcf.c0[capacitance])','print resistance_actual cf_actual']
 lines+=['quit','.endc','.end'];deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');snap=BASE/'tools/source_snapshots'/f'trim_bank_{sha}.py'
 if not snap.exists():snap.write_bytes(src.read_bytes())
 sources+=[snap,deck,md/'design.spice',md/'sm141064.spice',md/'sm141064_mim.spice']
 proc=subprocess.run(['docker','run','--rm','--network','none','--memory','4g','--cpus','2','--volume',str(ROOT)+':/workspace','--workdir',prefix,'--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=proc.stdout+proc.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);sources.append(lp);rows=[]
 for match in re.finditer(r'(?m)^SAMPLE (\d+) ([-+0-9.eE]+)\s*\n(.*?)(?=^SAMPLE|^ngspice-47 done|\Z)',log,re.S|re.M):
  code=int(match[1]);voltage=float(match[2]);values={k:float(v) for k,v in re.findall(r'(?m)^\s*(resistance_actual|cf_actual)\s*=\s*([-+0-9.eE]+)',match[3])}
  if len(values)==2:
   resistance=values['resistance_actual'];cap=values['cf_actual'];rows.append({'code':code,'voltage_difference_v':voltage-1.5,'resistance_actual_ohm':resistance,'cf_actual_f':cap,'rc_us':resistance*cap*1e6,'diagnostic_untrimmed_gain_error_percent':100*(4e-6/(resistance*cap)-1)})
 complete=proc.returncode==0 and 'ngspice-47 done' in log and len(rows)==256 and not re.search('simulation.*aborted|Error:|operating point failed|no convergence',log,re.I) and all(x['resistance_actual_ohm']>0 and x['cf_actual_f']>0 for x in rows)
 best=None;decreases=[]
 if complete:
  paired=[(max(abs(x['diagnostic_untrimmed_gain_error_percent']) for x in rows if x['code']==code),code) for code in range(128)];error,code=min(paired);best={'externally_selected_code':code,'maximum_two_polarity_rc_gain_error_percent':error,'rows':[x for x in rows if x['code']==code]}
  values=[next(x['resistance_actual_ohm'] for x in rows if x['code']==code and x['voltage_difference_v']>0) for code in range(128)];decreases=[i for i in range(1,128) if values[i]<=values[i-1]]
 report={'simulation_completed':complete,'simulator_returncode':proc.returncode,'settings':vars(a),'operating_point_solver_warning':bool(re.search('stepping failed|singular matrix',log,re.I)),'dc_numerical_precision_qualified':False,'source_snapshot':snap.relative_to(ROOT).as_posix(),'rows':rows,'analysis':{'best_external_dc_code':best,'nonincreasing_numeric_code_transitions':decreases,'numeric_code_order_monotonic_in_this_dc_probe':complete and not decreases,'sar_monotonicity_proven':False},'qualified_layout_components':qualified,'trim_bank_combined_layout_qualified':False,'autonomous_calibration_controller_implemented':False,'physical_writeback_accepted':False,'full_chip_accepted':False,'scope':'Seven native high-poly segments in series after native60um base; four actual TGs bypass each segment and four actual TGs provide input restore path; optional four actual TGs isolate bank output with the same real gate drivers, with four-inverter real loaded complementary drivers per bit/restore.128 externally commanded code settings, each probed at+/-0.2V relative to1.5V. Native feedback32-MIM capacitance queried only for metrology. Independent MOS/resistor corners and typicalMIM explicit. Operating-point stepping warnings are recorded separately from completed finite DC observations; numerical precision remains unqualified. Optional opposite-phase bank parking uses four real TGs tied to the diagnostic reference during restore-off; metrology probes only restore-on. Software selects reachable DC code; no fabricated calibration controller, transient result writeback, sampled noise, full PLIF, combined layout/RPEX/5ms/float/chip acceptance. Contact resistance and bypass loading included; binary ordering is not assumed monotonic.','sha256':{f.relative_to(ROOT).as_posix():digest(f) for f in set(sources)}}
 target=BASE/'results'/(stem+'.json');target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(target),'simulation_completed':complete,'rows':len(rows),'analysis':report['analysis']},indent=2))
 if not complete:raise RuntimeError(log[-1800:])
if __name__=='__main__':main()
