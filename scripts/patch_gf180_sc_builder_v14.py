from pathlib import Path
src=Path('scripts/build_gf180_sc_state_packet_compact_v13.py');dst=Path('scripts/build_gf180_sc_state_packet_compact_v14.py')
s=src.read_text().replace('gf180_sc_state_packet_compact_v13','gf180_sc_state_packet_compact_v14')
s=s.replace('("packet", "gf180_mim_5x5_ports_routed", 60000, 0)','("packet", "gf180_mim_5x5_ports_routed", 38000, 6000)')
old='''        if inst == "state":
            rx = -20000 - idx * 500
        elif inst in ("park", "sample", "drive"):
            rx = 40000 + idx * 500
        elif inst == "packet" and pin == "M":
            rx = 55000
        elif inst == "packet" and pin == "P":
            rx = 70000
        elif inst == "packet" and pin == "VSS":
            rx = 80000
        else:
            rx = 70000'''
new='''        if inst == "packet" and pin == "M":
            rx = dx - 2500
        else:
            rx = px + 500 + ports.index(net) * 400 + local_i * 200'''
assert s.count(old)==1
s=s.replace(old,new)
dst.write_text(s)
