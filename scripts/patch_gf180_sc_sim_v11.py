from pathlib import Path
s=Path('scripts/simulate_gf180_sc_state_packet_compact_v7_center_signed_compensated_5ms_v2.py').read_text()
s=s.replace('gf180_sc_state_packet_compact_v7_center_signed_compensated_5ms_v2','gf180_sc_state_packet_compact_v11_center_signed_compensated_5ms_v1')
s=s.replace("CELL='gf180_sc_state_packet_compact_v7'","CELL='gf180_sc_state_packet_compact_v11'")
Path('scripts/simulate_gf180_sc_state_packet_compact_v11_center_signed_compensated_5ms_v1.py').write_text(s)
