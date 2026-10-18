import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]; base=root/'artifacts/analog_asic/results'
curve=json.loads((base/'gf180_membrane_scale_compact_v23_transfer19.json').read_text())['curve']
req=json.loads((base/'gf180_membrane_scale_hardware_requirements_v1.json').read_text())
pts=[(p['command_v'],p['current_a']) for p in curve]
assert all(pts[i][1]>pts[i+1][1] for i in range(len(pts)-1))
ratio=req['required_scale_ratio_over_pulse_window']; high=pts[0][1]; low=pts[-1][1]; target=high/ratio
v=None
for (v0,i0),(v1,i1) in zip(pts,pts[1:]):
 if i0>=target>=i1:
  v=v0+(target-i0)*(v1-v0)/(i1-i0); break
report={'analysis_completed':True,'source_transfer_report':'artifacts/analog_asic/results/gf180_membrane_scale_compact_v23_transfer19.json','source_requirement_report':'artifacts/analog_asic/results/gf180_membrane_scale_hardware_requirements_v1.json','required_ratio':ratio,'measured_current_ratio_full_0p75_to_2p55':high/low,'target_min_current_for_ratio_a':target,'interpolated_upper_command_v_for_ratio':v,'usable_command_span_v':[pts[0][0],v],'unused_high_voltage_margin_v':pts[-1][0]-v,'interpretation':'The nominal measured PFET current span exceeds the one stated pulse-window ratio. This establishes range coverage only; it does not prove linearity, noise floor, current matching, sign handling, or float recurrence accuracy. Interpolation is between 0.1V sweep points.'}
out=base/'gf180_membrane_scale_compact_v23_transfer_range_check_v1.json';out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
