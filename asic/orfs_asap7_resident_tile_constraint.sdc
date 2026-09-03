# ASAP7 Liberty time_unit is 1 ps: 5000 ps = 5 ns = 200 MHz.
create_clock -name core_clk -period 5000 [get_ports clk]
set_max_fanout 64 [current_design]
set_input_delay 500 -clock core_clk \
  [get_ports {presynaptic_valid_i presynaptic_spike_vector_i \
              completion_valid_i completion_tag_i result_ready_i}]
set_output_delay 500 -clock core_clk [all_outputs]
set_false_path -from [get_ports reset]
