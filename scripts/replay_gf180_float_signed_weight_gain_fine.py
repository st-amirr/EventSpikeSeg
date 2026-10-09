"""Bounded full-frame original-float sensitivity to residual signed weight gain."""
import argparse,hashlib,json,time
from pathlib import Path
import torch
from eventspikeseg.data import DSECRawEventDataset,discover_dsec_records
from eventspikeseg.model import EventSpikeSeg140k
from eventspikeseg.asic.export import EVENTSPIKESEG140K_INFERENCE_STAGES
from eventspikeseg.model_components import ChannelAffine,SpikingStage
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';EXPECTED='c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tensor_digest(t):return hashlib.sha256(t.detach().contiguous().cpu().numpy().tobytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--dataset-root',type=Path,required=True);p.add_argument('--record-index',type=int,default=0);p.add_argument('--deltas',default='0.0001,0.001,0.003');a=p.parse_args();torch.set_num_threads(2)
 ck=ROOT/'artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt';assert digest(ck)==EXPECTED;q=torch.load(ck,map_location='cpu',weights_only=True);assert q['architecture']=='EventSpikeSeg140k' and q['epoch']==58
 seq,frame=q['temporal_protocol']['validation_record_ids'][a.record_index];records=[r for r in discover_dsec_records(a.dataset_root,'train') if r.sequence_id==seq and r.frame_index==frame];assert len(records)==1
 data=DSECRawEventDataset(a.dataset_root,split='train',output_size=(440,640),internal_updates=10,class_count=6,records=records);events,target,_=data[0];inputs=events.unsqueeze(1);valid=target!=255
 m=EventSpikeSeg140k(class_count=6,input_channels=2,internal_updates=10);m.load_state_dict(q['model_state_dict'],strict=True);m.set_mechanism_scale(float(q.get('mechanism_scale',1)))
 for module in m.modules():
  toggle=getattr(module,'set_asic_qat_enabled',None)
  if callable(toggle):toggle(False)
 m.eval();named=dict(m.named_modules());actors=[(name,named[name]) for name in EVENTSPIKESEG140K_INFERENCE_STAGES];assert len(actors)==25 and all(isinstance(mod,SpikingStage) for _,mod in actors)
 original={name:mod.conv.weight.detach().clone() for name,mod in actors};masks={}
 for name,mod in actors:
  gain=mod.transform.op.gain.view(-1,1,1,1) if isinstance(mod.transform.op,ChannelAffine) else 1
  masks[name]=(original[name]*gain)>=0
 def iou(pred):
  truth=target[valid].long();prediction=pred[valid].long();conf=torch.bincount(truth*6+prediction,minlength=36).reshape(6,6);inter=conf.diagonal();union=conf.sum(0)+conf.sum(1)-inter;present=union>0
  return float((inter[present]/union[present]).float().mean()),conf.tolist()
 results=[];baseline=None
 for delta in [0]+[float(v) for v in a.deltas.split(',')]:
  assert 0<=delta<1
  with torch.inference_mode():
   for name,mod in actors:mod.conv.weight.copy_(original[name]*torch.where(masks[name],1+delta,1-delta))
   m.reset();start=time.monotonic();output=m(inputs);pred=output['segmentation_logits'].argmax(1)[0].cpu();metric,conf=iou(pred);runtime=time.monotonic()-start
  if baseline is None:baseline=pred.clone()
  row={'residual_signed_gain_delta':delta,'positive_weight_gain':1+delta,'negative_weight_gain':1-delta,'mean_iou':metric,'pixel_change_fraction':float((pred!=baseline).float().mean()),'confusion':conf,'runtime_seconds':runtime,'prediction_sha256':tensor_digest(pred)};results.append(row);print(json.dumps(row),flush=True);del output
 source=Path(__file__);snap=BASE/'tools/source_snapshots'/('gf180_weight_gain_replay_'+digest(source)+'.py');snap.write_bytes(source.read_bytes())
 files=[ck,source,snap,*sorted((ROOT/'src/eventspikeseg').rglob('*.py'))]
 report={'simulation_completed':True,'checkpoint_sha256':EXPECTED,'checkpoint_epoch':58,'record':{'sequence_id':seq,'frame_index':frame,'validation_record_index':a.record_index},'full_frame_shape':[440,640],'update_count':10,'bin_us':5000,'actor_count':25,'input_sequence_sha256':tensor_digest(inputs),'target_sha256':tensor_digest(target),'results':results,'qat_or_quantized_reference_used':False,'readout_weights_modified':False,'settings':vars(a)|{'dataset_root':str(a.dataset_root)},'scope':'One full DSEC validation-listed record replay through all25 original-float actors using current repository code. Persistent deterministic signed weight-gain perturbation: effective positive coefficients gain1+delta, negatives1-delta; rawconv changed using sign after affine fold, affine not doubled. Perfect state storage/beta/threshold/reset/adaptation/graph/weight timing; no noise/circuit offset/current source calibration or service. Deltas are hypothetical residual error sensitivity, NOT measured device distribution or accepted accuracy threshold. No retraining/QAT/quantized compute. One record is not validation-set accuracy qualification.','original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_5ms_population_service_accepted':False,'full_chip_accepted':False,'sha256':{f.relative_to(ROOT).as_posix():digest(f) for f in files}}
 stem='gf180_float_signed_gain_fine_record'+str(a.record_index)+'_src'+digest(source)[:12];dest=BASE/'results'/(stem+'.json');dest.write_text(json.dumps(report,indent=2)+'\n');print('REPORT '+str(dest),flush=True)
if __name__=='__main__':main()
