"""Resume a completed Docker first pass without repeating its hierarchy extraction."""
from pathlib import Path
import hashlib,json,re,sys
import probe_gf180_mos_gate_cap as flow
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cell='gf180_formatted_energy64_v3';out=BASE/'layout'/cell;builder=ROOT/'scripts/build_gf180_formatted_full_channel_energy_v3.py';log=out/'first_pass_recovered.log';assert not (out/'qualification.json').exists();raw=log.read_text();assert re.search(r'Total DRC errors found:\s*0\b',raw) and 'BBOX ' in raw;assert (out/(cell+'.gds')).stat().st_size>1000 and (out/(cell+'.spice')).read_text().rstrip().endswith('.ends');assert not (out/'warnings.feedback').read_text() and not (out/'gds_warnings.feedback').read_text();assert sha(out/'build_source.py')==sha(builder)
 snapshot=out/'first_pass_extraction_snapshot.txt';assert not snapshot.exists();snapshot.write_bytes((out/(cell+'.ext')).read_bytes())
 source=builder.read_text();needle='assert not out.exists();out.mkdir(parents=True)';assert source.count(needle)==1;source=source.replace(needle,'assert out.exists();out.mkdir(parents=True,exist_ok=True)',1);execution=out/'resume_execution_source.py';assert not execution.exists();execution.write_text(source)
 oldmagic=flow.magic;wt=Path.write_text;wb=Path.write_bytes;calls=[0];protected={out/(cell+'.mag'),out/'build_source.py',out/'drc_preflight.log'}
 def write_text(p,text,*args,**kw):
  if p in protected and p.exists():assert p.read_text(encoding=kw.get('encoding') or 'utf-8')==text,p;return len(text)
  if p==out/'qualification.json':
   data=json.loads(text);data['completed_first_pass_recovery']={'container_id':'16bc8def2456','initial_host_timeout_s':120,'native_process_completed_without_restart':True,'recovered_log':log.relative_to(ROOT).as_posix(),'initial_geometry_and_GDS_preserved':True,'capacitance_export_from_preserved_complete_first_pass_ext':True,'GDS_LVS_extraction_disables_linear_capacitance_only':True,'scope':'Source hierarchy extraction completed in the original Docker process after host observation timed out. Reuse completed source/GDS and preserved full extraction snapshot; no rerun of original hierarchy extraction, no deleted capacitor branches or geometry edits. GDS device/port LVS does not require linear capacitance extraction; native capacitor devices remain present. Separate flat passive-cap qualification still required.'};data['input_sha256'].update({p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),execution,snapshot,log]});text=json.dumps(data,indent=2)+'\n'
  return wt(p,text,*args,**kw)
 def write_bytes(p,b):
  if p in protected and p.exists():assert p.read_bytes()==b,p;return len(b)
  return wb(p,b)
 def magic(script):
  calls[0]+=1
  if calls[0]==1:return (out/'drc_preflight.log').read_text()
  if calls[0]==2:return raw
  if calls[0]==3:
   assert 'extract do capacitance\nextract all\n' in script;assert sha(out/(cell+'.ext'))==sha(snapshot);script=script.replace('extract do capacitance\nextract all\n','extract do capacitance\n',1)
  elif calls[0]==4:script=script.replace('extract all\n','extract no capacitance\nextract all\n',1)
  else:raise AssertionError('Unexpected extra Magic call')
  return oldmagic(script)
 Path.write_text=write_text;Path.write_bytes=write_bytes;flow.magic=magic;sys.argv=[str(builder),'--channels','64'];ns={'__file__':str(builder),'__name__':'recovery_execution'}
 try:exec(compile(source,str(execution),'exec'),ns);ns['main']();assert calls[0]==4
 finally:Path.write_text=wt;Path.write_bytes=wb;flow.magic=oldmagic
if __name__=='__main__':main()
