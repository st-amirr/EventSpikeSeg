# SKY130HD standard-cell grid plus an explicit OpenRAM macro grid.  The
# bundled OpenRAM LEF names its supply pins "vdd" and "gnd" on met3, while
# the standard-cell library uses VPWR/VGND on met1.
add_global_connection -net {VDD} -inst_pattern {.*} -pin_pattern {^VDD$} -power
add_global_connection -net {VDD} -inst_pattern {.*} -pin_pattern {^VDDPE$}
add_global_connection -net {VDD} -inst_pattern {.*} -pin_pattern {^VDDCE$}
add_global_connection -net {VDD} -inst_pattern {.*} -pin_pattern {VPWR}
add_global_connection -net {VDD} -inst_pattern {.*} -pin_pattern {VPB}
add_global_connection -net {VDD} -inst_pattern {.*} -pin_pattern {^vdd$} -power
add_global_connection -net {VSS} -inst_pattern {.*} -pin_pattern {^VSS$} -ground
add_global_connection -net {VSS} -inst_pattern {.*} -pin_pattern {^VSSE$}
add_global_connection -net {VSS} -inst_pattern {.*} -pin_pattern {VGND}
add_global_connection -net {VSS} -inst_pattern {.*} -pin_pattern {VNB}
add_global_connection -net {VSS} -inst_pattern {.*} -pin_pattern {^gnd$} -ground
global_connect

set_voltage_domain -name {CORE} -power {VDD} -ground {VSS}

define_pdn_grid -name {grid} -voltage_domains {CORE} -pins {met5}
add_pdn_stripe -grid {grid} -layer {met1} -width {0.48} -pitch {5.44} \
  -offset {0} -followpins
add_pdn_stripe -grid {grid} -layer {met4} -width {1.600} -pitch {27.140} \
  -offset {13.570}
add_pdn_stripe -grid {grid} -layer {met5} -width {1.600} -pitch {27.200} \
  -offset {13.600}
add_pdn_connect -grid {grid} -layers {met1 met4}
add_pdn_connect -grid {grid} -layers {met4 met5}

define_pdn_grid -name {sram_grid} -voltage_domains {CORE} -macro \
  -cells {sky130_sram_1rw1r_80x64_8} -halo {2.0 2.0 2.0 2.0} \
  -grid_over_boundary
add_pdn_connect -grid {sram_grid} -layers {met3 met4}
