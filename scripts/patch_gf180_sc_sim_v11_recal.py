from pathlib import Path
src=Path('scripts/simulate_gf180_sc_state_packet_compact_v11_center_signed_compensated_5ms_v1.py').read_text()
s=src.replace('gf180_sc_state_packet_compact_v11_center_signed_compensated_5ms_v1','gf180_sc_state_packet_compact_v11_center_recalibrated_5ms_v1')
s=s.replace("('pos',0.108),('neg',0.064)","('pos',0.102),('neg',0.046)")
Path('scripts/simulate_gf180_sc_state_packet_compact_v11_center_recalibrated_5ms_v1.py').write_text(s)
