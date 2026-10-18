from pathlib import Path
p=Path('scripts/simulate_gf180_sc_state_packet_compact_v12_beta_aux_cap_sweep_v3.py');s=p.read_text().replace("SIM=CELL+'_beta_aux_cap_sweep_v3'","SIM=CELL+'_beta_aux_cap_sweep_v4'")
s=s.replace("f'Vwrite_{tag} write_{tag} 0 0',f'Vwriteb_{tag} writeb_{tag} 0 3.3'","f'Vwrite_{tag} write_{tag} 0 PWL(0 3.3 9.999u 3.3 10u 0 60u 0)',f'Vwriteb_{tag} writeb_{tag} 0 PWL(0 0 10u 0 10.001u 3.3 60u 3.3)'")
s=s.replace("f'Vdata_{tag} data_{tag} 0 {init}',","f'Vdata_{tag} data_{tag} 0 {init}',f'Vweight_{tag} weight_{tag} 0 1.65',")
s=s.replace('auxref_{tag} vcm_{tag} vcm_{tag} top_{tag}','auxref_{tag} vcm_{tag} weight_{tag} top_{tag}')
p2=Path('scripts/simulate_gf180_sc_state_packet_compact_v12_beta_aux_cap_sweep_v4.py');p2.write_text(s)
