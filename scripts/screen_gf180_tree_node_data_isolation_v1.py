"""One bounded374MOS tree-node boundary case with all64 DATA switches.

Native child capacitance retained; new parent atlas-wire RC deliberately absent.
Boundary sources and100fF loads are explicit fixtures, not resident-state evidence.
"""
from pathlib import Path
import hashlib,json,re,subprocess,time,numpy as np
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 stem='gf180_tree_node374_data_isolation_v1';rp=B/'results'/(stem+'.json');assert not rp.exists();raw=rp.with_suffix('.raw');deck=B/'benches'/(stem+'.spice');sources=[];defs=[];ports={}
 for c,suffix in [('gf180_shared_page_tree_selector8_v2','_fullcap'),('gf180_fixed_body_tg_quarter_shorttracks','_cap'),('gf180_dense_inverter_v1','_cap')]:
  d=B/'layout'/c;qf=d/'qualification.json';q=json.loads(qf.read_text());assert q['lvs_unique'] and q['magic_drc_count']==0;p=d/(c+suffix+'.spice');txt=p.read_text();pp=re.search(r'(?m)^\.subckt\s+'+c+r'\s+([^\n]+)',txt.replace('\n+',' '))[1].split();assert set(pp)==set(q['ports']);ports[c]=pp;sources.extend([qf,p]);defs.append(txt)
 frozen=B/'results/gf180_page1024_read_frontend_partition_v1_native_A_B_A.json';f=json.loads(frozen.read_text());assert f['module_simulation_completed'];va=f['cases'][0]['recovered_v'];vb=f['cases'][1]['recovered_v'];sources.append(frozen);pre='/workspace/artifacts/analog_asic/pdk/gf180_primitive_source/models/ngspice'
 lines=['374MOS page tree node with8isolatedwrite branches',f'.include {pre}/design.spice',f'.lib {pre}/sm141064.spice typical','.param sw_stat_global=0 sw_stat_mismatch=0','.temp 27','.options klu method=gear reltol=1e-4 vntol=1e-7 abstol=1e-16 gmin=1e-18']+defs+['.global VSUBS','Vsub VSUBS 0 0','Vdd VDD 0 3.3','Vss VSS 0 0','Vcm VCM 0 1.2']
 def instance(tag,c,mapping):lines.append('X'+tag+' '+' '.join(mapping.get(p,p) for p in ports[c])+' '+c)
 def ctrl(n,pts):
  lines.append(f'V{n} {n}_drv 0 PWL('+ ' '.join(f'{t}u {v}' for t,v in pts)+')');instance('b'+n,'gf180_dense_inverter_v1',{'IN':n+'_drv','OUT':n+'_b'});instance('d'+n,'gf180_dense_inverter_v1',{'IN':n+'_b','OUT':n})
 def windows(ww):
  pts=[(0,0)]
  for a,b in ww:pts.extend([(a-.01,0),(a,3.3),(b-.01,3.3),(b,0)])
  return pts+[(40,0)]
 for k in range(3):ctrl(f'A{k}',[(0,0),(11.99,0),(12,3.3),(24.99,3.3),(25,0),(40,0)])
 ctrl('WRITE_CMD',windows([(.5,4),(13,17),(26,30)]));ctrl('READ_CMD',windows([(5,11),(18,24),(31,37)]));ctrl('READ_ENABLE',windows([(5.1,10.9),(18.1,23.9),(31.1,36.9)]))
 targets=[]
 for k in range(8):
  aa=.9+.05*k;bb=1.35-.04*k;cc=1.1+.03*k;targets.append([aa,bb,cc]);lines.extend([f'Vdata{k} DATA{k}_src 0 PWL(0 {aa} 12u {aa} 12.01u {bb} 25u {bb} 25.01u {cc} 40u {cc})',f'Rdata{k} DATA{k}_src DATA{k} 100'])
 for j in range(8):
  instance(f'inv{j}','gf180_dense_inverter_v1',{'IN':f'WRITE{j}','OUT':f'WRITEB{j}'});lines.extend([f'Vr{j} RECOV{j}_src 0 {vb if j==7 else va:.16g}',f'Rr{j} RECOV{j}_src RECOV{j} 100'])
  for k in range(8):
   node=f'CH{j}_DATA{k}';instance(f'tg{j}_{k}','gf180_fixed_body_tg_quarter_shorttracks',{'A':f'DATA{k}','B':node,'EN':f'WRITE{j}','ENB':f'WRITEB{j}'});lines.extend([f'Cload{j}_{k} {node} VSS 100f',f'Rhold{j}_{k} {node} VCM 1e12'])
  for mode in ['WRITE','READ','ENABLE']:lines.append(f'Ccmd{mode}{j} {mode}{j} VSS 100f')
 instance('selector','gf180_shared_page_tree_selector8_v2',{});names=['RECOV']+[f'CH{j}_DATA{k}' for j in range(8) for k in range(8)]+[f'{mode}{j}' for j in range(8) for mode in ['WRITE','READ','ENABLE']];lines+=['Cout RECOV VSS 100f','.save '+' '.join('v('+n+')' for n in names)+' i(Vdd)','.tran .02u 40u 0 .2u','.end'];deck.write_text('\n'.join(lines)+'\n');started=time.monotonic()
 run=subprocess.run(['docker','run','--rm','--network','none','--memory','2g','--cpus','2','--volume',f'{R}:/workspace','--entrypoint','timeout','eventspikeseg:analog-ngspice47','120','ngspice','-b','-r','/workspace/'+raw.relative_to(R).as_posix(),'/workspace/'+deck.relative_to(R).as_posix()],capture_output=True,text=True,timeout=135);lp=rp.with_suffix('.log');log=run.stdout+run.stderr;lp.write_text(log);o={'module_simulation_completed':False,'node_native_MOS':374,'external_categorical_driver_MOS':24,'returncode':run.returncode,'wall_s':time.monotonic()-started,'parent_atlas_wire_RC_included':False,'full_population_5ms_accepted':False,'full_chip_complete':False,'scope':'Native230MOS selector+64native2MOS DATA TG+8native2MOS inverters,childextractedcap retained. One0-7-0 threeepochwrite/read case. AnalogDATA sources100ohm;childDATA100fF/1Tohm fixtures;recovery frozenfromcompletednativefrontend. Checksnode selection/isolation behavior,notresidentstorage orlongtree/fullatlas loading,accuracy or5ms.'}
 if raw.exists() and b'Binary:\n' in raw.read_bytes():
  header,data=raw.read_bytes().split(b'Binary:\n',1);nv=int(re.search(rb'No. Variables:\s*(\d+)',header)[1]);vv=[l.split()[1] for l in header.decode().split('Variables:\n')[1].splitlines() if l.strip()];arr=np.frombuffer(data[:len(data)//(nv*8)*(nv*8)],dtype='<f8').reshape(-1,nv);t=arr[:,0];np.savez_compressed(rp.with_suffix('.npz'),waveforms=arr,variables=np.array(vv));o['last_time_s']=float(t[-1]);o['module_simulation_completed']=bool(run.returncode==0 and abs(t[-1]-40e-6)<1e-12 and np.isfinite(arr).all() and 'aborted' not in log.lower())
  if o['module_simulation_completed']:
   at=lambda n,u:float(np.interp(u*1e-6,t,arr[:,vv.index('v('+n.lower()+')')]));rows=[]
   for ci,(tag,j,before,wu,ru,target) in enumerate([('A_first',0,.45,3.8,10.5,va),('B',7,12.9,16.8,23.5,vb),('A_return',0,25.9,29.8,36.5,va)]):
    selected=[at(f'CH{j}_DATA{k}',wu)-targets[k][ci] for k in range(8)];unselected=[at(f'CH{q}_DATA{k}',wu)-at(f'CH{q}_DATA{k}',before) for q in range(8) if q!=j for k in range(8)];checks=[]
    for mode,u in [('WRITE',wu),('READ',ru),('ENABLE',ru)]:
     vals=[at(f'{mode}{q}',u) for q in range(8)];checks.append(vals[j]>3 and max(v for q,v in enumerate(vals) if q!=j)<.1)
    rows.append({'case':tag,'selected_child':j,'max_selected_DATA_error_v':max(map(abs,selected)),'max_unselected_DATA_change_during_write_v':max(map(abs,unselected)),'recovery_error_v':at('RECOV',ru)-target,'onehot_commands_correct':all(checks)})
   o.update(cases=rows,max_selected_DATA_error_v=max(r['max_selected_DATA_error_v'] for r in rows),max_unselected_DATA_change_during_write_v=max(r['max_unselected_DATA_change_during_write_v'] for r in rows),all_commands_correct=all(r['onehot_commands_correct'] for r in rows));o['provisional_fixture_isolation_observed']=bool(o['all_commands_correct'] and o['max_selected_DATA_error_v']<.01 and o['max_unselected_DATA_change_during_write_v']<.005)
 o['sha256']={p.relative_to(R).as_posix():sha(p) for p in sources+[Path(__file__),deck,lp]};rp.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps({k:v for k,v in o.items() if k!='sha256'},indent=2))
if __name__=='__main__':main()
