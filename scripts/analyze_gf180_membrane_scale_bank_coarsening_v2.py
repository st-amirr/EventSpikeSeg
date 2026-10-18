"""Corrected range-only bank coarsening with real border-tile state weights."""
import json,math,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'artifacts/analog_asic/results/gf180_float_state_tile_calibration_dc685af8e3_srcc47640d01bc7.json'
OUT=ROOT/'artifacts/analog_asic/results/gf180_membrane_scale_bank_coarsening_v2.json'
assert not OUT.exists(); d=json.loads(SRC.read_text()); sides=[8,16,32,64,128]; output=[]
for side in sides:
 factor=side//8; banks=0; samples=[]; weights=[]; coarsevals=[]; active_states=0
 for actor,raw in d['state_tile8_ranges'].items():
  a=np.asarray(raw,dtype=float)[0]; c,h,w=a.shape
  down=round(440/(8*h)); down=2**round(math.log2(max(1,down)))
  fh=math.ceil(440/down); fw=math.ceil(640/down)
  assert math.ceil(fh/8)==h and math.ceil(fw/8)==w,(actor,h,w,fh,fw)
  active_states+=c*fh*fw
  banks+=c*math.ceil(h/factor)*math.ceil(w/factor)
  for r in range(h):
   for col in range(w):
    coarse=a[:,(r//factor)*factor:min((r//factor+1)*factor,h),(col//factor)*factor:min((col//factor+1)*factor,w)].max(axis=(1,2))
    base=a[:,r,col]
    n=min(8,fh-r*8)*min(8,fw-col*8)*c
    ratios=0.008238/0.9*coarse/base
    samples.extend(ratios.tolist()); weights.extend([n/c]*c); coarsevals.extend(coarse.tolist())
 x=np.asarray(samples); wt=np.asarray(weights)
 order=np.argsort(x); sx=x[order]; sw=wt[order]; cum=np.cumsum(sw)/np.sum(sw)
 def wp(q):return float(sx[min(np.searchsorted(cum,q),len(sx)-1)])
 pct=lambda q: wp(q)*100
 output.append({'tile_side':side,'scale_bank_count':banks,'state_identity_count':active_states,'roundtrip_error_percent_of_original_8x8_range':{'median':pct(.5),'p95':pct(.95),'p99':pct(.99),'max':float(x.max()*100),'states_over_1pct':float(np.sum(wt[x>.01])/np.sum(wt)),'states_over_5pct':float(np.sum(wt[x>.05])/np.sum(wt)),'states_over_10pct':float(np.sum(wt[x>.10])/np.sum(wt))},'coarsened_scale_range_model_units':{'min':float(min(coarsevals)),'median':float(np.median(coarsevals)),'max':float(max(coarsevals))}})
report={'source_report':SRC.relative_to(ROOT).as_posix(),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'sampled_roundtrip_error_v':0.008238,'native_differential_half_swing_v':0.9,'method':'Merge adjacent original guarded 8x8 ranges by maximum, then compare the same tested 8.238mV read/restore error mapped to the coarse-bank range against each underlying original 8x8 range. Weight statistics by actual membrane identities, accounting for cropped feature-map edge tiles.','summary':output,'scope':'Range-only estimate; does not simulate coarsened analog recurrence, local event values, scene accuracy or unseen-scene clipping. No full-float claim.'}
OUT.write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps({'report':OUT.as_posix(),'summary':output},indent=2))
