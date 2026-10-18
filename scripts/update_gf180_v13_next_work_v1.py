"""Update operational pointers after the V13 milestone; archive called separately."""
from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
def main():
 p=R/'docs/ACTIVE_TASKS.md';s=p.read_bytes();a=s.index(b'## Next work package');b=s.index(b'No critical user decision',a)
 replacement='''## Next work package

1. Complete global model connections and graph operators using the existing 43-node/54-edge original-float graph. Preserve spatial/channel addresses, binary residual OR semantics, nearest-neighbor fanout, concatenation and the unclipped two-spike skip sum. Existing corridors end at pads and are not connected operators. Connect actual producer/consumer interfaces; do not count corridor placement as completion.
2. Connect the original continuous parameter storage/distribution to shared weight-duration, beta, threshold and adaptation references. Retain the original epoch58 float checkpoint and distinct per-channel settings. Parameter capacity alone is insufficient.
3. Bind categorical addressing and phase sequencing to the completed membrane/adaptation/class-current access paths. Numerical state remains analog. Finish age advance, spike-qualified adaptation write and producer-to-RMS/sum connections.
4. Complete missing connected function simulations with bounded cases, reusing completed module evidence and carrying measured errors. Avoid precision sweeps. Evaluate parent loading and conditional service timing with explicit exclusions.
5. Publish the full research layout, views and per-module simulation package. Manufacture-ready signoff is outside scope; state whole-model accuracy and 5ms limitations clearly.

'''
 p.write_bytes(s[:a]+replacement.replace('\n','\r\n').encode()+s[b:])
 p=R/'docs/project_spec.yaml';s=p.read_bytes()
 for key,val in [('next_gate','bind_global_model_graph_operators_parameters_and_categorical_sequencing'),('    report','artifacts/analog_asic/results/gf180_class_current_shared_io_v1_native_readout_restore_capture_v2.json'),('    status','V13_all_numeric_state_access_built_native_class_restore_mux_capture_complete'),('    next_action','global_model_routing_operators_parameter_distribution_and_categorical_sequencer')]:
  prefix=('  '+key if not key.startswith(' ') else key)+': ';s,n=re.subn((re.escape(prefix)+'[^\r\n]+').encode(),(prefix+val).encode(),s,count=1);assert n==1,key
 p.write_bytes(s)
if __name__=='__main__':main()
