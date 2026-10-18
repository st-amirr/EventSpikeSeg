"""Bounded DC feasibility screen of native regulated-column current-matching readout."""
import hashlib,json,re,subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 source=Path(__file__);stem='gf180_regulated_current_readout_dc_src'+sha(source)[:12]
 rp=BASE/'results'/(stem+'.json');assert not rp.exists(),'Preserve prior results'
 files={source};texts=[]
 for cell in ['gf180_shared_ota_core_pmos_input_fullroute','gf180_source_pf05_l1_fullroute','gf180_nondestructive_sense_nf05_l1_fullroute','gf180_fixed_body_tg_fullroute_quarter']:
  directory=BASE/'layout'/cell;qp=directory/'qualification.json';q=json.loads(qp.read_text());files.add(qp)
  assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique'] and not q['extraction_feedback']
  for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
   for name,h in q.get(key,{}).items():
    p=directory/name if key=='sha256' else ROOT/name
    assert sha(p)==h,str(p)
    files.add(p)
  text=(directory/(cell+'_cap.spice')).read_text()
  for child in re.findall(r'(?m)^\.subckt (\S+)',text):
   if child!=cell:text=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(child)+r'(?![A-Za-z0-9_])',cell+'__'+child,text)
  texts+=text.splitlines()
 models=BASE/'pdk/gf180_primitive_source/models/ngspice';files.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix()
 data=BASE/'results'/(stem+'.dat')
 lines=['Native regulated-column current-matching DC diagnostic',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18','.global VSUBS','Vsubstrate VSUBS 0 0',*texts,
 'Vdd vdd 0 3.3','Vclamp clamp 0 .01','Vinput input 0 1.65','Ibias bias 0 5u','Xbias bias bias vdd vdd pfet_03v3 w=20u l=2u ad=8.8p as=8.8p pd=40.88u ps=40.88u',
 'Xcell drain input 0 0 gf180_nondestructive_sense_nf05_l1_fullroute','Xselect drain col vdd 0 0 vdd gf180_fixed_body_tg_fullroute_quarter',
 'Xclamp col clamp mirror_gate vdd 0 bias cmp1 gf180_shared_ota_core_pmos_input_fullroute','Xfeed col mirror_gate vdd vdd gf180_source_pf05_l1_fullroute',
 'Xrepfeed refcol mirror_gate vdd vdd gf180_source_pf05_l1_fullroute','Xrepselect refdrain refcol vdd 0 0 vdd gf180_fixed_body_tg_fullroute_quarter','Xreplica refdrain decoded 0 0 gf180_nondestructive_sense_nf05_l1_fullroute','Xinverse refcol clamp decoded vdd 0 bias cmp2 gf180_shared_ota_core_pmos_input_fullroute',
 'Xcomp1 mirror_gate cmp1 cap_mim_2f0_m4m5_noshield c_width=7u c_length=7u','Xcomp2 decoded cmp2 cap_mim_2f0_m4m5_noshield c_width=7u c_length=7u',
 '.nodeset v(col)=.01 v(refcol)=.01 v(mirror_gate)=2.5 v(decoded)=1.65',
 '.control','set numdgt=15','set wr_singlescale','set wr_vecnames','dc Vinput .75 2.55 .15',
 'wrdata /workspace/'+data.relative_to(ROOT).as_posix()+' v(input) v(decoded) v(col) v(refcol) v(drain) v(refdrain) i(Vdd)','quit','.endc','.end']
 deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n',encoding='utf-8');files.add(deck)
 snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(source.read_bytes());files.add(snap)
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=run.stdout+run.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log,encoding='utf-8');files.add(lp)
 rows=np.loadtxt(data,skiprows=1) if data.exists() else np.empty((0,8));complete=run.returncode==0 and rows.shape==(13,8) and np.isfinite(rows).all() and 'aborted' not in log.lower()
 if data.exists():files.add(data)
 records=[dict(zip(['sweep_v','input_v','decoded_v','column_v','replica_column_v','drain_v','replica_drain_v','supply_current_a'],map(float,row))) for row in rows]
 report={'simulation_completed':bool(complete),'simulator_returncode':run.returncode,'points':records,'max_absolute_decode_error_v':max((abs(r['decoded_v']-r['input_v']) for r in records),default=None),
 'scope':'DC topology screen with actual extracted native two7MOS OTAs, matched PF0.5/L1 feeds, matched NF0.5/L1 sense transistors and quarterTG selects; two schematic native7um compensation MIMs. Input sense gate is ideal swept voltage, not held memory. Native MOS feedback regulates actual columns;10mV is reference only, no ideal column clamp. Legacy implicit VSUBS globally tied to external substrate ground. Matching is nominal, no mismatch/noise/PVT/RPEX, settling, memory disturbance, autonomous service or combined layout acceptance.',
 'physical_storage_accepted':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_5ms_population_service_accepted':False,'full_chip_accepted':False,'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}}
 rp.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(rp),'simulation_completed':bool(complete),'max_decode_error_v':report['max_absolute_decode_error_v'],'points':records},indent=2))
 if not complete:raise RuntimeError(log[-2000:])
if __name__=='__main__':main()
