# ASAP7 Liberty time_unit is 1 ps: 5000 ps = 5 ns = 200 MHz.
create_clock -name core_clk -period 5000 [get_ports clk]
# Split large combinational broadcast nets before routing. The first extracted
# route localized all twelve 320 ps library-slew violations to one 136-sink net.
set_max_fanout 64 [current_design]
set_input_delay 500 -clock core_clk \
  [get_ports {presynaptic_valid presynaptic_x presynaptic_y epoch_end_valid \
              epoch_tag_i beta_i threshold_i spike_ready epoch_done_ready}]
set_output_delay 500 -clock core_clk [all_outputs]
set_false_path -from [get_ports reset]
