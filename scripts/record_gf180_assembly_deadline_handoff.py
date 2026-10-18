"""Freeze terminal startup evidence and advance the operational assembly index."""
from pathlib import Path
import datetime, hashlib, json, re, zipfile

R = Path(__file__).resolve().parents[1]
B = R/'artifacts/analog_asic'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p): return p.relative_to(R).as_posix()

rp = B/'results/gf180_scheduled_writer_startup_branch_close_v1.json'
assert not rp.exists()
reports = [B/'results'/('gf180_scheduled_rms_resident_write_v1_one_native_sequence_src'+h+'.json')
           for h in ['fef0a09917c6','935c0ad66755','754dc752df1b']]
cases = []
for p in reports:
    r = json.loads(p.read_text())
    lp = p.with_suffix('.log')
    values = re.findall(r'Reference value\s*:\s*([\deE.+-]+)',lp.read_text())
    cases.append({'report':rel(p),'completed':r['module_simulation_completed'],
                  'returncode':r['simulator_returncode'],
                  'last_logged_simulation_time_s':float(values[-1]) if values else None})
assert not any(x['completed'] for x in cases)
rp.write_text(json.dumps({'branch_review_completed':True,'cases':cases,
    'finding':'Matched UIC startup did not resolve native connected sequencing runtime. Native clock-driver repair and UIC method change both remained incomplete; no further startup or tolerance sweep.',
    'retained_evidence':'618MOS controller/writer source/GDS/flat/LEF physical qualification complete.374MOS controller native sequence and236MOS writer native analog sequence independently completed; this does not prove joined loaded sequencing.',
    'next_action':'Join the completed64-channel native formatter/reducer to the qualified RMS clip/strength frontend; keep its actual gate-input isolation buffer and separate bias domains. Preserve known precision errors; complete assembly coverage.',
    'full_chip_layout_complete':False,
    'sha256':{rel(p):sha(p) for p in [Path(__file__),*reports,*[p.with_suffix('.log') for p in reports]]}},indent=2)+'\n')
old=B/'assembly/article_module_catalog_v62.json';new=B/'assembly/article_module_catalog_v63.json'
assert not new.exists();c=json.loads(old.read_text())
c['in_progress_assemblies']=[x for x in c.get('in_progress_assemblies',[]) if x['cell']!='gf180_formatted_energy64_v3']
c['in_progress_assemblies'].extend([
 {'cell':'gf180_scheduled_rms_resident_write_v1','source_GDS_flat_LEF_complete':True,
  'native_loaded_sequence_complete':False,'branch_review':rel(rp),'next_action':'Retain physical assembly; defer combined native sequencing after unsuccessful bounded startup methods.'},
 {'cell':'gf180_full64_rms_frontend_v1','geometry_prepared':True,
  'source_GDS_flat_LEF_complete':False,'nominal_simulation_complete':False,
  'scope':'Actual full64 root wired to analog clipping/strength frontend. Source physical qualification running; no completion claim.'}])
c['revision']=63;c['previous_catalog']=rel(old);c['sha256'][rel(rp)]=sha(rp)
c['measured_RMS_settling_evidence']='artifacts/analog_asic/results/gf180_formatted64_measured_phase_budget_v1.json'
new.write_text(json.dumps(c,indent=2)+'\n')
docs=[R/'docs'/n for n in ['AGENTS.md','ACTIVE_TASKS.md','ARCHITECTURE.md','DECISIONS.md','RESULTS.md','PROGRESS.md','project_spec.yaml']]
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
archive=B/'documentation_history'/('project_docs_before_deadline_assembly_'+stamp+'.zip')
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
    for p in docs:z.writestr(rel(p),p.read_bytes())
archive.with_suffix('.json').write_text(json.dumps({'archive_sha256':sha(archive),'files':{rel(p):sha(p) for p in docs}},indent=2)+'\n')
p=R/'docs/ACTIVE_TASKS.md';b=p.read_bytes().replace(b'article_module_catalog_v62.json',b'article_module_catalog_v63.json').replace(b'catalog revision62',b'catalog revision63')
b=re.sub(rb'\| Job status \|[^\r\n]+',b'| Job status | Full64 RMS-to-clip/strength physical assembly running (session56586); joined controller/writer startup branch reviewed and deferred after bounded failures. |',b,count=1)
b=b.replace(b'Next: full25actor population hierarchy/interconnect, complete channel reduction and pre-reset RMS sampling.',b'Next: physically join completed full64 channel reduction to RMS clip/strength frontend, then full25actor hierarchy/interconnect. Pre-reset writer/controller physical assembly is complete but joined native sequencing remains incomplete.')
p.write_bytes(b)
p=R/'docs/project_spec.yaml';b=p.read_bytes();h,t=b.split(b'\ndocument:',1)
h=h.replace(b'article_module_catalog_v62.json',b'article_module_catalog_v63.json')
h=re.sub(rb'  live_sessions: [^\r\n]+',b'  live_sessions: [56586]',h,count=1)
h=re.sub(rb'    next_action: [^\r\n]+',b'    next_action: complete_native_full64_RMS_to_clip_strength_assembly_then_dense_full_population_layout',h,count=1)
p.write_bytes(h+b'\ndocument:'+t)
for name,text in [
 ('RESULTS.md','Full64 extracted ROOT reaches the observed10mV DC-error band after1.781us for half-active and1.682us for all-active, within the recorded2us windows. The1.5us gate remains false. These are finite fixture observations, not calibrated model accuracy or5ms service. Native joined controller/writer UIC startup also timed out, last logged0.721us of22us; preserve independent module simulations and defer further tuning. Full64-to-native-clip/strength assembly is now being built.'),
 ('DECISIONS.md','After direct-clock abort, qualified clock-driver timeout and matched UIC-startup timeout, close the native connected controller/writer startup branch for this milestone. Preserve all physical views and incomplete runs; use completed independent native module evidence with the joined-sequencing gap visible. Prioritize actual full64 RMS-to-clip/strength physical integration. No solver-tolerance sweep or accuracy claim.'),
 ('PROGRESS.md','Catalog63 corrects stale full64 in-progress status; completed counts remain20 reusable modules/47 characterization assemblies. Joined controller/writer remains physically qualified with native sequencing incomplete. Full64 RMS/frontend geometry prepared and physical qualification running. Exact prior documentation archive: '+rel(archive)+'.')]:
    p=R/'docs'/name;b=p.read_bytes();i=b.index(b'\n## ')
    p.write_bytes(b[:i]+('\n## Assembly priority and startup branch review - 2026-10-11\n\n'+text+'\n').encode()+b[i:])
print(rp);print(new)
