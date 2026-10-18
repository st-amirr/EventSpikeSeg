from pathlib import Path
src=Path('scripts/build_gf180_sc_state_packet_compact_v9.py');dst=Path('scripts/build_gf180_sc_state_packet_compact_v10.py')
s=src.read_text().replace('gf180_sc_state_packet_compact_v9','gf180_sc_state_packet_compact_v10')
s=s.replace('''    for idx, (inst, name, dx, dy, layer, x1, y1, x2, y2, net, local_i, pin) in enumerate(pin_sources):''','''    net_rx = {net: [] for net in ports}
    for idx, (inst, name, dx, dy, layer, x1, y1, x2, y2, net, local_i, pin) in enumerate(pin_sources):''')
s=s.replace('''        ty = tracks[net]
        if inst == "packet" and pin == "M" and layer == "metal4":''','''        net_rx[net].append(rx)
        ty = tracks[net]
        if inst == "packet" and pin == "M" and layer == "metal4":''')
old='''    for net in ports:
        ty = tracks[net]
        rect("metal5", (-30000, ty - 60, 120000, ty + 60))
        pin_boxes[net] = (-29920, ty - 20, -29880, ty + 20)'''
new='''    for net in ports:
        ty = tracks[net]
        xlo, xhi = min(net_rx[net]) - 200, max(net_rx[net]) + 200
        rect("metal5", (xlo, ty - 60, xhi, ty + 60))
        pin_boxes[net] = (xlo + 20, ty - 20, xlo + 60, ty + 20)'''
assert s.count(old)==1
s=s.replace(old,new)
dst.write_text(s)
