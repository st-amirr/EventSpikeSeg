`timescale 1ns/1ps
// Checkpoint-exact 1x1 resident readout hard-macro master.
module primitive_140k_readout_1x1_pnr_top (
  input logic clk, input logic reset,
  input logic in_valid_i, output logic in_ready_o,
  input logic [15:0] in_spike_vector_i,
  input logic in_completion_i, input logic [23:0] in_tag_i,
  output logic prediction_valid_o, input logic prediction_ready_i,
  output logic [0:0] prediction_x_o,
  output logic [0:0] prediction_y_o,
  output logic [2:0] prediction_class_o,
  output logic frame_done_valid_o, input logic frame_done_ready_i,
  output logic [23:0] frame_tag_o
);
  resident_temporal_class_readout #(
    .INPUT_CHANNELS(16), .CLASS_COUNT(6),
    .OUTPUT_WIDTH(1), .OUTPUT_HEIGHT(1),
    .PREDICTION_BINS(10), .TAG_WIDTH(24),
    .READOUT_WEIGHTS(2304'hfffe73ffdedeffe4edffcae6fff15ffff27a001433003b91ff535dffe8dfffc28900079d00219b000ef5ffc0cefffce5fff38e00038f000038ffd5b3ffed2dffd55affa923ffc1c9fef052ffbb15ffb277003538ffed36ff8392fc45ffffd0cd00096c0049100005bdfff74600091c002cabffec08ffdc7effd27fffe93effdc65ffc549000e27fff8dcffd985002919ffd67e0038f4fffca8fff774000df5001679ffff6bfff980ffef8fffe276ffeb45002aec000794fffa45ffbfd6fff611ffcf5bfffe0fffec35ffddac001e6200384e003784001e19000c32ffdb89ffd652ffee97fffba5002077001c5f00204dffa824ffdb06ffe80a00202dffc4db00043bffe9d600111bff63340003f1004524ffcb0f004832002276002306003157)
  ) readout (.*);
endmodule
