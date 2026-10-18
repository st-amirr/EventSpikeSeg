from pathlib import Path
s=Path('scripts/simulate_gf180_sc_state_packet_compact_v11_center_recalibrated_5ms_v1.py').read_text()
s=s.replace('gf180_sc_state_packet_compact_v11_center_recalibrated_5ms_v1','gf180_sc_state_packet_compact_v12_center_compensated_5ms_v1')
s=s.replace("CELL='gf180_sc_state_packet_compact_v11'","CELL='gf180_sc_state_packet_compact_v12'")
Path('scripts/simulate_gf180_sc_state_packet_compact_v12_center_compensated_5ms_v1.py').write_text(s)
