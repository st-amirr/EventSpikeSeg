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
    parser.add_argument('--seed', type=int, choices=[0], default=0)
    args = parser.parse_args()
    torch.set_num_threads(2)
    source = Path(__file__)
    stem = f'gf180_sc_packet_beta_channel_record{args.record_index}_seed{args.seed}_src{sha(source)[:12]}'
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
    audit_path=BASE/'results/gf180_sc_packet_detailstem_ch3_v4_trained_beta_packet21_v1.json'
    audit=json.loads(audit_path.read_text());assert audit['simulation_completed']
    netlist=BASE/'layout/gf180_sc_packet_detailstem_ch3_v4/gf180_sc_packet_detailstem_ch3_v4_cap.spice'
    assert sha(netlist)==audit['sha256']['netlist']
    actor='detail_stem';channel=3;neuron=named[actor].neuron
    beta=float(neuron.beta[channel]);assert beta==0.8818925023078918
    audit_target={'actor':actor,'channel':channel,'trained_beta':beta}
    samples=[c for c in audit['cases'] if c['target_packet_mv']==0]
    assert len(samples)==7
    curve_x=torch.tensor([c['pre_beta_v'] for c in samples]);curve_y=torch.tensor([c['post_release_v'] for c in samples]);half=.9
    assert float(curve_x[0])<1.65-half and float(curve_x[-1])>1.65+half
    active={'policy':'baseline'};diagnostics={};original=neuron._candidate_membrane
    def candidate(current,elapsed):
        output=original(current,elapsed)
        assert bool(torch.isclose(elapsed,torch.ones_like(elapsed)).all()), 'Replay requires actual unit5ms update'
        if active['policy']=='baseline':return output
        previous=neuron.membrane[:,channel:channel+1]
        f=fixed[actor][:,channel:channel+1];tile=local[actor][:,channel:channel+1,:previous.shape[2],:previous.shape[3]]
        limit=tile
        diagnostics['calls']=diagnostics.get('calls',0)+1
        diagnostics['previous_state_excursions']=diagnostics.get('previous_state_excursions',0)+int((previous.abs()>limit).sum())
        clamped=torch.maximum(torch.minimum(previous,limit),-limit)
        if active['policy']=='selected_channel_range_control':leaked=beta*clamped
        else:
            voltage=1.65+half*clamped/limit
            index=torch.bucketize(voltage,curve_x).clamp(1,len(curve_x)-1)
            decoded=curve_y[index-1]+(voltage-curve_x[index-1])*(curve_y[index]-curve_y[index-1])/(curve_x[index]-curve_x[index-1])
            leaked=(decoded-1.65)*limit/half
        output=output.clone();output[:,channel:channel+1]+=leaked-beta*previous
        return output
    neuron._candidate_membrane=candidate
    rows=[];baseline=None;valid=target!=255
    for policy in ['baseline','selected_channel_range_control','selected_channel_measured_complete_cycle']:
        active['policy']=policy;diagnostics.clear();torch.manual_seed(1729);start=time.monotonic()
        with torch.inference_mode():
            model.reset();output=model(inputs);prediction=output['segmentation_logits'].argmax(1)[0].cpu()
        if baseline is None:
            assert tsha(prediction)==prior['results'][0]['prediction_sha256'];baseline=prediction.clone()
        confusion=torch.bincount(target[valid].long()*6+prediction[valid].long(),minlength=36).reshape(6,6);inter=confusion.diagonal();union=confusion.sum(0)+confusion.sum(1)-inter
        row={'policy':policy,'mean_iou':float((inter[union>0]/union[union>0]).float().mean()),'pixel_change_fraction':float((prediction!=baseline).float().mean()),'prediction_sha256':tsha(prediction),'diagnostics':dict(diagnostics),'runtime_seconds':time.monotonic()-start};rows.append(row)
        with progress.open('a',encoding='utf-8') as stream:stream.write(json.dumps(row)+'\n')
        print(json.dumps(row),flush=True);del output
    snap=BASE/'tools/source_snapshots'/(stem+'.py');snap.write_bytes(source.read_bytes())
    files=[source,snap,checkpoint,prior_path,calibration_path,progress,audit_path,netlist,*sorted((ROOT/'src/eventspikeseg').rglob('*.py'))]
    report={'simulation_completed':True,'checkpoint_sha256':EXPECTED,'record_index':args.record_index,'corner':'GF180 typical,27C','target_channel':audit_target,'input_sequence_sha256':tsha(inputs),'target_sha256':tsha(target),'baseline_reproduced':True,'physical_storage_half_range_v':half,'measured_curve_x_v':curve_x.tolist(),'measured_curve_y_v':curve_y.tolist(),'results':rows,'scope':'Unchanged epoch58 original float checkpoint, QAT off. Only detail_stem channel3 uses the measured seven-point zero-packet beta-plus-handoff curve from the fully extracted v4 parent. Each original-float 8x8 tile range maps to +/-0.9V about1.65V. Same range clipping is measured separately; original baseline hashes must reproduce. Current contributions, other channels, threshold/reset and adaptation remain original equations. The replay does not include per-event packet amplitude error, physical reference delivery, sampled noise/PVT/history, all-channel scaling, service or chip acceptance.','qat_or_quantized_reference_used':False,'original_float_accuracy_accepted':False,'complete_PLIF_accepted':False,'full_5ms_population_service_accepted':False,'full_chip_accepted':False,'sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in files}}
    rp=BASE/'results'/(stem+'.json');assert not rp.exists();rp.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('REPORT '+str(rp),flush=True)
if __name__=='__main__':main()
