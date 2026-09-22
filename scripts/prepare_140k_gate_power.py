"""Small post-route functional simulations using retained 140k layouts."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path('/workspace')
BASE = ROOT/'artifacts/ASIC/primitive_characterization'

def parse_vcd(path):
    signals, values, snapshots = {}, {}, {}
    stamp = 0
    for line in path.read_text().splitlines():
        line = line.strip()
        if line.startswith('$var'):
            parts = line.split()
            signals[parts[3]] = (parts[4], int(parts[2]))
        elif line.startswith('#'):
            snapshots[stamp] = values.copy()
            stamp = int(line[1:])
        elif line.startswith('b'):
            value, code = line[1:].split()
            values[signals[code][0]] = int(value, 2)
        elif line and line[0] in '01' and line[1:] in signals:
            values[signals[line[1:]][0]] = int(line[0])
    snapshots[stamp] = values.copy()
    return dict(signals.values()), snapshots

def main():
    models = ROOT/'artifacts/ASIC_XL/activity/enc1_depthwise_1x1_beta48_gate/sim_models/stdcells'
    configs = [
        ('plif', 'primitive_140k_plif_1_pnr_top', 'ordinary_plif_1_checkpoint_exact',
         {'clk','reset','contribution_valid_i','weight_i','dense_current_valid_i',
          'dense_current_delta_i','completion_valid_i','completion_tag_i','spike_ready_i'},
         ['spike_valid_o','spike_o','completion_tag_o']),
        ('conv9','primitive_140k_conv9_pnr_top','detail_stem_conv9_checkpoint_exact',
         {'clk','spike_vector_i'}, ['current_delta_o']),
        ('readout','primitive_140k_readout_1x1_pnr_top','readout_1x1_checkpoint_exact',
         {'clk','reset','in_valid_i','in_spike_vector_i','in_completion_i','in_tag_i','prediction_ready_i','frame_done_ready_i'},
         ['in_ready_o','prediction_valid_o','prediction_class_o','prediction_x_o','prediction_y_o','frame_done_valid_o','frame_tag_o']),
    ]
    manifest = []
    for label, top, directory, inputs, checks in configs:
        source_dir = ROOT/'artifacts/ASIC/primitive_characterization'/directory
        OUT = source_dir
        source = next(p for p in source_dir.glob('*.vcd') if not p.name.endswith('_gate.vcd'))
        signals, snapshots = parse_vcd(source)
        result = ROOT/'artifacts/OpenROAD/results/asap7'/top/'checkpoint_exact'
        assert (result/'6_final.gds').is_file()
        lines = ['`timescale 1ps/1ps', f'module {label}_tb;']
        for name, width in signals.items():
            shape = f'[{width-1}:0] ' if width > 1 else ''
            lines.append(f'{"reg" if name in inputs else "wire"} {shape}{name};')
        lines.append(f'{top} dut (' + ','.join(f'.{name}({name})' for name in signals) + ');')
        lines += ['initial begin', f'$dumpfile("{label}_gate.vcd");', f'$dumpvars(0,{label}_tb);']
        now, count, old_clk = 0, 0, 0
        for stamp, values in sorted(snapshots.items()):
            lines.append(f'#{stamp-now};')
            for name in sorted(inputs):
                lines.append(f'{name} = {signals[name]}\'h{values.get(name,0):x};')
            rising = values.get('clk',0) == 1 and old_clk == 0
            old_clk = values.get('clk',0)
            now = stamp
            # Readout reference samples describe state BEFORE the cycle's rising edge.
            check_now = values.get('clk',0) == 0 if label == 'readout' else (label == 'conv9' or rising)
            if check_now and stamp > 0:
                lines.append('#1;')
                now += 1
                for name in checks:
                    if label == 'readout' and name == 'prediction_class_o' and not values['prediction_valid_o']:
                        continue
                    if label == 'readout' and name == 'frame_tag_o' and not values['frame_done_valid_o']:
                        continue
                    lines.append(f'if ({name} !== {signals[name]}\'h{values[name]:x}) $fatal(1,"{label} {name} mismatch at {stamp} ps");')
                count += 1
        lines += [f'$display("PASS {label}: {count} output checks");', '$finish;', 'end', 'endmodule']
        (OUT/f'{label}_tb.sv').write_text('\n'.join(lines)+'\n')
        tcl = f'''set platform /OpenROAD-flow-scripts/flow/platforms/asap7
foreach lib [glob $platform/lib/NLDM/*RVT*TT*.lib*] {{ read_liberty $lib }}
read_db {result}/6_final.odb
read_sdc {result}/6_final.sdc
read_spef {result}/6_final.spef
read_vcd -scope {label}_tb/dut {OUT}/{label}_gate.vcd
report_activity_annotation > {OUT}/{label}_annotation.rpt
report_activity_annotation -report_unannotated > {OUT}/{label}_unannotated.rpt
report_power -digits 9 > {OUT}/{label}_power.rpt
puts "POWER_PASS {label}"
'''
        (OUT/f'{label}_power.tcl').write_text(tcl)
        manifest.append({'block':label,'result_directory':str(source_dir.relative_to(ROOT)),'top':top,'checks':count,'simulation':'post-route functional zero-delay; extracted SPEF power; no SDF/glitch claim',
                         'trace_ps':max(snapshots),'reference_vcd_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                         'netlist_sha256':hashlib.sha256((result/'6_final.v').read_bytes()).hexdigest(),
                         'gds_sha256':hashlib.sha256((result/'6_final.gds').read_bytes()).hexdigest()})
    (BASE/'base_140k_inventory/gate_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Prepared three small gate simulations from existing routed netlists')


def prepare_mechanisms():
    """Bounded checks of existing combinational mechanism layout checkpoints."""
    cases = [
        ('inhibition','stem_inhibition_32_checkpoint_exact','stem_inhibition_32'),
        ('penalty_lane','down2_adaptation_penalty_lane_checkpoint_exact','down2_adaptation_penalty_lane'),
        ('square_lane','down2_adaptation_square_lane_checkpoint_exact','down2_adaptation_square_lane'),
        ('commit_lane','down2_adaptation_commit_lane_checkpoint_exact','down2_adaptation_commit_lane'),
        ('penalty_direct','down2_adaptation_penalty_reduce64_checkpoint_exact','down2_adaptation_penalty_reduce64'),
        ('penalty_lower','adaptation_penalty_reduce64_lower_checkpoint_exact','down2_adaptation_penalty_reduce64'),
        ('penalty_upper','adaptation_penalty_reduce64_upper_checkpoint_exact','down2_adaptation_penalty_reduce64'),
        ('energy64','down2_adaptation_energy_reduce64_checkpoint_exact','down2_adaptation_energy_reduce64'),
        ('energy128','adaptation_energy_reduce128_checkpoint_exact','adaptation_energy_reduce128'),
    ]
    manifest=[]
    for label,directory,stem in cases:
        dest=BASE/directory
        top='primitive_140k_'+stem+'_pnr_top'
        result=ROOT/'artifacts/OpenROAD/results/asap7'/top/'checkpoint_exact'
        original=json.loads((dest/'activity_manifest.json').read_text())
        n=int(original['samples'])
        sample_count={'inhibition':16,'energy64':8,'energy128':4}.get(label,64)
        indices=[int((i+0.5)*n/sample_count) for i in range(sample_count)]
        wanted={i*5000 for i in indices}
        source=next(x for x in dest.glob('*activity.vcd'))
        assert hashlib.sha256(source.read_bytes()).hexdigest()==original['vcd_sha256']
        signals,values,samples={}, {}, {}
        stamp=0
        with source.open() as handle:
            for line in handle:
                line=line.strip()
                if line.startswith('$var'):
                    parts=line.split(); signals[parts[3]]=(parts[4],int(parts[2]))
                elif line.startswith('#'):
                    if stamp in wanted:samples[stamp]=values.copy()
                    stamp=int(line[1:])
                elif line.startswith('b'):
                    value,code=line[1:].split(); values[signals[code][0]]=int(value,2)
                elif line and line[0] in '01' and line[1:] in signals:
                    values[signals[line[1:]][0]]=int(line[0])
            if stamp in wanted:samples[stamp]=values.copy()
        assert len(samples)==sample_count
        widths=dict(signals.values())
        inputs={name for name in widths if name=='clk' or name.endswith('_i')}
        outputs=set(widths)-inputs
        final=(result/'6_final.odb').exists()
        checkpoint='6_final' if final else '5_1_grt'
        assert (result/f'{checkpoint}.odb').is_file()
        netlist=result/'6_final.v' if final else dest/f'{label}_layout.v'
        load=f"read_db {result}/{checkpoint}.odb\nread_sdc {result}/{checkpoint}.sdc\n"
        libraries="set platform /OpenROAD-flow-scripts/flow/platforms/asap7\nforeach lib [glob $platform/lib/NLDM/*RVT*TT*.lib*] { read_liberty $lib }\n"
        (dest/f'{label}_export.tcl').write_text(libraries+load+f'write_verilog -remove_cells {{TAPCELL_ASAP7_75t_R}} {netlist}\n') if not final else None
        parasitics=f'read_spef {result}/6_final.spef\n' if final else 'source $platform/setRC.tcl\nestimate_parasitics -global_routing\n'
        power=libraries+load+parasitics+f"""read_vcd -scope {label}_tb/dut {dest}/{label}_gate.vcd
report_activity_annotation > {dest}/{label}_annotation.rpt
report_activity_annotation -report_unannotated > {dest}/{label}_unannotated.rpt
report_power -digits 9 > {dest}/{label}_power.rpt
puts "POWER_PASS {label}"
"""
        (dest/f'{label}_power.tcl').write_text(power)
        lines=['`timescale 1ps/1ps',f'module {label}_tb;']
        for name,width in widths.items():
            lines.append(f'{"reg" if name in inputs else "wire"} '+(f'[{width-1}:0] ' if width>1 else '')+name+';')
        lines += [f'{top} dut ('+','.join(f'.{name}({name})' for name in widths)+');',
                  'initial begin',f'$dumpfile("{label}_gate.vcd");',f'$dumpvars(0,{label}_tb);']
        for _,sample in sorted(samples.items()):
            for name in sorted(inputs):lines.append(f"{name} = {widths[name]}'h{sample[name]:x};")
            lines.append('#1;')
            for name in sorted(outputs):
                lines.append(f"if ({name} !== {widths[name]}'h{sample[name]:x}) $fatal(1,\"{label} {name} mismatch\");")
            lines += ['#2499; clk=1;', '#2500; clk=0;']
        lines += [f'$display("PASS {label}: {sample_count} output checks");','$finish;','end','endmodule']
        (dest/f'{label}_tb.sv').write_text('\n'.join(lines)+'\n')
        manifest.append({'block':label,'top':top,'result_directory':str(dest.relative_to(ROOT)),
                         'netlist':str(netlist.relative_to(ROOT)),'physical_stage':'detailed_route' if final else 'global_route_estimated_parasitics',
                         'checks':sample_count,'operations':sample_count,'trace_duration_ps':sample_count*5000,
                         'sampling':f'{sample_count} midpoint samples from original synthetic pool; small-sample activity proxy, not accuracy validation',
                         'source_samples':n,'source_indices':indices,'reference_vcd_sha256':original['vcd_sha256'],
                         'layout_sha256':hashlib.sha256((result/f'{checkpoint}.odb').read_bytes()).hexdigest()})
    (BASE/'base_140k_inventory/mechanism_gate_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Prepared nine bounded tests in existing mechanism directories; no new layout.')

if __name__ == '__main__':
    import sys
    prepare_mechanisms() if '--mechanisms' in sys.argv else main()



