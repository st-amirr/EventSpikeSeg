"""Prepare a source-linked 140k analog inventory and ideal sampled PLIF smoke test.

No transistor models, physical layout, or measured power are implied.
"""
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/analog_asic'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'artifacts/ASIC/model_spec.yaml'
    spec = json.loads(source.read_text())
    layers = [x for x in spec['layers'] if x.get('logical_membrane_states', 0)]
    assert len(layers) == 25
    assert sum(x['logical_membrane_states'] for x in layers) == 30976000
    hashes = {str(source.relative_to(ROOT)): hashlib.sha256(source.read_bytes()).hexdigest()}
    rows = []
    for layer in layers:
        param = ROOT / 'artifacts/ASIC' / layer['parameter_file']
        hashes[str(param.relative_to(ROOT))] = hashlib.sha256(param.read_bytes()).hexdigest()
        p = json.loads(param.read_text())
        betas = [x / 2**23 for x in p['beta_q']]
        rows.append(dict(name=layer['name'], membrane_capacitors=layer['logical_membrane_states'],
                         channels=layer['out_channels'], beta_min=min(betas), beta_max=max(betas),
                         parameters=layer['parameter_file'],
                         inhibition=bool(p.get('inhibition_enabled')),
                         adaptation=bool(p.get('threshold_adaptation_enabled'))))
    inventory = dict(model=spec['model'], checkpoint=spec['checkpoint'], actors=25,
                     graph_edges=len(spec['graph']['edges']), membrane_identities=30976000,
                     source_hashes=hashes, layers=rows,
                     evidence='Existing quantized checkpoint export; not original floating-point checkpoint extraction',
                     area_mm2=None, power_w=None, latency_s=None,
                     physical_layout_complete=False)
    (OUT / 'inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
    # Ordinary detail_stem channel 0 only. Normalized voltage is a mathematical
    # state, not a selected supply range. Signed states need a later common-mode
    # or differential circuit implementation. No circuit feasibility is claimed.
    p = json.loads((ROOT / 'artifacts/ASIC/parameters/00_detail_stem.json').read_text())
    beta, threshold = p['beta_q'][0] / 2**23, p['threshold_q'][0] / 2**16
    reference, stored_preleaked = 0.0, 0.0
    trace = []
    for n in range(80):
        current = (0.0, .12, -.08, .35, .04, -.2, .5, 0.0)[n % 8]
        candidate = beta * reference + current
        spike = int(candidate >= threshold)
        reference = candidate - spike * threshold
        analog_candidate = stored_preleaked + current
        analog_spike = int(analog_candidate >= threshold)
        analog_state = analog_candidate - analog_spike * threshold
        error = abs(reference - analog_state)
        assert spike == analog_spike and error < 1e-12
        stored_preleaked = beta * analog_state
        trace.append(dict(bin=n, current=current, reference=reference,
                          ideal_sampled_state=analog_state, spike=spike, error=error))
    with (OUT / 'ideal_plif_trace.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=trace[0])
        writer.writeheader(); writer.writerows(trace)
    result = dict(status='passed', samples=len(trace), max_error=max(x['error'] for x in trace),
                  beta=beta, threshold=threshold,
                  continuous_decay_tau_s=-.005/math.log(beta),
                  scope='Ideal sampled ordinary PLIF equation smoke test only; no saturation, adaptation, inhibition, noise, SPICE, or layout',
                  timing_note='Equivalent continuous tau is descriptive only; continuous event-time leak is not bin-equivalent',
                  measured_power_w=None, measured_latency_s=None)
    (OUT / 'ideal_plif_result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(actors=len(rows), states=30976000, smoke=result['status'], samples=80)))


if __name__ == '__main__':
    main()
