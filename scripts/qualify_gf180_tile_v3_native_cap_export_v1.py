"""Qualify a native hierarchy-off RC export without editing devices or capacitor values."""
from pathlib import Path
import sys,json,hashlib,re
import probe_gf180_mos_gate_cap as f
from resume_gf180_formatted64_completed_flat_v2 import branches_units
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 c='gf180_shared_analog_compute_tile_v3';d=f.BASE/'layout'/c;old=d/'flat_cap_qualification.json';q=json.loads(old.read_text());a=d/(c+'_flat_cap.spice');b=d/(c+'_flat_hierarchy_off_cap.spice');ext=d/(c+'_flat.ext')
 x=lambda p:[l.split() for l in p.read_text().replace('\n+',' ').splitlines() if l.startswith('X')]
 assert x(a)==x(b) and len(x(b))==593
 cs=branches_units(b,c+'_flat');prior=branches_units(a,c+'_flat');assert len(cs)==3941 and not any(v<0 for v in cs.values())
 added={str(k):v for k,v in cs.items() if k not in prior};changed={str(k):[v,cs.get(k)] for k,v in prior.items() if abs(cs.get(k,0)-v)>1e-20};assert not changed
 assert abs(cs[('C_STATE','VSS')]-1.70294e-12)<1e-18
 q.update(linear_branch_count=len(cs),export_hierarchy=False,device_tokens_identical_to_qualified_flat=True,added_substrate_branches=added,previous_hierarchical_export_missing_substrate_branches=True,scope=q['scope']+' Native hierarchy-off export restores185 omitted substrate branches,including1.70294pF C_STATE-to-VSS. Previous hierarchical-PCAP transient is underloaded and cannot support full extracted precision. Original devices and all existing coupling branches unchanged. No manually fitted or inserted capacitances.')
 files=[old,a,b,ext,d/'export_hierarchy_off_diagnosis.tcl',d/'export_hierarchy_off_diagnosis.log',Path(__file__)]
 q['sha256'].update({p.relative_to(R).as_posix():sha(p) for p in files});p=d/'flat_cap_export_correction_qualification.json';assert not p.exists();p.write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({'native_devices_unchanged':593,'added_substrate_branches':len(added),'total_branches':len(cs),'state_substrate_pF':cs[('C_STATE','VSS')]*1e12}))
if __name__=='__main__':main()
