from pathlib import Path
src=Path('scripts/build_gf180_sc_state_packet_compact_v12.py');dst=Path('scripts/build_gf180_sc_state_packet_compact_v13.py')
s=src.read_text().replace('gf180_sc_state_packet_compact_v12','gf180_sc_state_packet_compact_v13')
s=s.replace('tracks = {"STATE": 16000, "PKT_TOP": 16400, "PKT_BOTTOM": 16800, "VDD": 17200, "VSS": 17600}','tracks = {"STATE": 15400, "PKT_TOP": 16400, "PKT_BOTTOM": 17400, "VDD": 18400, "VSS": 19400}')
dst.write_text(s)
