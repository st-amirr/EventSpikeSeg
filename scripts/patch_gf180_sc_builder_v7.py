from pathlib import Path
src=Path('scripts/build_gf180_sc_state_packet_compact_v6.py')
dst=Path('scripts/build_gf180_sc_state_packet_compact_v7.py')
s=src.read_text().replace('gf180_sc_state_packet_compact_v6','gf180_sc_state_packet_compact_v7')
start=s.index('        if inst == "packet" and pin == "M" and layer == "metal4":')
end=s.index('\n\n    pin_boxes = {}', start)
old=s[start:end]
new='''        if inst == "packet" and pin == "M" and layer == "metal4":
            # Keep the MIM bottom-terminal escape on its native metal4 layer.
            rect("metal4", (min(px, rx) - 40, py - 40, max(px, rx) + 40, py + 40))
            rect("metal4", (rx - 80, min(py, ty), rx + 80, max(py, ty) + 1))
            via4(rx, ty)
            continue
        if layer == "metal1" and inst == "packet":
            via1(px, py)
            via2(px, py)
            rect("metal3", (px - 90, py - 90, px + 90, py + 90))
            rect("metal4", (px - 80, py - 70, px + 80, py + 70))
            rect("via3", (px - 28, py - 28, px + 28, py + 28))
            via4(px, py)
        elif layer == "metal3":
            via3(px, py)
        elif layer == "metal4":
            via4(px, py)
        elif layer == "metal5":
            pass
        else:
            raise AssertionError((name, layer, pin))
        rect("metal5", (min(px, rx) - 50, py - 50, max(px, rx) + 50, py + 50))
        via4(rx, py)
        rect("metal4", (rx - 80, min(py, ty), rx + 80, max(py, ty) + 1))
        via4(rx, ty)'''
assert old.count('via4(edge_x, py)')==1
s=s[:start]+new+s[end:]
dst.write_text(s)
