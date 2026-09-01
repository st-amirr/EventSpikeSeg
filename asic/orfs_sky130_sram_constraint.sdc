# SKY130 Liberty uses nanoseconds: 20 ns = 50 MHz.
create_clock -name core_clk -period 20 [get_ports clk]
set_max_fanout 64 [current_design]
set_input_delay 2 -clock core_clk \
  [get_ports {presynaptic_valid presynaptic_x presynaptic_y epoch_end_valid \
              epoch_tag_i beta_i threshold_i spike_ready epoch_done_ready}]
set_output_delay 2 -clock core_clk [all_outputs]
set_false_path -from [get_ports reset]
