from pathlib import Path
src=Path('scripts/build_gf180_sc_state_packet_compact_v7.py');dst=Path('scripts/build_gf180_sc_state_packet_compact_v9.py')
s=src.read_text().replace('gf180_sc_state_packet_compact_v7','gf180_sc_state_packet_compact_v9')
s=s.replace('tracks = {net: 100000 + 1500 * i for i, net in enumerate(ports)}','tracks = {net: 20000 + 1500 * i for i, net in enumerate(ports)}')
dst.write_text(s)
