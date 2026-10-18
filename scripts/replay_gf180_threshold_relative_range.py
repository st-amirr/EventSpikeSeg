"""Original-float sensitivity replay of measured native charge read/restore transfer."""
import argparse
import hashlib
import json
import math
import time
from pathlib import Path
import torch
from eventspikeseg.data import DSECRawEventDataset, discover_dsec_records
from eventspikeseg.model import EventSpikeSeg140k
from eventspikeseg.asic.export import EVENTSPIKESEG140K_INFERENCE_STAGES

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'artifacts/analog_asic'
EXPECTED = 'c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def tsha(tensor):
    return hashlib.sha256(tensor.detach().cpu().contiguous().numpy().tobytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-root', type=Path, required=True)
    parser.add_argument('--record-index', type=int, default=8)
    args = parser.parse_args()
    torch.set_num_threads(2)
    source = Path(__file__)
    stem = f'gf180_threshold_relative_range_record{args.record_index}_src{sha(source)[:12]}'
    progress = BASE/'results'/(stem+'_progress.jsonl')
    assert not progress.exists(), 'Preserve existing evidence'
    checkpoint = ROOT/'artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt'
    assert sha(checkpoint) == EXPECTED
    saved = torch.load(checkpoint, map_location='cpu', weights_only=True)
    assert saved['epoch'] == 58
    prior_path = BASE/'results'/f'gf180_float_spatial_stem_error_record{args.record_index}_srce512e5e711fa.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    candidates = list((BASE/'results').glob('gf180_float_state_tile_calibration_*.json'))
    assert len(candidates)==1
    calibration_path = candidates[0]
    calibration = json.loads(calibration_path.read_text(encoding='utf-8'))
    assert calibration['checkpoint_sha256'] == EXPECTED
    assert args.record_index not in [r['validation_record_index'] for r in calibration['records']]
    sequence, frame = saved['temporal_protocol']['validation_record_ids'][args.record_index]
    records = [r for r in discover_dsec_records(args.dataset_root, 'train') if r.sequence_id == sequence and r.frame_index == frame]
    assert len(records) == 1
    dataset = DSECRawEventDataset(args.dataset_root, split='train', output_size=(440,640), internal_updates=10, class_count=6, records=records)
    events, target, _ = dataset[0]
    inputs = events.unsqueeze(1)
    assert tsha(inputs) == prior['input_sequence_sha256'] and tsha(target) == prior['target_sha256']
    model = EventSpikeSeg140k(class_count=6, input_channels=2, internal_updates=10)
    model.load_state_dict(saved['model_state_dict'], strict=True)
    model.set_mechanism_scale(float(saved.get('mechanism_scale',1)))
    model.eval()
    for module in model.modules():
        toggle = getattr(module, 'set_asic_qat_enabled', None)
        if callable(toggle):
            toggle(False)
    named = dict(model.named_modules())
    fixed = {name: torch.tensor(values).view(1,-1,1,1) for name, values in calibration['channel_fixed_calibration_absmax'].items()}
    local = {name:torch.tensor(value).repeat_interleave(8,2).repeat_interleave(8,3) for name,value in calibration['state_tile8_ranges'].items()}
    assert set(local)==set(EVENTSPIKESEG140K_INFERENCE_STAGES)
    inventory_path=BASE/'results/gf180_float_threshold_voltage_inventory.json';inventory=json.loads(inventory_path.read_text());assert inventory['measurement_completed']
    for name,h in inventory['sha256'].items():assert sha(ROOT/name)==h,name
    thresholds={row['actor']:torch.tensor(row['base_threshold_model_units']).view(1,-1,1,1) for row in inventory['actors']}
    active={'multiple':None};diagnostics={};counts={}
    for name in EVENTSPIKESEG140K_INFERENCE_STAGES:
        neuron=named[name].neuron;original=neuron.forward
        def forward(current,elapsed_steps=1.0,update_mask=None,name=name,neuron=neuron,original=original):
            spikes=original(current,elapsed_steps,update_mask);value=neuron.membrane;counts[name]=value.numel()
            if active['multiple'] is not None:
                limit=thresholds[name]*active['multiple']
                diagnostics[name]=diagnostics.get(name,0)+int((value.abs()>limit).sum())
                neuron.membrane=torch.maximum(torch.minimum(value,limit),-limit)
            return spikes
        neuron.forward=forward
    rows=[];baseline=None;valid=target!=255
    for multiple in [None,64,16,4]:
        active['multiple']=multiple;diagnostics.clear();torch.manual_seed(1729);start=time.monotonic()
        with torch.inference_mode():
            model.reset();output=model(inputs);prediction=output['segmentation_logits'].argmax(1)[0].cpu()
        if baseline is None:
            assert tsha(prediction)==prior['results'][0]['prediction_sha256'];baseline=prediction.clone()
        confusion=torch.bincount(target[valid].long()*6+prediction[valid].long(),minlength=36).reshape(6,6);inter=confusion.diagonal();union=confusion.sum(0)+confusion.sum(1)-inter
        row={'policy':'baseline' if multiple is None else f'bounded_state_{multiple}x_base_threshold','range_multiple':multiple,'physical_base_threshold_offset_v':None if multiple is None else .44/multiple,'mean_iou':float((inter[union>0]/union[union>0]).float().mean()),'pixel_change_fraction':float((prediction!=baseline).float().mean()),'prediction_sha256':tsha(prediction),'state_clips_by_actor':dict(diagnostics),'runtime_seconds':time.monotonic()-start};rows.append(row)
        with progress.open('a',encoding='utf-8') as stream:stream.write(json.dumps(row)+'\n')
        print(json.dumps({k:v for k,v in row.items() if k!='state_clips_by_actor'}),flush=True);del output
    assert len(counts)==25 and sum(counts.values())==30976000
    snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(source.read_bytes());files=[source,snap,checkpoint,prior_path,calibration_path,progress,inventory_path,*sorted((ROOT/'src/eventspikeseg').rglob('*.py'))]
    report={'simulation_completed':True,'checkpoint_sha256':EXPECTED,'record_index':args.record_index,'input_sequence_sha256':tsha(inputs),'target_sha256':tsha(target),'baseline_reproduced':True,'results':rows,'state_counts':counts,'scope':'Sensitivity experiment only: unchanged original float checkpoint,QAT off, no retraining/weight rounding. Approximate hardware state saturation at +/-K times each original base threshold, after original reset/inhibition/adaptation bookkeeping, all25actors. Original equations inside bin preserved until post-reset clipping; state history changes on later bins. No precision/noise/transfer errors included. .44/K gives illustrative voltage threshold if same .44V half-range is used. This is a proposed representation approximation, not accepted replacement of trained behavior; evaluate errors before any architecture change. Two same-sequence reset heldouts do not establish continuous-stream or dataset-wide accuracy. No physical clipping/conversion circuit/layout/service acceptance.','qat_or_quantized_reference_used':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_5ms_population_service_accepted':False,'full_chip_accepted':False,'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in files}}
    rp=BASE/'results'/(stem+'.json');assert not rp.exists();rp.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('REPORT '+str(rp),flush=True)
if __name__=='__main__':main()
