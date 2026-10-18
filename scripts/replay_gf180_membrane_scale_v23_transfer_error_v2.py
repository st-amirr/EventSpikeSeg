"""Replay original-float PLIF with the measured v23 scale-transfer residual mapped per bank."""
import argparse,hashlib,json,time,math
from pathlib import Path
import numpy as np
import torch
from eventspikeseg.data import DSECRawEventDataset,discover_dsec_records
from eventspikeseg.model import EventSpikeSeg140k
from eventspikeseg.asic.export import EVENTSPIKESEG140K_INFERENCE_STAGES
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';EXPECTED='c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def td(x):return hashlib.sha256(x.detach().contiguous().cpu().numpy().tobytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--dataset-root',type=Path,required=True);ap.add_argument('--calibration-report',type=Path,required=True);ap.add_argument('--record-index',type=int,default=0);args=ap.parse_args();torch.set_num_threads(2)
 checkpoint=ROOT/'artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt';assert digest(checkpoint)==EXPECTED;saved=torch.load(checkpoint,map_location='cpu',weights_only=True);assert saved['epoch']==58 and saved['architecture']=='EventSpikeSeg140k'
 sequence,frame=saved['temporal_protocol']['validation_record_ids'][args.record_index];records=[r for r in discover_dsec_records(args.dataset_root,'train') if r.sequence_id==sequence and r.frame_index==frame];assert len(records)==1
 ds=DSECRawEventDataset(args.dataset_root,split='train',output_size=(440,640),internal_updates=10,class_count=6,records=records);events,target,_=ds[0];inputs=events.unsqueeze(1);valid=target!=255
 model=EventSpikeSeg140k(class_count=6,input_channels=2,internal_updates=10);model.load_state_dict(saved['model_state_dict'],strict=True);model.set_mechanism_scale(float(saved.get('mechanism_scale',1)))
 for module in model.modules():
  toggle=getattr(module,'set_asic_qat_enabled',None)
  if callable(toggle):toggle(False)
 model.eval();named=dict(model.named_modules());neurons={n:named[n].neuron for n in EVENTSPIKESEG140K_INFERENCE_STAGES};assert len(neurons)==25
 cal=json.loads(args.calibration_report.read_text());assert cal['checkpoint_sha256']==EXPECTED
 tile_ranges=cal['state_tile8_ranges'];all_scales=np.sort(np.concatenate([.9/np.asarray(x,dtype=np.float64)[0].reshape(-1) for x in tile_ranges.values()]));assert len(all_scales)==490240
 measured=json.loads((BASE/'results/gf180_membrane_scale_v23_bank_map_v5_validate81pt_batched.json').read_text());quantiles=np.asarray([x['quantile'] for x in measured['cases']]);errors=np.asarray([x['relative_current_error'] for x in measured['cases']]);assert len(quantiles)==81
 epsmaps={};range_maps={}
 for name,raw in tile_ranges.items():
  a=np.asarray(raw,dtype=np.float64)[0];c,h,w=a.shape;sc=.9/a;rank=np.searchsorted(all_scales,sc,side='left')/(len(all_scales)-1);eps=np.interp(rank,quantiles,errors);epsmaps[name]=eps
  down=round(440/(8*h));down=2**round(np.log2(max(1,down)));fh=int(np.ceil(440/down));fw=int(np.ceil(640/down));assert int(np.ceil(fh/8))==h and int(np.ceil(fw/8))==w
  range_maps[name]={'eps':eps,'h':h,'w':w}
 eps_all=np.concatenate([x.reshape(-1) for x in epsmaps.values()]);maxabs=float(np.max(np.abs(errors)));errstate={'mode':'none','clip_count':0,'state_count':0}
 for name,neuron in neurons.items():
  original=neuron.forward
  def wrapped(current,elapsed_steps=1.0,update_mask=None,_name=name,_neuron=neuron,_original=original):
   mode=errstate['mode']
   if mode!='none':
    info=range_maps[_name];a=info['eps'];
    if mode=='positive_max':a=np.full_like(a,maxabs)
    elif mode=='negative_max':a=np.full_like(a,-maxabs)
    e=torch.as_tensor(a,dtype=current.dtype,device=current.device).view(1,a.shape[0],info['h'],info['w']).repeat_interleave(8,2).repeat_interleave(8,3)[:,:,:current.shape[2],:current.shape[3]]
    current=current*(1.0+e)
   return _original(current,elapsed_steps,update_mask)
  neuron.forward=wrapped
 def metric(pred):
  conf=torch.bincount(target[valid].long()*6+pred[valid].long(),minlength=36).reshape(6,6);inter=conf.diagonal();union=conf.sum(0)+conf.sum(1)-inter;present=union>0;return float((inter[present]/union[present]).float().mean()),conf.tolist()
 modes=['none','measured_transfer_residual','positive_max_transfer_residual','negative_max_transfer_residual'];rows=[];baseline=None
 for mode in modes:
  errstate.update(mode=mode,clip_count=0,state_count=0);start=time.monotonic()
  with torch.inference_mode():
   output=model(inputs);pred=output['segmentation_logits'].argmax(1)[0].cpu();miou,conf=metric(pred)
  if baseline is None:
   baseline=pred.clone();expected=next(r['prediction_sha256'] for r in cal['records'] if r['validation_record_index']==args.record_index);assert td(pred)==expected,'original-float baseline does not match calibration'
  rows.append({'mode':mode,'mean_iou':miou,'pixel_change_fraction':float((pred!=baseline).float().mean()),'prediction_sha256':td(pred),'runtime_seconds':time.monotonic()-start});print(json.dumps(rows[-1]),flush=True);del output
 report={'simulation_completed':True,'checkpoint_sha256':EXPECTED,'checkpoint_epoch':58,'record_index':args.record_index,'record':{'sequence_id':sequence,'frame_index':frame},'input_sequence_sha256':td(inputs),'target_sha256':td(target),'full_frame_shape':[440,640],'updates':10,'actors':25,'results':rows,'measured_transfer_residual_quantiles':{'points':len(errors),'max_abs_relative_current_error':maxabs,'min_relative_error':float(errors.min()),'max_relative_error':float(errors.max())},'error_model':'Multiply each incoming float synaptic current by 1+epsilon for that channel/tile bank, where epsilon is linearly interpolated from 81 extracted v23 5ms current residuals versus bank-scale quantile. Additional positive/negative max-residual stress modes use the largest measured absolute residual. Original epoch58 float weights/equations retained; QAT disabled. This models the measured scale-current calibration residual only, not capacitor arithmetic, PVT, noise, mismatch or nonlinearity between sampled points.','scope':'One-record original-float software recurrence replay under the measured per-bank scale-cell calibration residual. Does not establish full validation accuracy, analog accumulation, full-chip service or 5ms population throughput.','qat_or_quantized_reference_used':False,'accuracy_accepted':False,'full_population_5ms_accepted':False,'sha256':{'script':digest(Path(__file__)),'calibration_report':digest(args.calibration_report),'transfer_validation':digest(BASE/'results/gf180_membrane_scale_v23_bank_map_v5_validate81pt_batched.json'),'checkpoint':digest(checkpoint)}}
 out=BASE/'results'/f'gf180_membrane_scale_v23_transfer_replay_record{args.record_index}_v2.json';assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n');print('REPORT',out)
if __name__=='__main__':main()

