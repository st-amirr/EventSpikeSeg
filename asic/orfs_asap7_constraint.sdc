create_clock -name core_clk -period 5.0 [get_ports clk]
set_input_delay 0.5 -clock core_clk \
  [remove_from_collection [all_inputs] [get_ports {clk reset}]]
set_output_delay 0.5 -clock core_clk [all_outputs]
set_false_path -from [get_ports reset]
