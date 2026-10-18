"""Map unchanged float base thresholds through the existing fixed tile representation."""
from pathlib import Path
import hashlib,json
import numpy as np
import torch
from eventspikeseg.model import EventSpikeSeg140k
from eventspikeseg.asic.export import EVENTSPIKESEG140K_INFERENCE_STAGES
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'artifacts/analog_asic/results';EXPECTED='c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'gf180_float_threshold_voltage_inventory.json';assert not out.exists();checkpoint=ROOT/'artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt';assert sha(checkpoint)==EXPECTED;d=torch.load(checkpoint,map_location='cpu',weights_only=True);assert d['epoch']==58
 model=EventSpikeSeg140k(class_count=6,input_channels=2,internal_updates=10);model.load_state_dict(d['model_state_dict'],strict=True);model.set_mechanism_scale(float(d.get('mechanism_scale',1)));model.eval()
 for m in model.modules():
  f=getattr(m,'set_asic_qat_enabled',None)
  if callable(f):f(False)
 cp=next(R.glob('gf180_float_state_tile_calibration_*.json'));cal=json.loads(cp.read_text());assert cal['checkpoint_sha256']==EXPECTED;named=dict(model.named_modules());rows=[];offsets=[]
 for name in EVENTSPIKESEG140K_INFERENCE_STAGES:
  n=named[name].neuron;values=n._base_threshold(torch.zeros((1,n.channels,1,1))).detach().tolist();fixed=np.array(cal['channel_fixed_calibration_absmax'][name]);tile=np.array(cal['state_tile8_ranges'][name])[0];gains=np.clip(2**np.floor(np.log2(fixed[:,None,None]/tile)),1,16);delta=.44*np.array(values)[:,None,None]*gains/fixed[:,None,None];offsets.extend(delta.reshape(-1).tolist())
  rows.append({'actor':name,'base_threshold_model_units':values,'fixed_absmax_model_units':fixed.tolist(),'base_threshold_voltage_offset_min_v':delta.reshape(n.channels,-1).min(1).tolist(),'base_threshold_voltage_offset_max_v':delta.reshape(n.channels,-1).max(1).tolist(),'adaptation_kind':n.config.adaptation_kind,'adaptation_enabled':n.config.threshold_adaptation_enabled})
 report={'measurement_completed':True,'checkpoint_sha256':EXPECTED,'half_range_v':.44,'actors':rows,'base_threshold_offset_v_min':min(offsets),'base_threshold_offset_v_max':max(offsets),'unweighted_tile_channel_offset_quantiles_v':{str(q):float(np.quantile(offsets,q)) for q in [.1,.5,.9]},'scope':'Ordinary original float base thresholds, QAT off, mapped through existing records0-7 fixed8x8 range/gain calibration and +/-.44V example representation. Dynamic adaptation penalties and actual conversion/reference circuits omitted. Inventory only, no inference/simulation or tolerance acceptance. Physical comparator1.85V tests are characterization fixtures; their200mV offset from1.65V does not establish actual trained threshold operation.','acceptance':{'threshold_interface':False,'original_float_accuracy':False,'complete_PLIF':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),checkpoint,cp,*sorted((ROOT/'src/eventspikeseg').rglob('*.py'))]}}
 out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:report[k] for k in ['base_threshold_offset_v_min','base_threshold_offset_v_max','unweighted_tile_channel_offset_quantiles_v']},indent=2));print('detail_stem_channel3',json.dumps({k:rows[0][k][3] for k in ['base_threshold_model_units','fixed_absmax_model_units','base_threshold_voltage_offset_min_v','base_threshold_voltage_offset_max_v']}))
if __name__=='__main__':main()
