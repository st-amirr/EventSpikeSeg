"""Evaluate scale-bank coarsening from verified original-float tile ranges."""
import json,math,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'artifacts/analog_asic/results/gf180_float_state_tile_calibration_dc685af8e3_srcc47640d01bc7.json'
OUT=ROOT/'artifacts/analog_asic/results/gf180_membrane_scale_bank_coarsening_v1.json'
assert not OUT.exists()
d=json.loads(SRC.read_text()); sizes=[8,16,32,64,128]
summary=[]
for side in sizes:
 factor=side//8; total_banks=0; total_cells=0; ratios=[]; original_ranges=[]; coarse_ranges=[]
 per_actor={}
 for actor,raw in d['state_tile8_ranges'].items():
  a=np.asarray(raw,dtype=np.float64)[0] # channel x tile-row x tile-col
  channels,h,w=a.shape
  ch=math.ceil(h/factor)*math.ceil(w/factor); total_banks+=channels*ch
  total_cells+=channels*math.ceil(h/factor)*math.ceil(w/factor)*side*side
  local=[]; ar=[]; cr=[]
  for r in range(h):
   for c in range(w):
    rr=r//factor; cc=c//factor
    v=a[:,r,c]
    block=a[:,rr*factor:min((rr+1)*factor,h),cc*factor:min((cc+1)*factor,w)]
    big=block.max(axis=(1,2))
    # Base 8x8 membrane-state holders; edge tiles get fewer state identities.
    cell_count=min(8, d['records'][0].get('height',440)-8*r) * min(8,640-8*c)
    # Per-actor output shape is inferred from number of row/column tiles; calibration uses ceil-mode tiles.
    # Spatial weighting is uniform per tile except edge tile; resolve dimensions from model feature maps below.
    local.extend((0.009153333333333334*big/v).tolist())
    ar.extend(v.tolist()); cr.extend(big.tolist())
  ratios.extend(local); original_ranges.extend(ar); coarse_ranges.extend(cr)
  per_actor[actor]={'channels':channels,'tile8_grid':[h,w],'bank_count':channels*math.ceil(h/factor)*math.ceil(w/factor)}
 x=np.asarray(ratios)
 def pct(q): return float(np.percentile(x,q)) if len(x) else 0.0
 summary.append({'tile_side':side,'scale_bank_count':total_banks,'state_capacity_upper_bound':total_cells,'roundtrip_error_as_percent_of_source_8x8_range':{'median':pct(50),'p95':pct(95),'p99':pct(99),'max':float(x.max()),'fraction_over_1pct':float(np.mean(x>0.01)),'fraction_over_5pct':float(np.mean(x>0.05)),'fraction_over_10pct':float(np.mean(x>0.10))},'scale_range_min':float(min(coarse_ranges)),'scale_range_median':float(np.median(coarse_ranges)),'scale_range_max':float(max(coarse_ranges)),'actors':per_actor})
report={'source_report':SRC.relative_to(ROOT).as_posix(),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'input_tile_side':8,'native_storage_swing_v':[0.75,2.55],'sampled_roundtrip_error_v':0.008238,'error_ratio_to_half_swing':0.008238/0.9,'method':'Coarsened each guarded tile8 range by taking max over adjacent tile blocks; compared the existing 8.238mV sampled roundtrip bound mapped to each coarse scale against each original tile8 local float interval. Counts include each coarse range per actor-channel-spatial block. No model replay or new accuracy claim.','summary':summary,'scope':'Deterministic range analysis only. Coarse-bank representational error proxy excludes actual scale programming/readout error, unseen-scene headroom, nonuniform spatial error weighting, membrane dynamics, noise/PVT and segmentation replay.'}
OUT.write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps({'report':OUT.as_posix(),'summary':[{k:v for k,v in row.items() if k!='actors'} for row in summary]},indent=2))
