"""Replay analog state-range clipping through the original full-float SNN."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import torch

from eventspikeseg.data import DSECRawEventDataset, discover_dsec_records
from eventspikeseg.model import EventSpikeSeg140k

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT = ROOT / "artifacts/model_checkpoints/dsec_6class/EventSpikeSeg140k_seed17_best.pt"
OUT = ROOT / "artifacts/analog_asic/results"
EXPECTED_CHECKPOINT_SHA256 = "c934da40b0f65d2a63155cb89b663e06aebf527cea1db4b9902a5b53840457d7"


def interpolate_hold(physical_v: torch.Tensor, hold_v: torch.Tensor,
                     hold_delta: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    inside = (physical_v >= hold_v[0]) & (physical_v <= hold_v[-1])
    index = torch.bucketize(physical_v.contiguous(), hold_v[1:-1])
    x0, x1 = hold_v[index], hold_v[index + 1]
    y0, y1 = hold_delta[index], hold_delta[index + 1]
    return y0 + (physical_v - x0) * (y1 - y0) / (x1 - x0), inside


def main() -> int:
    replay_source_bytes=Path(__file__).read_bytes()
    replay_sha=hashlib.sha256(replay_source_bytes).hexdigest()
    replay_snapshot=ROOT/'artifacts/analog_asic/tools/source_snapshots'/f'float_state_replay_{replay_sha}.py'
    replay_snapshot.parent.mkdir(parents=True,exist_ok=True)
    if not replay_snapshot.exists():replay_snapshot.write_bytes(replay_source_bytes)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--record-index", type=int, default=0)
    parser.add_argument("--scope", choices=("final-fuse", "all-neurons"), default="final-fuse")
    parser.add_argument("--full-frame", action="store_true")
    parser.add_argument("--noise-mode", choices=("none", "init-only", "reset-only", "threshold-only", "writeback-every-bin"), default="none",
                        help="Inject illustrative state noise or independent analog threshold-comparator noise")
    parser.add_argument("--noise-sigma-uv", type=float, default=None,
                        help="Illustrative independent differential state-noise RMS; overrides the 10um MIM proxy")
    parser.add_argument("--gains", default="1,2,4,10,32")
    parser.add_argument("--encoding", choices=("linear-clipped", "asinh-ideal", "piecewise-ideal", "measured-mos-ideal-inverse"), default="linear-clipped")
    parser.add_argument('--encoder-dc-profile',type=Path)
    parser.add_argument('--encoder-noise-profile',type=Path)
    parser.add_argument('--measured-noise-scale',type=float,choices=[0,.01,.1,1],default=1,
                        help='Explicit hypothetical noise-reduction bound; only1 uses full measured stationary RMS')
    parser.add_argument("--segments", type=int, default=8)
    parser.add_argument("--range-scope", choices=("actor", "channel"), default="actor")
    parser.add_argument('--restore-gain-positive',type=float,default=1)
    parser.add_argument('--restore-gain-negative',type=float,default=1)
    parser.add_argument('--restore-offset-uv',type=float,default=0,help='Affine encoded-state proxy in the existing +/-0.9V normalization')
    parser.add_argument('--restore-source',type=Path,action='append',default=[],help='Physical evidence provenance; affine extrapolation is not qualified transfer')
    parser.add_argument("--linear-compute-noise-sigma-uv", type=float, default=0,
                        help="Independent noise on linear candidate before threshold/encoding, normalized to the same +/-0.9V full scale")
    parser.add_argument("--retention-law", choices=("none", "mos-tt-measured-window", "mos-tt-rail-window",
                                                     "mos-tt-vcm-differential", "measured-vcm-differential"), default="none")
    parser.add_argument("--retention-profile", type=Path, default=None,
                        help="use a measured hold-profile JSON instead of the built-in TT profile")
    args = parser.parse_args()
    measured_encoder=None
    if args.encoding=='measured-mos-ideal-inverse':
        if not args.encoder_dc_profile or not args.encoder_noise_profile:
            raise ValueError('Measured encoding requires DC and matched stationary-noise reports')
        if args.noise_sigma_uv is not None or args.gains!='1' or args.range_scope!='actor' or args.retention_law!='none' or args.noise_mode not in ('none','writeback-every-bin'):
            raise ValueError('Measured curve probe uses gain1, actor range, matched noise, and none/writeback-every-bin only')
        dc=json.loads(args.encoder_dc_profile.read_text());noise=json.loads(args.encoder_noise_profile.read_text())
        if not dc['simulation_completed'] or not noise['simulation_completed'] or dc.get('operating_point_solver_warning') or noise.get('operating_point_solver_warning') or not dc['analysis']['strictly_monotonic'] or dc['analysis']['maximum_sum_minus_reference_uv']>500:
            raise ValueError('Measured DC transfer incomplete, nonmonotonic or loses virtual-sum regulation')
        ds,ns=dc['command_arguments'],noise['command_arguments']
        if ds.get('noise') or ds.get('transient') or not ns.get('noise') or ns.get('noise_input_na')!=0:
            raise ValueError('DC profile and zero-input stationary-noise profile required')
        for key in ['corner','temp_c','span_v','reference_ua','input_feedback_mim_count','mirrored_feedback','self_biased_span','calibration_na','source_lifted','lift_reference_na','lift_reference_node','switched_compensation','minimum_feedback_size_um','feedback_scale','buffer_reference_ua','physical_compensation_controller','physical_controller_threshold_scale','physical_controller_hysteresis','compensation_bank_clamp']:
            if ds.get(key)!=ns.get(key):raise ValueError(f'Encoder operating settings differ: {key}')
        for name,sha in dc['sha256'].items():
            if name.startswith('artifacts/analog_asic/layout/') and name.endswith('_cap.spice') and noise['sha256'].get(name)!=sha:
                raise ValueError('Noise/DC extracted layout mismatch')
        physical_current_knots=torch.tensor([row['input_current_na'] for row in dc['rows']],dtype=torch.float32)
        physical_voltage_knots=torch.tensor([row['v(enc)'] for row in dc['rows']],dtype=torch.float32)
        if not bool(torch.all(torch.diff(physical_current_knots)>0)) or not bool(torch.all(torch.diff(physical_voltage_knots)>0)) or physical_current_knots[0]!=-physical_current_knots[-1]:
            raise ValueError('Signed monotonic symmetric-current-domain transfer required')
        measured_encoder={'dc_source':str(args.encoder_dc_profile),'noise_source':str(args.encoder_noise_profile),
            'dc_sha256':hashlib.sha256(args.encoder_dc_profile.read_bytes()).hexdigest(),
            'noise_sha256':hashlib.sha256(args.encoder_noise_profile.read_bytes()).hexdigest(),
            'settings':ds,'current_knots_na':physical_current_knots.tolist(),
            'voltage_knots_v':physical_voltage_knots.tolist(),
            'stationary_output_noise_uv':noise['analysis']['encoded_output_rms_uv'],
            'hypothetical_noise_scale':args.measured_noise_scale,
            'scope':'Measured asymmetric MOS DC interpolation with mathematically exact inverse, optimistic ideal per-record actor current scaling, constant zero-bias stationary RMS reused as independent every-bin noise. No physical inverse, state-dependent noise, calibration current generator, update circuit or accuracy acceptance.'}
        args.noise_sigma_uv=measured_encoder['stationary_output_noise_uv']*args.measured_noise_scale
    elif args.encoder_dc_profile or args.encoder_noise_profile or args.measured_noise_scale!=1:
        raise ValueError('Encoder profiles require measured-mos-ideal-inverse encoding')
    restore_active=(args.restore_gain_positive!=1 or args.restore_gain_negative!=1 or args.restore_offset_uv!=0)
    if not all(math.isfinite(v) for v in [args.restore_gain_positive,args.restore_gain_negative,args.restore_offset_uv]) or not all(0.9<=v<=1.1 for v in [args.restore_gain_positive,args.restore_gain_negative]) or abs(args.restore_offset_uv)>1000:
        raise ValueError('bounded affine restore requires gains0.9..1.1 and offset+/-1000uV')
    if restore_active and args.encoding!='linear-clipped':
        raise ValueError('affine restore proxy currently supports linear encoding only')
    if args.noise_sigma_uv is not None and (args.noise_sigma_uv < 0 or not math.isfinite(args.noise_sigma_uv)):
        raise ValueError("noise sigma must be finite and nonnegative")
    if not 0 <= args.linear_compute_noise_sigma_uv <= 1000 or not math.isfinite(args.linear_compute_noise_sigma_uv):
        raise ValueError("linear computation noise must be finite0..1000uV")
    if args.retention_law != "none" and args.encoding == "asinh-ideal":
        raise ValueError("measured MOS retention currently supports linear or piecewise encoding")
    if args.range_scope == "channel" and (args.encoding != "linear-clipped" or args.retention_law != "none"):
        raise ValueError("per-channel range screen currently supports linear encoding without retention")
    gains = tuple(float(value) for value in args.gains.split(","))
    if not gains or any(gain < 1 or not math.isfinite(gain) for gain in gains):
        raise ValueError("gains must be finite and at least 1")
    if args.segments < 2 or args.segments > 32:
        raise ValueError("segments must be in 2..32")
    torch.set_num_threads(2)
    digest = hashlib.sha256(CHECKPOINT.read_bytes()).hexdigest()
    if digest != EXPECTED_CHECKPOINT_SHA256:
        raise RuntimeError("full-float checkpoint hash differs from the active analog reference")
    hold = None
    vcm_differential_profile = args.retention_law in ("mos-tt-vcm-differential", "measured-vcm-differential")
    if args.retention_law != "none":
        default_retention_file = ("sky130_mos_gate_bank_hold_vcm_loaded_5ms.json" if vcm_differential_profile else
                                  "sky130_mos_fullrail_hold_boundary.json" if args.retention_law == "mos-tt-rail-window"
                                  else "sky130_mos_decay_prediction_boundary.json")
        retention_path = args.retention_profile or (OUT / default_retention_file)
        retention_file = str(retention_path)
        hold = json.loads(retention_path.read_text(encoding="utf-8"))
        expected_biases = ([-900, -500, -100, 0, 100, 500, 900] if vcm_differential_profile else
                           [0.0, 0.15, 0.3, 0.45, 0.6, 0.75, 0.9, 1.05, 1.2, 1.35, 1.5, 1.65, 1.8]
                           if args.retention_law == "mos-tt-rail-window" else [0.6, 0.75, 0.9, 1.05, 1.2])
        complete = hold.get("simulation_completed", False) if vcm_differential_profile else hold.get("all_simulations_completed", False)
        observed_biases = ([row["initial_differential_mv"] for row in hold["rows"]] if vcm_differential_profile
                           else [row["program_v"] for row in hold["rows"]])
        if not complete or observed_biases != expected_biases:
            raise RuntimeError("measured MOS state hold profile is missing or incomplete")
        if vcm_differential_profile:
            hold_v = torch.tensor([
                row.get("measured_at_hold_start_v", row.get("measured_at_4us_v"))
                for row in hold["rows"]], dtype=torch.float32)
            hold_delta = torch.tensor([row["drift_uv"] * 1e-6 for row in hold["rows"]], dtype=torch.float32)
            if not bool(torch.all(torch.diff(hold_v) > 0)):
                raise RuntimeError("VCM differential hold profile is not monotone")
            valid_rows = []
        else:
            if args.retention_law == "mos-tt-rail-window" and not hold["measured_start_voltages_strictly_increasing"]:
                raise RuntimeError("full-rail MOS sampled voltages are not monotonic")
            # The rail=0 case starts slightly below 0V after sampling, outside the
            # documented 1.8V NMOS VGS range; exclude it from interpolation.
            valid_rows = hold["rows"][1:] if args.retention_law == "mos-tt-rail-window" else hold["rows"]
            hold_v = torch.tensor([row["measured_v"]["start"] for row in valid_rows], dtype=torch.float32)
            hold_delta = torch.tensor([
                row["measured_v"]["five_ms"] - row["measured_v"]["start"]
                for row in valid_rows], dtype=torch.float32)
    checkpoint = torch.load(CHECKPOINT, map_location="cpu", weights_only=True)
    if checkpoint["architecture"] != "EventSpikeSeg140k":
        raise RuntimeError("unexpected model")
    updates = int(checkpoint["temporal_protocol"]["internal_updates"])
    sequence_id, frame_index = checkpoint["temporal_protocol"]["validation_record_ids"][args.record_index]
    records = [row for row in discover_dsec_records(args.dataset_root, "train")
               if row.sequence_id == sequence_id and row.frame_index == frame_index]
    if len(records) != 1:
        raise RuntimeError("selected validation record is unavailable")
    dataset = DSECRawEventDataset(args.dataset_root, split="train", output_size=(440, 640),
                                 internal_updates=updates, class_count=6, records=records)
    events, target, _ = dataset[0]
    if args.full_frame:
        selected = [(0, 0)]
        input_sequence = events.unsqueeze(1)
        selected_target = target.unsqueeze(0)
    else:
        size = 64
        tiles = [(float(events[:, :, y:y+size, x:x+size].sum()), y, x)
                 for y in range(0, events.shape[-2]-size+1, size)
                 for x in range(0, events.shape[-1]-size+1, size)]
        tiles.sort()
        selected = [(int(y), int(x)) for _, y, x in
                    (tiles[0], tiles[len(tiles)//2], tiles[-1])]
        input_sequence = torch.stack(
            [events[:, :, y:y+size, x:x+size] for y, x in selected], dim=1)
        selected_target = torch.stack([target[y:y+size, x:x+size] for y, x in selected])
    valid = selected_target != 255
    def mean_iou(prediction: torch.Tensor) -> float:
        truth = selected_target[valid].to(torch.int64)
        predicted = prediction[valid].to(torch.int64)
        confusion = torch.bincount(truth * 6 + predicted, minlength=36).reshape(6, 6)
        intersection = confusion.diagonal()
        union = confusion.sum(dim=0) + confusion.sum(dim=1) - intersection
        present = union > 0
        return float((intersection[present] / union[present]).float().mean())
    model = EventSpikeSeg140k(class_count=6, input_channels=2, internal_updates=updates)
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.set_mechanism_scale(float(checkpoint.get("mechanism_scale", 1.0)))
    for module in model.modules():
        disable = getattr(module, "set_asic_qat_enabled", None)
        if callable(disable):
            disable(False)
    model.eval()
    all_neurons = [(name, module.neuron) for name, module in model.named_modules()
                   if hasattr(module, "neuron") and hasattr(module.neuron, "_candidate_membrane")]
    selected_neurons = [(name, neuron) for name, neuron in all_neurons
                        if args.scope == "all-neurons" or name == "final_fuse.standard"]
    maxima = {}
    channel_maxima = {}
    original_candidates = {}
    for name, neuron in selected_neurons:
        original = neuron._candidate_membrane
        original_candidates[name] = original
        def capture(current, elapsed, *, _name=name, _original=original):
            candidate = _original(current, elapsed)
            maxima[_name] = max(maxima.get(_name, 0.0), float(candidate.detach().abs().max()))
            if args.range_scope == "channel":
                if candidate.ndim != 4:
                    raise RuntimeError("per-channel range capture requires NCHW membrane")
                per_channel = candidate.detach().abs().amax(dim=(0, 2, 3), keepdim=True)
                channel_maxima[_name] = torch.maximum(channel_maxima.get(_name, per_channel), per_channel)
            return candidate
        neuron._candidate_membrane = capture
    stage = dict(model.named_modules())["final_fuse.standard"].neuron
    reference_spikes = []
    handle = stage.register_forward_hook(
        lambda _m, _i, out: reference_spikes.append(out.detach().cpu().bool().clone()))
    with torch.inference_mode():
        model.reset()
        baseline = model(input_sequence)
    handle.remove()
    for name, neuron in selected_neurons:
        neuron._candidate_membrane = original_candidates[name]
    baseline_spikes = torch.stack(reference_spikes)
    baseline_mask = baseline["segmentation_logits"].argmax(dim=1).detach().cpu()
    original_forwards = {name: neuron.forward for name, neuron in selected_neurons}
    original_thresholds = {name: neuron._threshold_tensor for name, neuron in selected_neurons}
    trials = []
    thermal_sigma_uv = math.sqrt(2 * 1.380649e-23 * 273.15 / 203.8e-15) * 1e6
    injected_sigma_uv = args.noise_sigma_uv if args.noise_sigma_uv is not None else thermal_sigma_uv
    seeds = (0,) if args.noise_mode == "none" and args.linear_compute_noise_sigma_uv == 0 else (1729, 1730, 1731)
    if measured_encoder and args.measured_noise_scale==0 and args.linear_compute_noise_sigma_uv==0:seeds=(0,)
    for gain in gains:
        for seed in seeds:
            torch.manual_seed(seed)
            retention_counts = {"inside": 0, "outside": 0}
            for name, neuron in selected_neurons:
                if maxima.get(name, 0) <= 0:
                    continue
                maximum = maxima[name]
                if args.range_scope == "channel":
                    maximum = torch.where(channel_maxima[name] > 0, channel_maxima[name], maximum)
                bound = maximum / gain
                sigma_units = injected_sigma_uv * 1e-6 / (0.9 * gain / maximum)
                original_candidate = original_candidates[name]
                if args.linear_compute_noise_sigma_uv:
                    compute_sigma = args.linear_compute_noise_sigma_uv * 1e-6 * maximum / 0.9
                    def noisy_candidate(current, elapsed, *, _base=original_candidate, _sigma=compute_sigma):
                        candidate = _base(current, elapsed)
                        return candidate + torch.randn_like(candidate) * _sigma
                    original_candidate = noisy_candidate
                original_forward = original_forwards[name]
                first = [True]
                def apply_retention(state):
                    return state
                if args.encoding == "linear-clipped":
                    def clipped_candidate(current, elapsed, *, _original=original_candidate, _bound=bound):
                        return _original(current, elapsed).clamp(-_bound, _bound)
                    def add_noise(state, current, *, _sigma=sigma_units):
                        return state + torch.randn_like(current) * _sigma
                    if hold is not None:
                        def apply_retention(state, *, _scale=0.9 * gain / maximum,
                                            _hold_v=hold_v, _hold_delta=hold_delta,
                                            _counts=retention_counts):
                            physical_v = state * _scale if vcm_differential_profile else 0.9 + state * _scale
                            delta, inside = interpolate_hold(physical_v, _hold_v, _hold_delta)
                            n_inside = int(inside.sum())
                            _counts["inside"] += n_inside
                            _counts["outside"] += state.numel() - n_inside
                            return torch.where(inside, state + delta / _scale, state)
                    state_bound = bound
                elif args.encoding == "asinh-ideal":
                    # Ideal invertible voltage map. Charge-domain implementation
                    # of its nonlinear update is deliberately not assumed.
                    scale = maximum / gain
                    arc_range = math.asinh(gain)
                    def clipped_candidate(current, elapsed, *, _original=original_candidate):
                        return _original(current, elapsed)
                    def add_noise(state, current, *, _scale=scale, _arc=arc_range):
                        encoded = torch.asinh(state / _scale)
                        noise = torch.randn_like(current) * (injected_sigma_uv * 1e-6 * _arc / 0.9)
                        return _scale * torch.sinh((encoded + noise).clamp(-_arc, _arc))
                    state_bound = maximum
                elif args.encoding=='measured-mos-ideal-inverse':
                    current_scale=physical_current_knots[-1]/maximum
                    def map_signed(value, source, destination):
                        value=value.clamp(min=source[0],max=source[-1])
                        indices=torch.bucketize(value.contiguous(),source[1:-1])
                        x0,x1=source[indices],source[indices+1]
                        y0,y1=destination[indices],destination[indices+1]
                        return y0+(value-x0)*(y1-y0)/(x1-x0)
                    def clipped_candidate(current,elapsed,*,_original=original_candidate):
                        return _original(current,elapsed)
                    def add_noise(state,current,*,_scale=current_scale,_ki=physical_current_knots,_kv=physical_voltage_knots):
                        encoded=map_signed(state*_scale,_ki,_kv)
                        disturbed=(encoded+torch.randn_like(current)*injected_sigma_uv*1e-6).clamp(min=_kv[0],max=_kv[-1])
                        return map_signed(disturbed,_kv,_ki)/_scale
                    state_bound=maximum
                else:
                    scale = maximum / gain
                    arc_range = math.asinh(gain)
                    knots_x = torch.tensor(
                        [scale * math.sinh(arc_range * i / args.segments)
                         for i in range(args.segments + 1)], dtype=torch.float32)
                    knots_v = torch.linspace(0, 0.9, args.segments + 1)
                    def piecewise(value, source_knots, dest_knots):
                        magnitude = value.abs().clamp(max=source_knots[-1])
                        indices = torch.bucketize(magnitude.contiguous(), source_knots[1:-1])
                        x0, x1 = source_knots[indices], source_knots[indices + 1]
                        y0, y1 = dest_knots[indices], dest_knots[indices + 1]
                        return value.sign() * (y0 + (magnitude - x0) * (y1 - y0) / (x1 - x0))
                    def clipped_candidate(current, elapsed, *, _original=original_candidate):
                        return _original(current, elapsed)
                    def add_noise(state, current, *, _kx=knots_x, _kv=knots_v):
                        voltage = piecewise(state, _kx, _kv)
                        disturbed = (voltage + torch.randn_like(current) *
                                     (injected_sigma_uv * 1e-6)).clamp(-0.9, 0.9)
                        return piecewise(disturbed, _kv, _kx)
                    if hold is not None:
                        def apply_retention(state, *, _kx=knots_x, _kv=knots_v,
                                            _hold_v=hold_v, _hold_delta=hold_delta,
                                            _counts=retention_counts):
                            encoded_state_v = piecewise(state, _kx, _kv)
                            physical_v = encoded_state_v if vcm_differential_profile else 0.9 + encoded_state_v
                            delta, inside = interpolate_hold(physical_v, _hold_v, _hold_delta)
                            n_inside = int(inside.sum())
                            _counts["inside"] += n_inside
                            _counts["outside"] += physical_v.numel() - n_inside
                            decoded_voltage = (physical_v + delta if vcm_differential_profile else
                                               physical_v + delta - 0.9)
                            decoded = piecewise(decoded_voltage.clamp(-0.9, 0.9), _kv, _kx)
                            return torch.where(inside, decoded, state)
                    state_bound = maximum
                def apply_restore(state, *, _offset=args.restore_offset_uv*1e-6*maximum/(0.9*gain)):
                    return torch.where(state>=0,state*args.restore_gain_positive,state*args.restore_gain_negative)+_offset
                def clipped_forward(current, *fargs, _neuron=neuron, _original=original_forward,
                                    _bound=state_bound, _first=first, _add_noise=add_noise,
                                    _apply_retention=apply_retention,_apply_restore=apply_restore, **fkwargs):
                    if _first[0]:
                        _neuron._ensure_state(current)
                        if args.noise_mode in ("init-only", "reset-only", "writeback-every-bin"):
                            _neuron.membrane = _add_noise(_neuron.membrane, current)
                        _first[0] = False
                    else:
                        _neuron.membrane = _apply_retention(_neuron.membrane)
                    spikes = _original(current, *fargs, **fkwargs)
                    if args.noise_mode == "reset-only":
                        disturbed = _add_noise(_neuron.membrane, current)
                        _neuron.membrane = torch.where(spikes.bool(), disturbed, _neuron.membrane)
                    elif args.noise_mode == "writeback-every-bin":
                        _neuron.membrane = _add_noise(_neuron.membrane, current)
                    if restore_active:
                        _neuron.membrane = _apply_restore(_neuron.membrane)
                    _neuron.membrane = _neuron.membrane.clamp(-_bound, _bound)
                    return spikes
                neuron._candidate_membrane = clipped_candidate
                neuron.forward = clipped_forward
                if args.noise_mode == "threshold-only":
                    original_threshold = original_thresholds[name]
                    if args.encoding == "linear-clipped":
                        threshold_sigma_units = (injected_sigma_uv * 1e-6 /
                                                 (0.9 * gain / maxima[name]))
                        def noisy_threshold(current, *, _original=original_threshold,
                                            _sigma=threshold_sigma_units):
                            return _original(current) + torch.randn_like(current) * _sigma
                    elif args.encoding == "asinh-ideal":
                        threshold_scale = maxima[name] / gain
                        threshold_arc = math.asinh(gain)
                        def noisy_threshold(current, *, _original=original_threshold,
                                            _scale=threshold_scale, _arc=threshold_arc,
                                            _noise=injected_sigma_uv * 1e-6):
                            base = _original(current)
                            voltage = 0.9 * torch.asinh(base / _scale) / _arc
                            voltage = (voltage + torch.randn_like(current) * _noise).clamp(-0.9, 0.9)
                            return _scale * torch.sinh(voltage * _arc / 0.9)
                    else:
                        threshold_knots_x = torch.tensor(
                            [maxima[name] / gain * math.sinh(math.asinh(gain) * i / args.segments)
                             for i in range(args.segments + 1)], dtype=torch.float32)
                        threshold_knots_v = torch.linspace(0, 0.9, args.segments + 1)
                        def noisy_threshold(current, *, _original=original_threshold,
                                            _kx=threshold_knots_x, _kv=threshold_knots_v,
                                            _noise=injected_sigma_uv * 1e-6, _segments=args.segments):
                            def map_piecewise(value, source, dest):
                                magnitude = value.abs().clamp(max=source[-1])
                                indices = torch.bucketize(magnitude.contiguous(), source[1:-1])
                                x0, x1 = source[indices], source[indices + 1]
                                y0, y1 = dest[indices], dest[indices + 1]
                                return value.sign() * (y0 + (magnitude - x0) * (y1 - y0) / (x1 - x0))
                            encoded = map_piecewise(_original(current), _kx, _kv)
                            disturbed = (encoded + torch.randn_like(current) * _noise).clamp(-0.9, 0.9)
                            return map_piecewise(disturbed, _kv, _kx)
                    neuron._threshold_tensor = noisy_threshold
            got_spikes = []
            handle = stage.register_forward_hook(
                lambda _m, _i, out: got_spikes.append(out.detach().cpu().bool().clone()))
            with torch.inference_mode():
                model.reset()
                output = model(input_sequence)
            handle.remove()
            for name, neuron in selected_neurons:
                neuron._candidate_membrane = original_candidates[name]
                neuron.forward = original_forwards[name]
                neuron._threshold_tensor = original_thresholds[name]
            got_mask = output["segmentation_logits"].argmax(dim=1).detach().cpu()
            spike_mismatch = float((torch.stack(got_spikes) != baseline_spikes).float().mean())
            pixel_agreement = float((got_mask == baseline_mask).float().mean())
            labeled_accuracy = float((got_mask[valid] == selected_target[valid]).float().mean())
            trials.append({"linear_gain_relative_to_max_fitting_range": gain,
                           "near_zero_voltage_gain_relative_to_linear": (
                               gain / math.asinh(gain) if args.encoding == "asinh-ideal" else
                               gain / (args.segments * math.sinh(math.asinh(gain) / args.segments))
                               if args.encoding == "piecewise-ideal" else gain),
                           "seed": seed if args.noise_mode != "none" or args.linear_compute_noise_sigma_uv else None,
                           "final_fuse_spike_mismatch": spike_mismatch,
                           "segmentation_pixel_agreement_with_float": pixel_agreement,
                           "labeled_pixel_accuracy": labeled_accuracy,
                           "present_class_mean_iou": mean_iou(got_mask),
                           "measured_retention_window_state_accesses": retention_counts.copy()})
    if not restore_active and args.retention_law == "none" and args.noise_mode == "none" and args.linear_compute_noise_sigma_uv == 0 and (args.encoding != "linear-clipped" or 1 in gains) and any(
            trial["final_fuse_spike_mismatch"] or trial["segmentation_pixel_agreement_with_float"] != 1
            for trial in trials if args.encoding != "linear-clipped" or
            trial["linear_gain_relative_to_max_fitting_range"] == 1):
        raise RuntimeError("lossless encoding control changed the float baseline")
    report = {
        "test": "sky130_full_float_state_saturation_range_replay",
        "checkpoint_sha256": digest,
        "qat_or_quantized_reference_used": False,
        'affine_restore_active':restore_active,
        'restore_gain_positive':args.restore_gain_positive,
        'restore_gain_negative':args.restore_gain_negative,
        'restore_offset_uv_in_0p9v_normalization':args.restore_offset_uv,
        'restore_placement':'After each completed post-reset membrane update, including inactive neurons; initialization remains ideal. Model beta, weighted sum, threshold, subtractive reset/adaptation order retained.',
        'restore_scope':'Ideal per-record linear encoding with constant per-polarity affine restore extrapolated beyond measured small-signal voltages. Sensitivity only, not qualified transfer, physical correction, nonlinear encoding, sampled noise, device leakage, full validation accuracy or service acceptance.',
        'restore_source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in args.restore_source},
        'replay_source_sha256':replay_sha,
        'replay_source_snapshot':replay_snapshot.relative_to(ROOT).as_posix(),
        "record_index": args.record_index,
        "sequence_id": sequence_id,
        "frame_index": frame_index,
        "scope": args.scope,
        "full_frame": args.full_frame,
        "selected_patch_yx": selected,
        "headroom_v_each_polarity": 0.9,
        "noise_mode": args.noise_mode,
        "retention_law": args.retention_law,
        "retention_source": retention_file if hold is not None else None,
        "retention_profile_metadata": ({
            key: hold.get(key) for key in ("mos_corner", "temperature_c", "injector_bank_isolated_during_retention",
                                           "write_end_time_us", "hold_start_time_us", "access_switch",
                                           "simulation_completed")
        } if hold is not None else None),
        "retention_window_absolute_v": [float(hold_v[0]), float(hold_v[-1])] if hold is not None else None,
        "encoding": args.encoding,
        'measured_encoder':measured_encoder,
        "piecewise_segment_count": args.segments if args.encoding == "piecewise-ideal" else None,
        "gains": gains,
        "independent_10um_pair_ktc_proxy_uv_rms_at_0c": thermal_sigma_uv,
        "injected_state_noise_sigma_uv_rms": injected_sigma_uv if args.noise_mode != "none" else 0.0,
        "injected_threshold_noise_sigma_uv_rms": injected_sigma_uv if args.noise_mode == "threshold-only" else 0.0,
        "writeback_noise_on_all_post_bin_membranes": args.noise_mode == "writeback-every-bin",
        "linear_compute_noise_sigma_uv_rms": args.linear_compute_noise_sigma_uv,
        "linear_compute_noise_placement": "After beta/weighted sum, before threshold and state encoding; independent Gaussian proxy, not measured computation noise",
        "actor_max_absolute_candidate_model_units": maxima,
        "range_scope": args.range_scope,
        "channel_max_absolute_candidate_model_units": {name:value.flatten().tolist() for name,value in channel_maxima.items()},
        "baseline_labeled_pixel_accuracy": float((baseline_mask[valid] == selected_target[valid]).float().mean()),
        "baseline_present_class_mean_iou": mean_iou(baseline_mask),
        "trials": trials,
        "interpretation": ("Each actor (or channel in channel-range mode) is ideally per-record normalized to +/-0.9V. Linear-clipped mode clamps candidate and post-reset membrane at maximum/gain. Asinh-ideal mode uses the hypothetical invertible encoding V=0.9*asinh(m/(maximum/gain))/asinh(gain). Piecewise-ideal mode joins equally spaced voltage samples of that curve with straight segments and exact inverse interpolation. Both preserve the full observed range and translate Gaussian voltage noise through an ideal inverse. Their state-dependent updates and switching/encoding circuits do not exist in this study. Threshold-only mode adds zero-mean independent Gaussian voltage-equivalent noise to each actor threshold decision after scaling to that actor's +/-0.9V range; it models neither systematic offset nor measured circuit noise. Writeback-every-bin adds independent Gaussian noise at initial programming and to every post-bin membrane, including inactive neurons, as an illustrative shared-read/restore proxy; it does not establish actual switched-noise magnitude/correlation. "
                           "Optional independent Gaussian 10um-pair kT/C noise is applied at initialization and, in reset-only mode, after a spike while preserving subtractive reset. The retention option applies interpolated SKY130 TT 5ms MOS-gate/TG voltage drift before each update only within measured physical voltages; outside states remain ideal. The full-rail profile excludes its 0V-program case because physical sampling moved the gate below the documented NMOS VGS range. This is an optimistic sensitivity probe with ideal per-record gain/programming, no physical range update, readout or leakage compensation. The Gaussian mode is a proxy, not physical switched noise. No adaptive gain circuit, injector error, mismatch, PVT or timing is modeled. Three selected patches or two full frames are not a validation-set accuracy estimate."),
    }
    stem = (f"sky130_float_state_saturation_validation_{args.record_index}_"
            f"{args.scope.replace('-', '_')}_{'full' if args.full_frame else 'patches'}"
            f"_{args.noise_mode.replace('-', '_')}_g{'-'.join(f'{gain:g}' for gain in gains)}"
            f"{'_asinh_ideal' if args.encoding == 'asinh-ideal' else ''}"
            f"{f'_piecewise{args.segments}_ideal' if args.encoding == 'piecewise-ideal' else ''}"
            f"{f'_n{args.noise_sigma_uv:g}uv' if args.noise_sigma_uv is not None else ''}"
            f"{'_channel_ranges' if args.range_scope == 'channel' else ''}"
            f"{f'_compute_n{args.linear_compute_noise_sigma_uv:g}uv' if args.linear_compute_noise_sigma_uv else ''}"
            f"{'_mos_tt_retention_window' if args.retention_law == 'mos-tt-measured-window' else ''}"
            f"{'_mos_tt_rail_window' if args.retention_law == 'mos-tt-rail-window' else ''}"
            f"{'_mos_vcm_diff' if vcm_differential_profile else ''}"
            f"{f'_profile_{Path(args.retention_profile).stem}' if args.retention_profile else ''}")
    if restore_active:
        stem=f'analog_float_affine_restore_record{args.record_index}_{args.scope.replace("-","_")}_{"full" if args.full_frame else "patches"}_'+hashlib.sha256(stem.encode()+f'{args.restore_gain_positive},{args.restore_gain_negative},{args.restore_offset_uv}'.encode()).hexdigest()[:20]
    if measured_encoder:
        identity=hashlib.sha256(replay_source_bytes+json.dumps(measured_encoder,sort_keys=True).encode()+stem.encode()).hexdigest()[:20]
        stem=f'gf180_measured_encoder_float_record{args.record_index}_{args.scope.replace("-","_")}_{"full" if args.full_frame else "patches"}_{args.noise_mode.replace("-","_")}_{identity}'
        report['interpretation']=measured_encoder['scope']+' Original float signed contributions, beta, threshold/subtractive reset/adaptation semantics retained. Model scaling uses each actor maximum measured from the same baseline record and is optimistic. A full-frame sensitivity replay is not validation-set or chip qualification.'
        report['headroom_v_each_polarity']=None
        center=[row for row in dc['rows'] if abs(row['input_current_na'])==.1]
        central=(center[1]['v(enc)']-center[0]['v(enc)'])/.2
        half_span=(dc['rows'][-1]['v(enc)']-dc['rows'][0]['v(enc)'])/2
        for trial in report['trials']:
            trial['near_zero_voltage_gain_relative_to_linear']=central*float(physical_current_knots[-1])/half_span
            trial['near_zero_0p1pa_voltage_gain_relative_to_linear']=(dc['analysis'].get('near_zero_0p1pa_gain_mv_per_na',central*1000)/1000)*float(physical_current_knots[-1])/half_span
        report['measured_encoder']['noise_reduction_physically_implemented']=False
    (OUT / f"{stem}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"baseline_labeled_pixel_accuracy": report["baseline_labeled_pixel_accuracy"],
                      "trials": trials}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
