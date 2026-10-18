# Native nominal contact resistance: local open_pdks gf180mcuD.tech contact m2c,m3c,via3,via4 =4500 milliohm.
source /OpenROAD-flow-scripts/flow/platforms/gf180/setRC.tcl
foreach via {Via1 Via2 Via3 Via4} { set_layer_rc -via $via -resistance 4.5 }
