# High-contrast GF180 layer colors; presentation only, unchanged GDS.
PALETTE={21:0x7D4F9F,22:0x5E966B,31:0xB73544,24:0x5C8FBC,30:0xB73544,32:0x7D4F9F,33:0x263F79,34:0x2868A0,35:0x302B2B,36:0x287A50,38:0x302B2B,40:0x302B2B,41:0x302B2B,42:0xA46C00,46:0x7D4F9F,81:0xB73544}
def apply_palette(view):
 it=view.begin_layers()
 while not it.at_end():
  p=it.current(); color=PALETTE.get(p.source_layer,0x263F79)
  p.fill_color=color; p.frame_color=color; p.width=4
  view.set_layer_properties(it,p); it.next()
