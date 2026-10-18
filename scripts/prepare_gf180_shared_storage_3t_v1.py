"""Versioned 3T gain-cell trial: remove complementary write FET, preserve buffered read."""
from pathlib import Path
import json,hashlib,zipfile,datetime
R=Path(__file__).resolve().parents[1]
def main():
 docs=['ACTIVE_TASKS.md','ARCHITECTURE.md','RESULTS.md','DECISIONS.md','PROGRESS.md','project_spec.yaml','AGENTS.md']
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
 archive=R/'artifacts/analog_asic/documentation_history'/('project_docs_before_shared_storage_'+stamp+'.zip')
 archive.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for name in docs:z.write(R/'docs'/name,'docs/'+name)
 archive.with_suffix('.sha256.json').write_text(json.dumps({'archive':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()},indent=2))
 p=R/'scripts/build_gf180_compact_analog_memory_4t_v4.py';s=p.read_text()
 s=s.replace('gf180_compact_analog_memory_4t_v4','gf180_shared_analog_memory_3t_v1')
 s=s.replace("('wp','pfet',.5,.28,800,0),",'')
 s=s.replace("['wn','wp']","['wn']")
 s=s.replace(" enb=gate('wp',400);horizontal('metal2',enb,1400,400)\n",'')
 s=s.replace("[(-440,'p'),(1200,'n')]","[(-440,'p')]")
 s=s.replace(" rect('nwell',(600,-200,1380,250))\n",'')
 s=s.replace("horizontal('metal1',1200,1600,0,38)","horizontal('metal1',1560,1600,0,38)")
 s=s.replace("'WRITEB':('metal2',(1320,380,1360,420)),",'')
 s=s.replace("Xwp STATE WRITEB DATA VDD pfet_03v3 w=.5u l=.28u\\n",'')
 s=s.replace('STATE DATA WRITE WRITEB READ READOUT VCM VDD VSS','STATE DATA WRITE READ READOUT VCM VDD VSS')
 s=s.replace('mos_count=4','mos_count=3')
 a=s.index("  scope='");b=s.index("')\n if r[",a)
 s=s[:a]+"  scope='3T gain-cell candidate: one native NFET write-access, local source-follower and read-select NFET, one 50fF MIM. Row selection and column bias/read processing are shared. The single NFET is evaluated only in the existing 1.0-1.4V storage window with 3.3V wordline; no rail-to-rail write claim. Local buffered read retained to isolate held state from column charge sharing. Fresh physical and native retention/read checks required; no model, accuracy, full-chip or complete periphery acceptance."+s[b:]
 out=p.with_name('build_gf180_shared_analog_memory_3t_v1.py');assert not out.exists();out.write_text(s)
 p=R/'scripts/qualify_gf180_compact_memory_4t_v4_views.py';s=p.read_text().replace('gf180_compact_analog_memory_4t_v4','gf180_shared_analog_memory_3t_v1').replace('mos_count=4','mos_count=3')
 out=p.with_name('qualify_gf180_shared_memory_3t_v1_views.py');assert not out.exists();out.write_text(s)
 active=R/'docs/ACTIVE_TASKS.md';raw=active.read_bytes()
 note=b'\r\n## Shared storage optimization - 2026-10-11\r\n\r\nUser authorized shared membrane access and continued layout/simulation. First bounded candidate:3T/50fF gain cell, single NFET write in existing1.0-1.4V window, local nondestructive buffered read, shared row controls/column processing. Compare against4T bank with actual source/GDS DRC/LVS, extracted5ms hold and selected read; tighten physical bank pitch after cell qualification. A passive shared read requires charge-sharing/restore evidence before replacing local buffers. Do not count unimplemented shared peripherals or capacitor overlap as measured savings. Full goal incomplete.\r\n'
 active.write_bytes(raw+note)
 print(json.dumps({'archive':str(archive),'candidate':'3T buffered gain cell','scripts_prepared':True},indent=2))
if __name__=='__main__':main()
