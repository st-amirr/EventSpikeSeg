"""Complete native GDS/device readback and actual flat capacitance for the compact cell."""
from pathlib import Path
import hashlib,json,re
import probe_gf180_mos_gate_cap as f
from resume_gf180_formatted64_completed_flat_v2 import branches_units
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def xlines(p):return [l.split() for l in p.read_text().replace('\n+',' ').splitlines() if l.startswith('X')]
def main():
 cell='gf180_compact_memory_bank8x8_v1';d=f.BASE/'layout'/cell;initial=d/'initial_physical_result.json';iq=json.loads(initial.read_text());assert iq['magic_drc_count']==0 and iq['lvs_unique']
 for n,h in iq['sha256'].items():assert sha(R/n)==h,n
 assert not re.search(r'(?m)^use ',(d/(cell+'.mag')).read_text()),'Cell must actually be flat'
 assert not (d/'qualification.json').exists();f.OUT=d
 log=f.magic(f'load {cell}\nextract do capacitance\nextract all\nfeedback save capacitance.feedback\next2spice lvs\next2spice cthresh 0\next2spice scale off\next2spice -o {cell}_cap.spice\nquit -noprompt\n');lp=d/'capacitance_extraction.log';lp.write_text(log);assert not (d/'capacitance.feedback').read_text()
 assert xlines(d/(cell+'.spice'))==xlines(d/(cell+'_cap.spice')),'Native device connectivity/parameters changed in capacitor export'
 branches=branches_units(d/(cell+'_cap.spice'),cell);negative={str(k):v for k,v in branches.items() if v< -1e-20};assert not negative
 rd=f.BASE/'verification/gds_roundtrip'/cell;assert not rd.exists();rd.mkdir(parents=True);f.OUT=rd
 log=f.magic('gds read /workspace/'+(d/(cell+'.gds')).relative_to(R).as_posix()+f'\nload {cell}\ndrc on\ndrc style drc(full)\nselect top cell\ndrc check\ndrc catchup\ndrc count total\nextract all\nfeedback save roundtrip.feedback\next2spice lvs\next2spice scale off\next2spice -o roundtrip.spice\nquit -noprompt\n');gl=rd/'readback.log';gl.write_text(log)
 assert re.search(r'Total DRC errors found:\s*0\b',log) and not (rd/'roundtrip.feedback').read_text()
 setup='/workspace/'+f.PDK.relative_to(R).as_posix()+'/libs.tech/netgen/gf180mcuD_setup.tcl'
 nl=f.run(['netgen-lvs','-batch','lvs','roundtrip.spice '+cell,'/workspace/'+(d/'reference.spice').relative_to(R).as_posix()+' reference',setup,'lvs.out']);(rd/'netgen.log').write_text(nl);assert 'Circuits match uniquely' in nl
 outputs=[d/(cell+s) for s in ['.mag','.spice','.gds','_cap.spice']]+[d/'build_source.py',d/'reference.spice',d/'netgen.log',d/'extraction.log',lp,d/'capacitance.feedback']
 inputs=[Path(__file__),initial,R/'scripts/resume_gf180_formatted64_completed_flat_v2.py']+[R/n for n in iq['sha256'] if (R/n).parent!=d]
 q=dict(cell=cell,ports=iq['ports'],bbox_um=iq['bbox_um'],mos_count=256,native_mim_count=64,native_resistor_count=0,
  magic_drc_count=0,drc_style='drc(full)',lvs_unique=True,gds_roundtrip_drc_count=0,gds_roundtrip_lvs_unique=True,
  actual_source_ports_verified=True,actual_gds_ports_verified=True,extraction_feedback='',physical_storage_accepted=False,
  full_chip_accepted=False,scope=iq['scope'].replace('Four STATE diagnostic pads','64 STATE diagnostic pads')+' Source full DRC0 and independent Netgen LVS unique; GDS readback full DRC0 and independent reference LVS unique. Native flat capacitor export device records exactly match qualified source. All extracted aggregate routing branches nonnegative. Storage/read behavior and array loading remain to be simulated.',
  sha256={p.name:sha(p) for p in outputs},input_sha256={p.relative_to(R).as_posix():sha(p) for p in inputs},
  gds_roundtrip_sha256={p.relative_to(R).as_posix():sha(p) for p in [rd/'roundtrip.spice',gl,rd/'netgen.log',rd/'roundtrip.feedback']})
 qp=d/'qualification.json';qp.write_text(json.dumps(q,indent=2)+'\n')
 fp=d/'flat_cap_qualification.json';assert not fp.exists()
 files=[Path(__file__),qp,lp,d/(cell+'_cap.spice'),d/(cell+'.spice'),d/'capacitance.feedback',d/'netgen.log']
 fp.write_text(json.dumps(dict(cell=cell,flat_subcircuit=cell,flat_extraction_completed=True,flat_lvs_unique=True,
  full_flat_drc_count=0,linear_branch_count=len(branches),negative_aggregate_branches=negative,
  scope='The source MAG itself contains only painted primitive geometry and no child uses, so qualified source full DRC is the full flat DRC. Source Netgen reference LVS passes; every native device record in actual flat capacitance export is token-identical to that source. All routing-capacitance branches retained and aggregate signs checked. No array, retention, noise, model, service or chip acceptance.',
  sha256={p.relative_to(R).as_posix():sha(p) for p in files}),indent=2)+'\n')
 print(json.dumps({'qualification':str(qp),'full_DRC_source_and_GDS':0,'native_source_and_GDS_LVS':True,'linear_branches':len(branches),'area_um2':(q['bbox_um'][2]-q['bbox_um'][0])*(q['bbox_um'][3]-q['bbox_um'][1])},indent=2))
if __name__=='__main__':main()
