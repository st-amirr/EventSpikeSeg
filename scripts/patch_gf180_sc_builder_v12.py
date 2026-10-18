from pathlib import Path
src=Path('scripts/build_gf180_sc_state_packet_compact_v11.py');dst=Path('scripts/build_gf180_sc_state_packet_compact_v12.py')
s=src.read_text().replace('gf180_sc_state_packet_compact_v11','gf180_sc_state_packet_compact_v12')
old='tracks = {net: 20000 + 1500 * i for i, net in enumerate(ports)}'
new='tracks = {"STATE": 16000, "PKT_TOP": 16400, "PKT_BOTTOM": 16800, "VDD": 17200, "VSS": 17600}'
assert s.count(old)==1
s=s.replace(old,new)
dst.write_text(s)
