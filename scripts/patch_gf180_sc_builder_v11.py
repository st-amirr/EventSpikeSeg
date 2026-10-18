from pathlib import Path
src=Path('scripts/build_gf180_sc_state_packet_compact_v7.py');dst=Path('scripts/build_gf180_sc_state_packet_compact_v11.py')
s=src.read_text().replace('gf180_sc_state_packet_compact_v7','gf180_sc_state_packet_compact_v11')
s=s.replace('tracks = {net: 100000 + 1500 * i for i, net in enumerate(ports)}','shared_nets = {"STATE", "PKT_TOP", "PKT_BOTTOM", "VDD", "VSS"}\n    tracks = {net: 20000 + 1500 * i for i, net in enumerate(ports)}')
s=s.replace('''    for idx, (inst, name, dx, dy, layer, x1, y1, x2, y2, net, local_i, pin) in enumerate(pin_sources):
        px, py = dx + (x1 + x2) // 2, dy + (y1 + y2) // 2''','''    direct_pin_boxes = {}
    net_rx = {net: [] for net in ports}
    for idx, (inst, name, dx, dy, layer, x1, y1, x2, y2, net, local_i, pin) in enumerate(pin_sources):
        px, py = dx + (x1 + x2) // 2, dy + (y1 + y2) // 2
        if net not in shared_nets:
            assert net not in direct_pin_boxes, net
            direct_pin_boxes[net] = (layer, (dx + x1, dy + y1, dx + x2, dy + y2))
            continue''')
s=s.replace('''        ty = tracks[net]
        if inst == "packet" and pin == "M" and layer == "metal4":''','''        net_rx[net].append(rx)
        ty = tracks[net]
        if inst == "packet" and pin == "M" and layer == "metal4":''')
old='''    pin_boxes = {}
    for net in ports:
        ty = tracks[net]
        rect("metal5", (-30000, ty - 60, 120000, ty + 60))
        pin_boxes[net] = (-29920, ty - 20, -29880, ty + 20)'''
new='''    pin_boxes = dict(direct_pin_boxes)
    for net in ports:
        if net not in shared_nets:
            continue
        ty = tracks[net]
        xlo, xhi = min(net_rx[net]) - 200, max(net_rx[net]) + 200
        rect("metal5", (xlo, ty - 60, xhi, ty + 60))
        pin_boxes[net] = ("metal5", (xlo + 20, ty - 20, xlo + 60, ty + 20))'''
assert s.count(old)==1
s=s.replace(old,new)
old='''    for index, net in enumerate(ports, 1):
        lines += [
            f"rlabel metal5 s " + " ".join(map(str, pin_boxes[net])) + f" 4 {net}",
            f"port {index} nsew",
        ]'''
new='''    for index, net in enumerate(ports, 1):
        layer, box = pin_boxes[net]
        lines += [
            f"rlabel {layer} s " + " ".join(map(str, box)) + f" 4 {net}",
            f"port {index} nsew",
        ]'''
assert s.count(old)==1
s=s.replace(old,new)
dst.write_text(s)
