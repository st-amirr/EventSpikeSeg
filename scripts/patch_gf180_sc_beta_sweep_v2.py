from pathlib import Path
s=Path('scripts/simulate_gf180_sc_state_packet_compact_v12_beta_aux_cap_sweep_v1.py').read_text()
s=s.replace("SIM=CELL+'_beta_aux_cap_sweep_v1'","SIM=CELL+'_beta_aux_cap_sweep_v2'")
s=s.replace("f'Vwrite_{tag} write_{tag} 0 PWL(0 3.3 9.999u 3.3 10u 0 60u 0)',f'Vwriteb_{tag} writeb_{tag} 0 PWL(0 0 9.999u 0 10u 3.3 60u 3.3)'","f'Vwrite_{tag} write_{tag} 0 0',f'Vwriteb_{tag} writeb_{tag} 0 3.3'")
Path('scripts/simulate_gf180_sc_state_packet_compact_v12_beta_aux_cap_sweep_v2.py').write_text(s)
