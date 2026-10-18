from pathlib import Path
s=Path('scripts/simulate_gf180_sc_state_packet_compact_v12_beta15_endpoint_screen_v1.py').read_text()
s=s.replace("SIM=CELL+'_beta15_endpoint_screen_v1'","SIM=CELL+'_beta_aux2_endpoint_screen_v1'")
s=s.replace("f'Vdata_{tag} data_{tag} 0 {init}',","f'Vdata_{tag} data_{tag} 0 {init}',f'Caux_{tag} aux_{tag} vcm_{tag} 2f',")
Path('scripts/simulate_gf180_sc_state_packet_compact_v12_beta_aux2_endpoint_screen_v1.py').write_text(s)
