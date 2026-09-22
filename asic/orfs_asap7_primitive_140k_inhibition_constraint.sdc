# ASAP7 Liberty time_unit is 1 ps: 20000 ps = 20 ns.
# The exact combinational 32-channel peer-inhibition/RMS group only needs to
# settle once per 5 ms model bin.
create_clock -name core_clk -period 20000 [get_ports clk]
set_max_fanout 64 [current_design]
set_input_delay 500 -clock core_clk \
  [get_ports -quiet {candidates_i update_mask_i}]
set_output_delay 500 -clock core_clk [all_outputs]
