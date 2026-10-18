"""Executed original-float beta/channel state inventory for native local-update design."""
import hashlib,json,math
from pathlib import Path
import torch
from eventspikeseg.model import EventSpikeSeg140k
from eventspikeseg.asic.export import EVENTSPIKESEG140K_INFERENCE_STAGES
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic/results';EXPECTED='c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=BASE/'gf180_executed_float_beta_inventory.json';assert not out.exists();p=ROOT/'artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt';assert sha(p)==EXPECTED;d=torch.load(p,map_location='cpu',weights_only=True);assert d['epoch']==58
 model=EventSpikeSeg140k(class_count=6,input_channels=2,internal_updates=10);model.load_state_dict(d['model_state_dict'],strict=True);model.set_mechanism_scale(float(d.get('mechanism_scale',1)));model.eval()
 for m in model.modules():
  f=getattr(m,'set_asic_qat_enabled',None)
  if callable(f):f(False)
 activity=next(BASE.glob('gf180_float_bin_activity_record8_src*.json'));a=json.loads(activity.read_text());assert a['prior_baseline_reproduced'];named=dict(model.named_modules());rows=[];weighted=[]
 for name in EVENTSPIKESEG140K_INFERENCE_STAGES:
  values=named[name].neuron.beta.detach().tolist();states=a['activity'][name]['destinations'];assert states%len(values)==0;perchannel=states//len(values)
  rows.append({'actor':name,'states_per_channel':perchannel,'beta':values,'ideal_aux_to_state_cap_ratio':[1/v-1 for v in values]});weighted.extend((v,perchannel) for v in values)
 assert sum(n for v,n in weighted)==30976000
 ordered=sorted(weighted);total=sum(n for v,n in ordered)
 def quantile(q):
  running=0
  for v,n in ordered:
   running+=n
   if running>=q*total:return v
 result={'measurement_completed':True,'checkpoint_sha256':EXPECTED,'executed_actors':len(rows),'executed_beta_channels':len(weighted),'resident_membranes':total,'beta_min':min(v for v,n in weighted),'beta_max':max(v for v,n in weighted),'neuron_weighted_beta_quantiles':{str(q):quantile(q) for q in [.1,.5,.9]},'resident_states_by_beta_band':{label:sum(n for v,n in weighted if lo<=v<hi) for label,lo,hi in [('below0p8',0,.8),('0p8_to0p9',.8,.9),('0p9_to0p95',.9,.95),('0p95_to1',.95,1)]},'actors':rows,'scope':'Executed25actors only, ordinary float sigmoid(beta_logit),QAT off, no rounding to power-of-two or parameter/model edits. Ideal Caux/Cstate formula gives intended capacitive ratio, not actual native switch/parasitic response or accepted physical implementation. Activity inventory sizes reproduced previously; no inference forwards in this extraction.','acceptance':{'resident_beta':False,'complete_PLIF':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{f.relative_to(ROOT).as_posix():sha(f) for f in [Path(__file__),p,activity,*sorted((ROOT/'src/eventspikeseg').rglob('*.py'))]}}
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:result[k] for k in ['executed_beta_channels','beta_min','beta_max','neuron_weighted_beta_quantiles','resident_states_by_beta_band']}))
if __name__=='__main__':main()
