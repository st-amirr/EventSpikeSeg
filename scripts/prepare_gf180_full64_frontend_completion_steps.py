"""Prepare bounded extracted transient and publication; preserve every consumed baseline."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[1]
old=R/'scripts/screen_gf180_formatted64_flat_transient_180s.py'
new=R/'scripts/screen_gf180_full64_rms_frontend_flat_transient_v1.py'
assert not new.exists()
s=old.read_text().replace('gf180_formatted_energy64_v3','gf180_full64_rms_frontend_v1')
s=s.replace("q['mos_count']==36*n", "q['mos_count']==2397").replace("'native_mos_count':36*n", "'native_mos_count':2397")
s=s.replace('Ireference BIAS 0 64u','Ireference REDUCER_BIAS 0 64u')
s=s.replace("'Vpen PENALTY 0 1.2',", "'Vpen PENALTY 0 1.2','Vrootref ROOT_REF 0 2.412488477821002','Vstrength STRENGTH 0 1.4','Vmin VMIN 0 1.2','Vmax VMAX 0 1.8','Ifront FRONTEND_BIAS 0 4u','Inf VDD NF_BIAS 1u',")
s=s.replace("+' v(ROOT) i(Vdd)'", "+' v(ROOT) v(RMS_RAW) v(RMS_CLIP) v(ADAPT_AMP) i(Vdd)'")
s=s.replace('w.shape[1]==3','w.shape[1]==6').replace("'supply_current_a':-sample(2,us)", "'rms_raw_v':sample(2,us),'rms_clip_v':sample(3,us),'adapt_amp_v':sample(4,us),'supply_current_a':-sample(5,us)")
dc=R/'scripts/screen_gf180_full64_rms_frontend_dc.py'
h=hashlib.sha256(dc.read_bytes()).hexdigest()[:12]
s=s.replace('gf180_full64_rms_frontend_v1_native_hierarchy_dc_src06716ac6c5d8.json','gf180_full64_rms_frontend_v1_three_native_DC_src'+h+'.json')
s=s.replace('native_full_channel_energy_transient_observed','native_connected_RMS_frontend_transient_observed')
s=s.replace('One180s runtime extension justified by4.97215us of requested6us progress at120s; unchanged circuitry, solver, fixtures and gates. Actual64 candidate-minus-penalty native formatters and full64 energy/mean-root connected in one flat2304MOS2816R1024MIM parent', 'One180s native bound based on completed actual2304MOS full64 baseline6us transient. Actual64 candidate-minus-penalty formatters and full64 energy/mean-root physically drive native high-common-mode buffer, offset conversion, clipping and strength product in one flat2397MOS2866R1056MIM parent')
s=s.replace('No ideal internal candidate-minus-penalty arithmetic or formatted gate drive.', 'No ideal internal candidate-minus-penalty arithmetic, formatted gate drive or ROOT voltage source. Frozen independently calibrated ROOT_REF2.412488477821002V and STRENGTH1.4V remain external, with separate4uA PMOS/1uA NF frontend references.')
s=s.replace('independent frozen source-hierarchy DC report','independent actual connected-source-hierarchy three-level DC report')
new.write_text(s)
p=R/'scripts/publish_gf180_characterization_assembly_20261011.py'
q=R/'scripts/publish_gf180_characterization_assembly_20261011_v2.py';assert not q.exists()
t=p.read_text().replace("cat['characterization_assemblies'].append(entry);cat['revision']", "cat['characterization_assemblies'].append(entry);cat['in_progress_assemblies']=[x for x in cat.get('in_progress_assemblies',[]) if x['cell'] not in {e['cell'] for e in cat['characterization_assemblies']}];cat['revision']",1)
q.write_text(t);print(new);print(q)
