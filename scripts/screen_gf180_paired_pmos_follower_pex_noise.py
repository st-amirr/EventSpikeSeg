"""Measure continuous read-buffer noise with driven input; excludes sampled capture noise."""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_pmos_follower_baseline_readout_fullroute_guarded';folder=BASE/'layout'/cell;qp=folder/'qualification.json';q=json.loads(qp.read_text());sources={qp}
 assert q['magic_drc_count']==q['gds_roundtrip_drc_count']==0 and q['lvs_unique'] and q['gds_roundtrip_lvs_unique']
 for key in ['sha256','input_sha256','gds_roundtrip_sha256']:
  for n,h in q.get(key,{}).items():
   p=folder/n if key=='sha256' else ROOT/n;assert digest(p)==h,str(p);sources.add(p)
 models=BASE/'pdk/gf180_primitive_source/models/ngspice';sources.update(models.rglob('*.spice'));prefix='/workspace/'+models.relative_to(ROOT).as_posix()
 stem='gf180_paired_pmos_follower_pex_noise_src'+digest(Path(__file__))[:12];snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(Path(__file__).read_bytes());sources.add(snap)
 spectrum=BASE/'results'/(stem+'_spectrum.txt')
 lines=['Driven-input read-buffer small-signal noise diagnostic',f'.include {prefix}/design.spice',f'.lib {prefix}/sm141064.spice typical',f'.lib {prefix}/sm141064.spice mimcap_typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options reltol=1e-6 abstol=1e-16 vntol=1e-10 gmin=1e-18',(folder/(cell+'_cap.spice')).read_text(),'Vdd vdd 0 3.3','Vcm vcm 0 1.65','Vinput capture 0 DC 1.65 AC 1','Vcap cap 0 0','Vcapb capb 0 3.3','Ireference pbias 0 10u','Xreference pbias pbias vdd vdd 0 gf180_read_pf10_l1',f'Xread vcm capture vcm cap capb vdd 0 pbias out {cell}','Cload out 0 500f','Vinputr capturer 0 DC 1.65 AC 0',f'Xreadr vcm capturer vcm cap capb vdd 0 pbias outr {cell}','Cloadr outr 0 500f','.control','set numdgt=15','op','print v(out)','noise v(outr,out) Vinput dec 100 1 1e8','print noise2.onoise_total noise2.inoise_total','noise v(outr,out) Vinput dec 100 200 1e8','print noise4.onoise_total noise4.inoise_total','setplot noise1','set wr_singlescale','set wr_vecnames','wrdata /workspace/'+spectrum.relative_to(ROOT).as_posix()+' onoise_spectrum','quit','.endc','.end']
 deck=BASE/'benches'/(stem+'.spice');deck.write_text('\n'.join(lines)+'\n');sources.add(deck)
 r=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{ROOT}:/workspace','--workdir','/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','/workspace/'+deck.relative_to(ROOT).as_posix()],capture_output=True,text=True,timeout=135)
 log=r.stdout+r.stderr;lp=BASE/'results'/(stem+'.log');lp.write_text(log);sources.add(lp)
 values={k:float(v) for k,v in re.findall(r'(?m)^(noise[24]\.(?:onoise_total|inoise_total)|v\(out\))\s*=\s*([-+0-9.eE]+)',log)}
 complete=r.returncode==0 and len(values)==5 and spectrum.exists()
 if spectrum.exists():sources.add(spectrum)
 report={'simulation_completed':complete,'simulator_returncode':r.returncode,'measurements':values,'spectrum':spectrum.relative_to(ROOT).as_posix(),'band_definitions_hz':{'noise2':[1,1e8],'noise4':[200,1e8]},'scope':'Actual physically qualified4MOS/9MIM source-body-tied PMOS follower/capture macro pair, ideal driven1.65V capture nodes ONLY in standalone continuous-noise diagnostic,500fF outputs, nominal27C native models. Real schematic-connected extracted PF10 mirror and ideal10uA external reference; common bias correlations included. Clamp off and input forced excludes capture-sampling kT/C, storage/source/clock/reference-programmer noise. New geometry/body parasitics included without RPEX. Nonunity gain/lower output common mode require calibration; no full-model accuracy/retention/service or fullPLIF/chip acceptance.','manual_reference':'https://ngspice.sourceforge.io/docs/ngspice-manual.pdf','weighted_charge_accepted':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_chip_accepted':False,'sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(sources)}}
 rp=BASE/'results'/(stem+'.json');rp.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(rp),'completed':complete,'measurements':values}))
 if not complete:raise RuntimeError(log[-3000:])
if __name__=='__main__':main()
