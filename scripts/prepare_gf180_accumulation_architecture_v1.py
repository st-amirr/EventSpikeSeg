"""Bind existing categorical fabric/ingress interfaces for accumulation scope.

This creates RTL and a physical pin binding contract, not routed parent metal.
Analog magnitudes/signs and phases remain explicit external research interfaces.
"""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/analog_asic'
OUT = BASE / 'assembly/accumulation_architecture_v1'
TOP = 'gf180_analog_accumulation_architecture_v1'
PAIRS = [
    ('actor_in_valid_o', 'graph_valid_i', 25),
    ('actor_in_ready_i', 'graph_ready_o', 25),
    ('actor_in_payload_o', 'graph_payload_i', 800),
    ('actor_in_completion_o', 'graph_completion_i', 25),
    ('actor_in_bin_tag_o', 'graph_bin_tag_i', 600),
]


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def ports(path):
    header = path.read_text().split(');', 1)[0]
    result = {}
    for direction, hi, lo, name in re.findall(
            r'\b(input|output)\s+wire\s*(?:\[(\d+):(\d+)\]\s*)?(\w+)', header):
        width = int(hi) - int(lo) + 1 if hi else 1
        assert not lo or int(lo) == 0
        result[name] = (direction, width)
    assert result and 'clk' in result and 'reset' in result
    return result


def main():
    assert not OUT.exists(), 'Preserve previous evidence.'
    sources = {
        'fabric': ROOT / 'asic/analog/gf180_analog_full25_packet_fabric_v1.sv',
        'ingress': ROOT / 'asic/analog/gf180_analog_full25_actor_ingress_v2.sv',
    }
    manifests = {
        'fabric': BASE / 'assembly/full25_packet_fabric_v1/physical_macro.json',
        'ingress': BASE / 'assembly/full25_actor_ingress_v2/physical_macro.json',
    }
    pp = {k: ports(p) for k, p in sources.items()}
    physical = {k: json.loads(p.read_text()) for k, p in manifests.items()}
    connections = {k: {} for k in sources}
    declarations = ['  input wire clk', '  input wire reset']
    wires = []
    bindings = []
    for a, b, width in PAIRS:
        assert pp['fabric'][a][1] == pp['ingress'][b][1] == width
        assert pp['fabric'][a][0] != pp['ingress'][b][0]
        net = 'link__' + b.removesuffix('_i').removesuffix('_o')
        wires.append('  wire ' + (f'[{width-1}:0] ' if width > 1 else '') + net + ';')
        connections['fabric'][a] = connections['ingress'][b] = net
        for i in range(width):
            names = [f'{a}[{i}]', f'{b}[{i}]'] if width > 1 else [a, b]
            endpoints = []
            for side, name in zip(['fabric', 'ingress'], names):
                pin = physical[side]['ports'][name]
                expected = pp[side][a if side == 'fabric' else b][0].upper()
                assert pin['direction'] == expected
                assert pin['rectangles']
                endpoints.append(dict(instance=side.upper(), pin=name,
                                      direction=pin['direction'], rectangles=pin['rectangles']))
            bindings.append(dict(net=f'{net}[{i}]', endpoints=endpoints,
                                 physical_parent_route_complete=False))
    for side in sources:
        for name, (direction, width) in pp[side].items():
            if name in connections[side]:
                continue
            if name in ['clk', 'reset']:
                connections[side][name] = name
                continue
            external = side + '__' + name
            connections[side][name] = external
            declarations.append('  ' + direction + ' wire ' +
                                (f'[{width-1}:0] ' if width > 1 else '') + external)
    OUT.mkdir(parents=True)
    rtl = ROOT / 'asic/analog' / (TOP + '.sv')
    assert not rtl.exists()
    text = ('// Article accumulation scope: categorical routing only.\n'
            '// Trained-weight loading and output completion are not acceptance gates.\n'
            '// group_settled_done means actual analog accumulation has completed.\n'
            '// This wrapper does not implement the analog contribution producer.\n'
            f'module {TOP} (\n' + ',\n'.join(declarations) + '\n);\n' +
            '\n'.join(wires) + '\n')
    for side, path in sources.items():
        text += f'  {path.stem} {side.upper()} (\n'
        text += ',\n'.join(f'    .{port}({net})' for port, net in connections[side].items())
        text += '\n  );\n'
    rtl.write_text(text + 'endmodule\n', encoding='utf-8', newline='\n')
    evidence_paths = list(sources.values()) + list(manifests.values()) + [rtl, Path(__file__)]
    for side, manifest in physical.items():
        assert manifest['physical_implementation_completed']
        gds = [(ROOT / p, digest) for p, digest in manifest['sha256'].items() if p.endswith('.gds')]
        assert len(gds) == 1
        path, digest = gds[0]
        assert sha(path) == digest, ('stale physical artifact', side)
        evidence_paths.append(path)
    report = dict(
        stage='rtl_and_physical_pin_binding_contract', top=TOP,
        connected_rtl_signal_bits=len(bindings), actor_interfaces=25,
        physical_parent_route_complete=False, full_architecture_layout_complete=False,
        accumulation_5ms_accepted=False, bindings=bindings,
        external_boundaries=[
            'Analog contribution magnitude/sign and actual injector controls',
            'Membrane address/read/restore/capture/commit producer',
            'group_ready and group_settled_done from actual accumulation service',
            'Clock/reset/supplies and existing native phase controls',
            'Optional output/decision inputs for inter-layer event propagation',
        ],
        completion_scope=dict(
            input_event_accumulation_deadline_seconds=0.005,
            output_deadline_required=False, trained_weight_transfer_required=False,
            hardware_miou_required=False,
            supplied_actor_workloads_allowed=True,
        ),
        remaining_work=['Route physical fabric-to-ingress nets',
                        'Connect ingress destination addressing to native membrane services',
                        'Expose external analog contribution and required phase interfaces',
                        'Export full architecture GDS and boundary inventory',
                        'Run per-module accumulation/timing simulations'],
        sha256={p.relative_to(ROOT).as_posix(): sha(p) for p in evidence_paths},
    )
    (OUT / 'physical_binding_contract.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in [
        'stage', 'connected_rtl_signal_bits', 'actor_interfaces',
        'physical_parent_route_complete', 'accumulation_5ms_accepted']}))


if __name__ == '__main__':
    main()
