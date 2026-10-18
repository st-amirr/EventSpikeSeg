"""Original-float replay of measured nominal parked-readout write/hold/read transfer."""
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
    stem = f'gf180_extracted_memory_transfer_record{args.record_index}_src{sha(source)[:12]}'
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
    curve_reports=sorted((BASE/'results').glob('gf180_writer_memory_extracted_readout_*.json'))
    assert len(curve_reports)==2
    sampled={}
    for path in curve_reports:
        report=json.loads(path.read_text(encoding='utf-8'))
        assert report['simulation_completed'] and report['combined_writer_memory_layout_qualified'] and report['readout_layout_qualified']
        for name,h in report['sha256'].items():assert sha(ROOT/name)==h,name
        for name,v in report['target_levels_v'].items():
            sampled.setdefault(v,[]).append(report['measurements'][name+'_decoded_late'])
    assert sorted(sampled)==[.75,1.2,1.65,2.1,2.55]
    # Average only the repeated common-point control; no transfer inversion or correction.
    curve_x=torch.tensor(sorted(sampled))
    curve_y=torch.tensor([sum(sampled[v])/len(sampled[v]) for v in sorted(sampled)])
    active = {'policy': 'baseline'}
    excursions = {}
    state_counts = {}
    for name in EVENTSPIKESEG140K_INFERENCE_STAGES:
        neuron = named[name].neuron
        original = neuron.forward
        def forward(current, elapsed_steps=1.0, update_mask=None, name=name, neuron=neuron, original=original):
            spikes = original(current, elapsed_steps, update_mask)
            value = neuron.membrane
            state_counts[name] = value.numel()
            limit = fixed[name]
            tile = local[name][:,:,:value.shape[2],:value.shape[3]]
            gain = torch.pow(2.0, torch.floor(torch.log2(fixed[name]/tile))).clamp(1,16)
            limit = fixed[name]/gain
            excursions[name] = excursions.get(name,0) + int((value.abs() > limit).sum())
            if active['policy'] != 'baseline':
                value=torch.maximum(torch.minimum(value,limit),-limit)
                if active['policy']=='measured_nominal_write_hold_read':
                    voltage=1.65+0.9*value/limit
                    index=torch.bucketize(voltage,curve_x).clamp(1,len(curve_x)-1)
                    decoded=curve_y[index-1]+(voltage-curve_x[index-1])*(curve_y[index]-curve_y[index-1])/(curve_x[index]-curve_x[index-1])
                    value=(decoded-1.65)*limit/0.9
                neuron.membrane=value
            return spikes
        neuron.forward = forward
    rows = []
    baseline = None
    valid = target != 255
    for policy in ['baseline','fixed_storage_range_zero_noise','measured_nominal_write_hold_read']:
        active.update(policy=policy)
        excursions.clear()
        torch.manual_seed(1729)
        start = time.monotonic()
        with torch.inference_mode():
            model.reset()
            output = model(inputs)
            prediction = output['segmentation_logits'].argmax(1)[0].cpu()
        if baseline is None:
            assert tsha(prediction) == prior['results'][0]['prediction_sha256']
            baseline = prediction.clone()
        confusion = torch.bincount(target[valid].long()*6+prediction[valid].long(), minlength=36).reshape(6,6)
        inter = confusion.diagonal()
        union = confusion.sum(0)+confusion.sum(1)-inter
        row = {'policy':policy, 'mean_iou':float((inter[union>0]/union[union>0]).float().mean()),
               'pixel_change_fraction':float((prediction!=baseline).float().mean()), 'prediction_sha256':tsha(prediction),
               'post_reset_range_excursions_before_noise_by_actor':dict(excursions), 'runtime_seconds':time.monotonic()-start}
        rows.append(row)
        with progress.open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(row)+'\n')
        print(json.dumps({k:row[k] for k in ['policy','mean_iou','pixel_change_fraction','runtime_seconds']}),flush=True)
        del output
    assert len(state_counts) == 25 and sum(state_counts.values()) == 30976000
    snap = BASE/'tools/source_snapshots'/(stem+'.py')
    snap.write_bytes(source.read_bytes())
    files = [source,snap,checkpoint,prior_path,calibration_path,progress,*curve_reports,*sorted((ROOT/'src/eventspikeseg').rglob('*.py'))]
    report = {'simulation_completed':True, 'checkpoint_sha256':EXPECTED, 'record_index':args.record_index,
              'input_sequence_sha256':tsha(inputs), 'target_sha256':tsha(target), 'baseline_reproduced':True,
              'physical_storage_half_range_v':0.9,'transfer_input_levels_v':curve_x.tolist(),'transfer_decoded_levels_v':curve_y.tolist(),
              'results':rows,'state_counts':state_counts,
              'scope':'Unchanged epoch58 original-float weights/equations, QAT off. All25 actors receive measured nominal end-to-end write/5ms-hold/read transfer after each post-reset/inhibition update; effects appear on later bins. Piecewise-linear interpolation of five physical target levels, no mathematical inverse or arithmetic correction. Measured circuit is extracted writer-memory plus separately qualified cap-extracted native regulated-current readout with external references and idle parking. The repeated midpoint is averaged only as a control. Fixed tiled ranges from calibration0-7, ideal +/-0.9V conversion to model units, no target-range oracle. Baseline and clipped control distinguish range from deterministic transfer. Extrapolates one nominal circuit to every membrane and operation; does not reproduce event schedule, mismatch, sampled noise, history, load, beta/inhibition/adaptation conversion or complete circuits. Decoder layout exists; combined parent routing, real references and5ms population throughput remain unqualified. This is approximate task sensitivity to the measured mean transfer, not hardware accuracy acceptance.',
              'qat_or_quantized_reference_used':False, 'physical_storage_accepted':False, 'original_float_accuracy_accepted':False,
              'complete_PLIF_accepted':False, 'full_5ms_population_service_accepted':False, 'full_chip_accepted':False,
              'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in files}}
    path = BASE/'results'/(stem+'.json')
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('REPORT '+str(path),flush=True)

if __name__ == '__main__':
    main()
