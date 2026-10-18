"""Actual-activity sensitivity to measured per-event state bias; not native model validation."""
import argparse,hashlib,json,time
from pathlib import Path
import torch
import torch.nn.functional as F
from eventspikeseg.data import DSECRawEventDataset,discover_dsec_records
from eventspikeseg.model import EventSpikeSeg140k
from eventspikeseg.asic.export import EVENTSPIKESEG140K_INFERENCE_STAGES
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic'
EXPECTED='c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tsha(t):return hashlib.sha256(t.detach().cpu().contiguous().numpy().tobytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dataset-root',type=Path,required=True);p.add_argument('--record-index',type=int,default=8);a=p.parse_args();torch.set_num_threads(2)
 audit=BASE/'results/gf180_tracking_parking_boundary.json';physical=json.loads(audit.read_text(encoding='utf-8'))
 rows=[r for r in physical['integrated_tracking_cases'] if r['completed'] and 'fourbank' in r['report'] and abs(r['settings']['preload_differential_v'])>.01]
 coefficients=[];physical_files=[audit]
 for row in rows:
  rp=ROOT/row['report'];assert sha(rp)==row['sha256'];physical_files.append(rp)
  # Locate matching same-hierarchy, same-program and same-step zero control.
  r=json.loads(rp.read_text(encoding='utf-8'));m=r['measurements'];settings=r['settings']
  controls=[x for x in physical['integrated_tracking_cases'] if x['completed'] and 'fourbank' in x['report'] and x['settings']['preload_differential_v']==0 and all(x['settings'][k]==settings[k] for k in ['pf_program_levels','max_step_ns','cell_order'])]
  assert len(controls)==1;c=controls[0];cp=ROOT/c['report'];assert sha(cp)==c['sha256'];physical_files.append(cp)
  state_delta=m['signal_before']-c['measurements']['signal_before']
  coefficients.extend([(m[f'eventstep_{i}']-c['measurements'][f'eventstep_{i}'])/state_delta for i in range(4)])
 assert len(coefficients)>=8 and all(0<v<1e-3 for v in coefficients)
 k=max(coefficients) # conservative among these eight finite differences only
 checkpoint=ROOT/'artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt';assert sha(checkpoint)==EXPECTED
 saved=torch.load(checkpoint,map_location='cpu',weights_only=True);assert saved['epoch']==58
 sequence,frame=saved['temporal_protocol']['validation_record_ids'][a.record_index]
 records=[r for r in discover_dsec_records(a.dataset_root,'train') if r.sequence_id==sequence and r.frame_index==frame];assert len(records)==1
 dataset=DSECRawEventDataset(a.dataset_root,split='train',output_size=(440,640),internal_updates=10,class_count=6,records=records)
 events,target,_=dataset[0];inputs=events.unsqueeze(1);assert torch.all(inputs>=0) and torch.equal(inputs,inputs.round())
 model=EventSpikeSeg140k(class_count=6,input_channels=2,internal_updates=10);model.load_state_dict(saved['model_state_dict'],strict=True);model.set_mechanism_scale(float(saved.get('mechanism_scale',1)));model.eval()
 for module in model.modules():
  toggle=getattr(module,'set_asic_qat_enabled',None)
  if callable(toggle):toggle(False)
 named=dict(model.named_modules());stages={n:named[n] for n in EVENTSPIKESEG140K_INFERENCE_STAGES};assert len(stages)==25
 active={'policy':'baseline'};pending={};activity={};error_stats={};hooks=[]
 for name,stage in stages.items():
  def before(module,args,_name=name):
   seq=args[0];t,n=seq.shape[:2];flat=seq.reshape(t*n,*seq.shape[2:]).float();assert bool((flat>=0).all()) and torch.equal(flat,flat.round())
   conv=module.conv;g=conv.groups;counts=F.conv2d(flat,torch.ones((g,conv.in_channels//g,*conv.kernel_size),device=flat.device),stride=conv.stride,padding=conv.padding,dilation=conv.dilation,groups=g).reshape(t,n,g,-1)
   pending[_name]={'counts':counts,'index':0,'groups':g,'per_group':conv.out_channels//g}
   expanded_total=int(counts.sum(dtype=torch.float64))*(conv.out_channels//g)
   activity[_name]={'weighted_event_deliveries':expanded_total,'max_events_per_state_per_bin':int(counts.max()),'mean_events_per_state_per_bin':float(counts.float().mean()),'state_updates':counts.numel()*(conv.out_channels//g)}
  hooks.append(stage.register_forward_pre_hook(before))
  def after(module,args,output,_name=name):pending.pop(_name)
  hooks.append(stage.register_forward_hook(after))
  neuron=stage.neuron;base=neuron._candidate_membrane
  def candidate(current,elapsed,_name=name,_neuron=neuron,_base=base):
   q=pending[_name];idx=q['index'];q['index']+=1;result=_base(current,elapsed)
   if active['policy']=='baseline' or (active['policy']=='stem_only' and _name!='stem'):return result
   n,c,h,w=result.shape;count=q['counts'][idx].reshape(n,q['groups'],1,h,w)
   gain=torch.expm1(count*float(torch.log1p(torch.tensor(k))))
   # Midpoint approximation: charge evolves from leaked previous state toward
   # the summed-current endpoint. Actual ordering within a bin is unavailable.
   midpoint=result-.5*current
   error=(gain*midpoint.reshape(n,q['groups'],q['per_group'],h,w)).reshape_as(result)
   stats=error_stats.setdefault(_name,{'max_abs_model_error':0.0,'sum_abs_model_error':0.0,'elements':0})
   stats['max_abs_model_error']=max(stats['max_abs_model_error'],float(error.abs().max()));stats['sum_abs_model_error']+=float(error.abs().sum());stats['elements']+=error.numel()
   return result+error
  neuron._candidate_membrane=candidate
 stem=Path(__file__).stem+f'_record{a.record_index}_src'+sha(Path(__file__))[:12];progress=BASE/'results'/(stem+'_progress.jsonl');assert not progress.exists()
 results=[];baseline=None;valid=target!=255
 for policy in ['baseline','stem_only','all_actors_extrapolation']:
  active['policy']=policy;activity.clear();error_stats.clear();start=time.monotonic()
  with torch.inference_mode():
   model.reset()
   output=model(inputs);prediction=output['segmentation_logits'].argmax(1)[0].cpu()
  assert not pending
  confusion=torch.bincount(target[valid].long()*6+prediction[valid].long(),minlength=36).reshape(6,6);inter=confusion.diagonal();union=confusion.sum(0)+confusion.sum(1)-inter
  if baseline is None:baseline=prediction.clone()
  row={'policy':policy,'mean_iou':float((inter[union>0]/union[union>0]).float().mean()),'prediction_sha256':tsha(prediction),'pixel_change_fraction':float((prediction!=baseline).float().mean()),'runtime_seconds':time.monotonic()-start,'activity':dict(activity),'systematic_error':dict(error_stats),'confusion':confusion.tolist()};results.append(row)
  with progress.open('a',encoding='utf-8') as f:f.write(json.dumps(row)+'\n')
  print(json.dumps({key:row[key] for key in ['policy','mean_iou','pixel_change_fraction','runtime_seconds']}),flush=True)
  del output
 source=Path(__file__);snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(source.read_bytes())
 files=set([checkpoint,source,snap,progress,*physical_files,*sorted((ROOT/'src/eventspikeseg').rglob('*.py'))])
 report={'simulation_completed':True,'checkpoint_sha256':EXPECTED,'record_index':a.record_index,'record':{'sequence':sequence,'frame':frame},'input_sequence_sha256':tsha(inputs),'target_sha256':tsha(target),'state_sensitivity_coefficients':coefficients,'selected_coefficient':k,'results':results,'scope':'Original float model/QAToff/unchanged weights. Actual per-destination presynaptic event counts via grouped all-one connectivity convolution; raw multiplicity preserved. Diagnostic per-event law V<-V*(1+k) extrapolated from eight finite differences at two source weights, one seed and about+/-90mV state. Midpoint aggregate expm1(N*log1p(k))*(beta*previous_state+0.5*summed_current) approximates within-bin ordering; not an exact packet-by-packet reference. Stem-only extends measured channel2 behavior to the stem; all-actor case additionally extrapolates to unmeasured actors. No random noise, clipping, reference/programming error, absolute-state readout, service or native whole-model SPICE. One heldout/same sequence; not accuracy acceptance. Actual error under varied weights/state/order remains unqualified.','qat_or_quantized_reference_used':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_chip_accepted':False,'sha256':{f.relative_to(ROOT).as_posix():sha(f) for f in sorted(files)}}
 rp=BASE/'results'/(stem+'.json');rp.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('REPORT '+str(rp),flush=True)
if __name__=='__main__':main()
