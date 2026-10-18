"""Measure exact event-free state matches and conservative event-history allocation; no model edits."""
import argparse,hashlib,json,math,time
from pathlib import Path
import torch
import torch.nn.functional as F
from eventspikeseg.data import DSECRawEventDataset,discover_dsec_records
from eventspikeseg.model import EventSpikeSeg140k
from eventspikeseg.asic.export import EVENTSPIKESEG140K_INFERENCE_STAGES
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/analog_asic';EXPECTED='c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tsha(t):return hashlib.sha256(t.detach().cpu().contiguous().numpy().tobytes()).hexdigest()
def compact(t):
 t=t.detach();base=t[:,:,:1,:1]
 return base.clone().expand_as(t) if torch.equal(t,base.expand_as(t)) else t.clone()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--dataset-root',type=Path,required=True);a=parser.parse_args();torch.set_num_threads(2)
 source=Path(__file__);stem='gf180_float_background_state_src'+sha(source)[:12];out=BASE/'results'/(stem+'.json');progress=BASE/'results'/(stem+'_progress.jsonl');assert not out.exists() and not progress.exists()
 checkpoint=ROOT/'artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt';assert sha(checkpoint)==EXPECTED;saved=torch.load(checkpoint,map_location='cpu',weights_only=True);assert saved['epoch']==58
 model=EventSpikeSeg140k(class_count=6,input_channels=2,internal_updates=10);model.load_state_dict(saved['model_state_dict'],strict=True);model.set_mechanism_scale(float(saved.get('mechanism_scale',1)));model.eval()
 for m in model.modules():
  toggle=getattr(m,'set_asic_qat_enabled',None)
  if callable(toggle):toggle(False)
 named=dict(model.named_modules());mode={'reference':True};references={};reference_inputs={};reference_stats={};counts={};touches={};dirty={};bins={};sizes={};adapt_sizes={}
 for name in EVENTSPIKESEG140K_INFERENCE_STAGES:
  stage=named[name];neuron=stage.neuron
  def before(module,inputs,name=name):
   seq=inputs[0];assert seq.shape[0]==10 and seq.shape[1]==1
   if mode['reference']:
    assert bool(torch.isfinite(seq).all()) and bool((seq==seq.round()).all()) and seq.abs().max()<128
    scalar=seq.flatten()[0]
    reference_inputs[name]=scalar.to(torch.int8).clone().expand_as(seq) if bool((seq==scalar).all()) else seq.to(torch.int8).clone()
   else:
    different=(seq!=reference_inputs[name]).float();conv=module.conv
    # Every input channel and every kernel position: conservative for grouped/depthwise connectivity.
    kernel=torch.ones((1,conv.in_channels,*conv.kernel_size))
    touches[name]=F.conv2d(different.reshape(10,*seq.shape[2:]),kernel,stride=conv.stride,padding=conv.padding,dilation=conv.dilation)>0
  stage.register_forward_pre_hook(before)
  original=neuron.forward
  def forward(current,elapsed_steps=1.0,update_mask=None,name=name,neuron=neuron,original=original):
   result=original(current,elapsed_steps,update_mask);k=counts.get(name,0);counts[name]=k+1;assert k<10
   fields={'membrane':neuron.membrane}
   if neuron.config.threshold_adaptation_enabled:
    fields.update(age=neuron.threshold_adaptation_age,amplitude=neuron.threshold_adaptation_amplitude)
   assert all(bool(torch.isfinite(v).all()) and v.dtype==torch.float32 for v in fields.values())
   if mode['reference']:
    references.setdefault(name,[]).append({key:compact(v) for key,v in fields.items()})
    spatial_uniform={key:bool((v==v[:,:,:1,:1]).all()) for key,v in fields.items()}
    reference_stats.setdefault(name,[]).append({'bin':k,'spatially_uniform_by_channel':spatial_uniform,'output_spike_count':int(result.sum()),'membrane_nonzero':int(torch.count_nonzero(neuron.membrane))})
   else:
    ref=references[name][k];memdiff=fields['membrane'].view(torch.int32)!=ref['membrane'].contiguous().view(torch.int32)
    adaptdiff=torch.zeros_like(memdiff)
    for key in ['age','amplitude']:
     if key in fields:adaptdiff |= fields[key].view(torch.int32)!=ref[key].contiguous().view(torch.int32)
    joint=memdiff|adaptdiff;dirt=dirty.get(name,torch.zeros_like(touches[name][k:k+1]));dirt=dirt|touches[name][k:k+1];dirty[name]=dirt
    expanded=dirt.expand_as(joint);outside=int((joint & ~expanded).sum());assert outside==0,(name,k,outside)
    sizes[name]=neuron.membrane.numel();adapt_sizes[name]=sizes[name] if 'age' in fields else 0
    bins.setdefault(name,[]).append({'bin':k,'membrane_bitwise_exceptions':int(memdiff.sum()),'adaptation_bitwise_exceptions':int(adaptdiff.sum()),'joint_bitwise_exceptions':int(joint.sum()),'conservative_event_history_allocations':int(expanded.sum()),'exceptions_outside_history_mask':outside})
   return result
  neuron.forward=forward
 all_records=discover_dsec_records(a.dataset_root,'train');records=[];prior_files=[]
 with torch.inference_mode():
  model.reset();model(torch.zeros((10,1,2,440,640)));assert all(v==10 for v in counts.values());assert len(references)==25
 for index in [8,64]:
  seq,frame=saved['temporal_protocol']['validation_record_ids'][index];matching=[r for r in all_records if r.sequence_id==seq and r.frame_index==frame];assert len(matching)==1
  dataset=DSECRawEventDataset(a.dataset_root,split='train',output_size=(440,640),internal_updates=10,class_count=6,records=matching);events,target,_=dataset[0];inputs=events.unsqueeze(1)
  prior_path=BASE/'results'/f'gf180_float_spatial_stem_error_record{index}_srce512e5e711fa.json';prior=json.loads(prior_path.read_text());prior_files.append(prior_path)
  assert tsha(inputs)==prior['input_sequence_sha256'] and tsha(target)==prior['target_sha256']
  mode['reference']=False;counts.clear();touches.clear();dirty.clear();bins.clear();start=time.monotonic()
  with torch.inference_mode():model.reset();output=model(inputs);prediction=output['segmentation_logits'].argmax(1)[0].cpu()
  assert tsha(prediction)==prior['results'][0]['prediction_sha256'];assert len(sizes)==25 and sum(sizes.values())==30976000 and sum(adapt_sizes.values())==10982400 and all(v==10 for v in counts.values())
  totals=[{key:sum(bins[name][k][key] for name in bins) for key in ['membrane_bitwise_exceptions','adaptation_bitwise_exceptions','joint_bitwise_exceptions','conservative_event_history_allocations']} for k in range(10)]
  summary={'record_index':index,'sequence':seq,'frame':frame,'input_sequence_sha256':tsha(inputs),'target_sha256':tsha(target),'prediction_sha256':tsha(prediction),'baseline_reproduced':True,'runtime_seconds':time.monotonic()-start,'by_actor':{name:{'resident_membranes':sizes[name],'adaptation_states':adapt_sizes[name],'bins':rows} for name,rows in bins.items()},'totals_by_bin':totals,'peak_joint_exceptions':max(v['joint_bitwise_exceptions'] for v in totals),'peak_history_allocations':max(v['conservative_event_history_allocations'] for v in totals),'sum_actor_peak_joint_exceptions':sum(max(v['joint_bitwise_exceptions'] for v in rows) for rows in bins.values()),'sum_actor_peak_history_allocations':sum(max(v['conservative_event_history_allocations'] for v in rows) for rows in bins.values())}
  records.append(summary)
  with progress.open('a',encoding='utf-8') as stream:stream.write(json.dumps({k:summary[k] for k in ['record_index','baseline_reproduced','runtime_seconds','peak_joint_exceptions','peak_history_allocations','sum_actor_peak_joint_exceptions','sum_actor_peak_history_allocations']})+'\n')
  print(progress.read_text().splitlines()[-1],flush=True);del output,inputs,events,target
 snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(source.read_bytes());files=[source,snap,checkpoint,progress,*prior_files,*sorted((ROOT/'src/eventspikeseg').rglob('*.py'))]
 report={'measurement_completed':True,'checkpoint_sha256':EXPECTED,'qat_or_quantized_reference_used':False,'resident_membranes':30976000,'adaptation_states':10982400,'zero_input_reference':reference_stats,'records':records,'one_all_membrane_exception_bitmap_bytes':math.ceil(30976000/8),'scope':'Unchanged original-float checkpoint and inference, reset separately for zero-input reference and each actual10bin record. Bitwise float32 equality, no near-zero truncation, quantization or arithmetic state correction. Joint exceptions include membrane and enabled triangular age/amplitude. Reference spatial-uniformity and default output spikes measured, not assumed. Conservative allocation mask accumulates any presynaptic-reference difference through full kernel spatial footprint, expands over all output channels to cover peer inhibition/adaptation, never clears within record; verifies all observed joint exceptions lie inside. Reference values/spikes and input differences are analysis only, not qualified hardware detection/reference generators. Every logical identity remains distinct; sharing requires real mapping, allocation, analog values and5ms service. Two same-sequence reset records only, no continuous-stream/worst-case dataset qualification. No compact layout/noise/leakage/physical sharing/model approximation acceptance.','acceptance':{'storage_organization':False,'original_float_accuracy':False,'complete_PLIF':False,'full_5ms_population_service':False,'full_chip':False},'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in files}}
 out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('REPORT '+str(out),flush=True)
if __name__=='__main__':main()
