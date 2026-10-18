"""Replay original-float SNN with bounded per-bank capacitor roundtrip-error surrogates."""
import argparse, hashlib, json, time
from pathlib import Path
import numpy as np
import torch
from eventspikeseg.data import DSECRawEventDataset, discover_dsec_records
from eventspikeseg.model import EventSpikeSeg140k
from eventspikeseg.asic.export import EVENTSPIKESEG140K_INFERENCE_STAGES
ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT/'artifacts/analog_asic'
EXPECTED='c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def td(x): return hashlib.sha256(x.detach().contiguous().cpu().numpy().tobytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--dataset-root',type=Path,required=True); ap.add_argument('--calibration-report',type=Path,required=True); ap.add_argument('--record-index',type=int,default=0); args=ap.parse_args()
 torch.set_num_threads(2); checkpoint=ROOT/'artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt'; assert digest(checkpoint)==EXPECTED
 saved=torch.load(checkpoint,map_location='cpu',weights_only=True); assert saved['epoch']==58 and saved['architecture']=='EventSpikeSeg140k'
 sequence,frame=saved['temporal_protocol']['validation_record_ids'][args.record_index]
 records=[r for r in discover_dsec_records(args.dataset_root,'train') if r.sequence_id==sequence and r.frame_index==frame]; assert len(records)==1
 ds=DSECRawEventDataset(args.dataset_root,split='train',output_size=(440,640),internal_updates=10,class_count=6,records=records); events,target,_=ds[0]; inputs=events.unsqueeze(1)
 valid=target!=255; model=EventSpikeSeg140k(class_count=6,input_channels=2,internal_updates=10);model.load_state_dict(saved['model_state_dict'],strict=True);model.set_mechanism_scale(float(saved.get('mechanism_scale',1)))
 for m in model.modules():
  toggle=getattr(m,'set_asic_qat_enabled',None)
  if callable(toggle):toggle(False)
 model.eval(); named=dict(model.named_modules()); neurons={n:named[n].neuron for n in EVENTSPIKESEG140K_INFERENCE_STAGES}; assert len(neurons)==25
 cal=json.loads(args.calibration_report.read_text(encoding='utf-8')); assert cal['checkpoint_sha256']==EXPECTED
 tile_maps={}
 for name,raw in cal['state_tile8_ranges'].items():
  a=np.asarray(raw,dtype=np.float64)[0]; c,h,w=a.shape
  down=round(440/(8*h));down=2**round(np.log2(max(1,down))); fh=int(np.ceil(440/down));fw=int(np.ceil(640/down)); assert int(np.ceil(fh/8))==h and int(np.ceil(fw/8))==w
  tile_maps[name]={'a':a,'fh':fh,'fw':fw}
 errmode={'mode':'none','clip_count':0,'state_count':0}
 for name,neuron in neurons.items():
  original=neuron.forward
  def wrapped(current,elapsed_steps=1.0,update_mask=None,_name=name,_neuron=neuron,_original=original):
   spikes=_original(current,elapsed_steps,update_mask)
   mode=errmode['mode']
   if mode!='none':
    info=tile_maps[_name]; a=info['a']; fac=2 if mode.startswith('tile16') else 1
    h,w=a.shape[1:]; oh=(h+fac-1)//fac;ow=(w+fac-1)//fac
    coarse=np.zeros((a.shape[0],oh,ow))
    for r in range(oh):
     for c in range(ow):coarse[:,r,c]=a[:,r*fac:min((r+1)*fac,h),c*fac:min((c+1)*fac,w)].max(axis=(1,2))
    side=8*fac; rr=torch.tensor(coarse,dtype=current.dtype).view(1,a.shape[0],oh,ow).repeat_interleave(side,2).repeat_interleave(side,3)[:,:,:_neuron.membrane.shape[2],:_neuron.membrane.shape[3]]
    bound=rr*(0.008238/0.9)
    if mode.endswith('positive'): sign=1.0
    elif mode.endswith('negative'):sign=-1.0
    else:
     iy=torch.arange(_neuron.membrane.shape[2])//side;ix=torch.arange(_neuron.membrane.shape[3])//side
     pattern=((iy[:,None]+ix[None,:])%2*2-1).to(current.dtype)*-1
     sign=pattern.view(1,1,*pattern.shape)
    candidate=_neuron.membrane+sign*bound
    errmode['clip_count']+=int((candidate.abs()>rr).sum());errmode['state_count']+=candidate.numel()
    _neuron.membrane=torch.maximum(torch.minimum(candidate,rr),-rr)
   return spikes
  neuron.forward=wrapped
 def metric(pred):
  conf=torch.bincount(target[valid].long()*6+pred[valid].long(),minlength=36).reshape(6,6); inter=conf.diagonal();union=conf.sum(0)+conf.sum(1)-inter;present=union>0
  return float((inter[present]/union[present]).float().mean()),conf.tolist()
 modes=['none','tile8_alternating','tile16_alternating','tile16_positive','tile16_negative']; rows=[]; baseline=None
 for mode in modes:
  errmode.update(mode=mode,clip_count=0,state_count=0);start=time.monotonic()
  with torch.inference_mode():
   output=model(inputs);pred=output['segmentation_logits'].argmax(1)[0].cpu();miou,conf=metric(pred)
  if baseline is None:
   baseline=pred.clone()
   expected=next(r['prediction_sha256'] for r in cal['records'] if r['validation_record_index']==args.record_index)
   assert td(pred)==expected, 'original-float baseline does not match saved calibration'
  rows.append({'mode':mode,'mean_iou':miou,'pixel_change_fraction':float((pred!=baseline).float().mean()),'membrane_clip_fraction':errmode['clip_count']/max(1,errmode['state_count']),'confusion':conf,'prediction_sha256':td(pred),'runtime_seconds':time.monotonic()-start});print(json.dumps(rows[-1]),flush=True)
  del output
 report={'simulation_completed':True,'checkpoint_sha256':EXPECTED,'checkpoint_epoch':58,'record_index':args.record_index,'record':{'sequence_id':sequence,'frame_index':frame},'input_sequence_sha256':td(inputs),'target_sha256':td(target),'full_frame_shape':[440,640],'updates':10,'actors':25,'results':rows,'error_model':'After each PLIF forward update, add a bounded state perturbation equal to the measured 8.238mV roundtrip error mapped through the bank voltage range; clip to bank rails. Alternating tile signs is a balanced stress surrogate; positive/negative cases are biased stress bounds. Not a measured distribution or circuit simulation. Weights/checkpoint remain original float; QAT disabled.','scope':'One-record software recurrence replay to screen 16x16 bank coarsening against 8x8 using the native sampled roundtrip-error bound. Does not include actual scale writer/current transfer, per-event analog arithmetic errors, PVT/noise, unseen scenes, or full validation acceptance.','qat_or_quantized_reference_used':False,'accuracy_accepted':False,'full_population_5ms_accepted':False}
 report['sha256']={'scripts':digest(Path(__file__)),'calibration':digest(args.calibration_report),'checkpoint':digest(checkpoint)}
 out=BASE/'results'/f'gf180_membrane_scale_coarsening_replay_record{args.record_index}_v2.json';assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('REPORT',out)
if __name__=='__main__':main()
