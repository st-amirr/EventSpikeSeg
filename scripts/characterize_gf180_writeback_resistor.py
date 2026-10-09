"""Native writeback resistor/feedback-cap metrology, not calibrated writeback."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
import probe_gf180_mos_gate_cap as flow
ROOT=flow.ROOT;BASE=flow.BASE;CELL='gf180_writeback_resistor_123x1'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--resistor-corner',choices=['res_typical','res_ff','res_ss'],default='res_typical');p.add_argument('--temp-c',type=int,choices=[0,27,85],default=27);a=p.parse_args()
 src=Path(__file__);sha=digest(src);sources=[];cells=[];qualified=[]
 for name in [CELL,'gf180_mim_22x22']:
  folder=BASE/'layout'/name;qp=folder/'qualification.json';q=json.loads(qp.read_text())
  if q['magic_drc_count'] or not q['lvs_unique'] or q['extraction_feedback']:raise ValueError('Native primitive qualification failed')
  for filename,expected in q['sha256'].items():
   f=folder/filename
   if digest(f)!=expected:raise ValueError('Native provenance mismatch')
   sources.append(f)
  sources.append(qp);qualified.append(q);cells.append(folder/(name+'_cap.spice'))
 md=BASE/'pdk/gf180_primitive_source/models/ngspice';prefix='/workspace/'+md.relative_to(ROOT).as_posix();stem=f'gf180_writeback_resistor_{a.resistor_corner}_{a.temp_c}_src{sha[:12]}';dat=BASE/'results'/(stem+'_dc.dat')
 lines=['Native resistor/feedback capacitance metrology',f'.include {prefix}/design.spice','.param sw_stat_global=0 sw_stat_mismatch=0',f'.lib {prefix}/sm141064.spice {a.resistor_corner}',f'.lib {prefix}/sm141064.spice mimcap_typical',f'.temp {a.temp_c}','.options gmin=1e-18 reltol=1e-7 vntol=1e-10 abstol=1e-18']
 for f in cells:lines+=f.read_text().splitlines()
 lines+=['Vb b 0 1.5','Va a 0 DC 1.7 AC 1',f'Xres b a 0 {CELL}','Hnoise nout 0 Va 1e9','Vcft cft 0 1.5','Vcfref cfref 0 1.5','Xcf cft cfref 0 gf180_mim_22x22','.control','set numdgt=15','reset','op','let resistance_actual=(v(a)-v(b))/(-i(va))','let cf_actual=32*(@c.xcf.x0.c_cap[capacitance]+@c.xcf.c0[capacitance])','let rc_actual=resistance_actual*cf_actual','let once_beta_writeback_scale=4e-6/rc_actual','print resistance_actual cf_actual rc_actual once_beta_writeback_scale','noise v(nout) Va dec 80 10 100meg','let current_noise_rms=onoise_total/1e9','print current_noise_rms','dc Va 1.25 1.75 0.05','set wr_singlescale','set wr_vecnames','wrdata /workspace/'+dat.relative_to(ROOT).as_posix()+' i(va)','quit','.endc','.end']
 deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');snap=BASE/'tools/source_snapshots'/f'writeback_resistor_{sha}.py'
 if not snap.exists():snap.write_bytes(src.read_bytes())
 sources+=[snap,deck,md/'design.spice',md/'sm141064.spice',md/'sm141064_mim.spice']
 proc=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','1','--volume',f'{ROOT}:/workspace','--workdir',prefix,'--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=proc.stdout+proc.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);sources.append(lp)
 names=['resistance_actual','cf_actual','rc_actual','once_beta_writeback_scale','current_noise_rms'];v={k:float(x) for k,x in re.findall(r'(?m)^\s*('+'|'.join(names)+r')\s*=\s*([-+0-9.eE]+)',log)}
 complete=proc.returncode==0 and 'ngspice-47 done' in log and len(v)==len(names) and dat.exists()
 rows=[]
 if dat.exists():
  sources.append(dat)
  for line in dat.read_text().splitlines()[1:]:
   voltage,current=map(float,line.split());rows.append({'voltage_difference_v':voltage-1.5,'source_current_a':current,'inferred_resistance_ohm':(voltage-1.5)/(-current) if abs(voltage-1.5)>1e-8 else None})
 if len(rows)!=11:complete=False
 report={'simulation_completed':complete,'simulator_returncode':proc.returncode,'settings':vars(a),'source_snapshot':snap.relative_to(ROOT).as_posix(),'measurements':v,'dc_rows':rows,'qualified_layout_components':qualified,'physical_writeback_accepted':False,'full_chip_accepted':False,'scope':'Native high-poly resistor across ideal rail-safe diagnostic ports; resistor process corner explicitly independent from MOS. Standalone identical native feedback-MIM device queried for temperature-adjusted32-bank capacitance. RC-derived scale refers to4us base window, excludes beta so decay is applied once. Ideal sources only metrology; no physical R/C calibration, result loading/writeback, integration-aperture noise, active OTA/noise/mismatch, silicon gate leakage, combined route/PLIF/5ms/chip acceptance. Current-noise RMS10Hz..100MHz is stationary under0.2V DC resistor bias; not sampled-current/charge noise.','sha256':{f.relative_to(ROOT).as_posix():digest(f) for f in set(sources)}}
 target=BASE/'results'/(stem+'.json');target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(target),'simulation_completed':complete,'measurements':v},indent=2))
 if not complete:raise RuntimeError(log[-2500:])
if __name__=='__main__':main()
