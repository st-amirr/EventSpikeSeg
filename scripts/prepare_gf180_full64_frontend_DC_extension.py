"""One measured runtime extension; preserve failed initial three-case native report."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];B=R/'artifacts/analog_asic'
old=R/'scripts/screen_gf180_full64_rms_frontend_dc.py'
new=R/'scripts/screen_gf180_full64_rms_frontend_dc_300s.py'
assert not new.exists()
s=old.read_text().replace("'120','ngspice'","'300','ngspice'").replace('timeout=135','timeout=315')
s=s.replace("'scope':'Actual extracted", "'scope':'One300s runtime extension after the initial120s run completed zero and half-active native operating points but timed out during the third point. Same actual geometry, models, bias domains, solver tolerances, three fixtures and frozen reference; no calibration change. Actual extracted",1)
new.write_text(s)
oldhash=hashlib.sha256(old.read_bytes()).hexdigest()[:12]
newhash=hashlib.sha256(new.read_bytes()).hexdigest()[:12]
p=R/'scripts/screen_gf180_full64_rms_frontend_flat_transient_v1.py'
assert not list((B/'tools/source_snapshots').glob('gf180_full64_rms_frontend_v1_three_transient_src*.py'))
t=p.read_text().replace('_three_native_DC_src'+oldhash+'.json','_three_native_DC_src'+newhash+'.json')
p.write_text(t)
report=B/'results/gf180_full64_frontend_DC_runtime_review_v1.json';assert not report.exists()
report.write_text(json.dumps({'runtime_review_completed':True,'initial_timeout_seconds':120,'native_operating_points_completed':2,'requested_points':3,'estimated_equal_cost_three_point_runtime_seconds':180,'one_extension_seconds':300,'reason':'Two actual completed native operating points establish progress; allow margin for observed dynamic gmin stepping during continuation. No geometry, voltage reference, model, tolerance or case changes. No repeated runtime extensions.','original_report':'artifacts/analog_asic/results/gf180_full64_rms_frontend_v1_three_native_DC_src'+oldhash+'.json','extended_report':'artifacts/analog_asic/results/gf180_full64_rms_frontend_v1_three_native_DC_src'+newhash+'.json','full_chip_layout_complete':False},indent=2)+'\n')
print(new)
