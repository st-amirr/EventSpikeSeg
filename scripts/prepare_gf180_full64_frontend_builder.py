"""Derive a physical RMS chain builder; preserve the consumed parent builder."""
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'scripts/build_gf180_scheduled_rms_resident_write.py'
target = ROOT / 'scripts/build_gf180_full64_rms_frontend_v1.py'
assert not target.exists()
text = source.read_text()
text = text.replace('gf180_scheduled_rms_resident_write_v1', 'gf180_full64_rms_frontend_v1')
start = text.index(" writer='gf180_sampled")
end = text.index('\n for name in names:', start)
text = text[:start] + " reducer='gf180_formatted_energy64_v3';frontend='gf180_rms_clip_strength_frontend_v2';mim='gf180_mim_5x5_ports_routed';names=[reducer,frontend]" + text[end:]
start = text.index(' ports=list(children[writer]')
end = text.index('\n # Reserve bbox', start)
text = text[:start] + ''' rm={p:('REDUCER_BIAS' if p=='BIAS' else p) for p in children[reducer][1]['ports']}
 fm={p:('FRONTEND_BIAS' if p=='BIAS' else p) for p in children[frontend][1]['ports']}
 ports=list(dict.fromkeys(list(rm.values())+list(fm.values())))
 local=['RMS_RAW','RMS_CLIP','ADAPT_AMP']
 nets=[p for p in ports if p not in local];localpins={};tracks={n:1800000+640*i for i,n in enumerate(nets)};layers={};uses=[]
 instances=[('full64_energy',reducer,0,rm),('adaptation_frontend',frontend,8800000,fm)]
''' + text[end:]
text = text.replace("'mos_count':618", "'mos_count':2397")
text = text.replace("'native_resistor_count':98", "'native_resistor_count':2866")
text = text.replace("'native_mim_count':72", "'native_mim_count':1056")
start = text.index("'scope':'Native618MOS")
end = text.index("','complete_PLIF_accepted'", start)
scope = ('Native2397MOS2866R1056MIM: actual64 candidate-minus-penalty formatters and64 energy/root receivers drive the native high-common-mode input buffer, offset conversion, clipping and strength product. ROOT is physically connected between qualified children; no ideal internal RMS voltage source. Candidate, shared penalty, offset reference, strength and voltage/bias references remain external. Separate64uA reducer and4uA frontend PMOS master domains and1uA supplied NF bias are retained. RMS_RAW/RMS_CLIP/ADAPT_AMP diagnostic pins stay local. Source/GDS exact graph qualification required; no child qualification transfer. No resident writer, sequencer, membrane decision/reset, model accuracy, full-population5ms or full-chip claim. Spacious characterization assembly is not dense area.')
text = text[:start] + "'scope':" + repr(scope)[:-1] + text[end:]
text = '# Derived from immutable builder SHA256 ' + hashlib.sha256(source.read_bytes()).hexdigest() + '\n' + text
target.write_text(text)
print(target)
