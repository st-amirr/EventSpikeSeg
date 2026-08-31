`timescale 1ns/1ps
module convolution_plif_actor #(
  parameter integer COORD_WIDTH    = 10,
  parameter integer WEIGHT_WIDTH   = 8,
  parameter integer KERNEL_WIDTH   = 3,
  parameter integer KERNEL_HEIGHT  = 3,
  parameter integer STRIDE_X       = 1,
  parameter integer STRIDE_Y       = 1,
  parameter integer DILATION_X     = 1,
  parameter integer DILATION_Y     = 1,
  parameter integer PAD_X          = 1,
  parameter integer PAD_Y          = 1,
  parameter integer OUTPUT_WIDTH   = 16,
  parameter integer OUTPUT_HEIGHT  = 16,
  parameter integer DEST_COUNT     = OUTPUT_WIDTH * OUTPUT_HEIGHT,
  parameter integer ADDRESS_WIDTH  = $clog2(DEST_COUNT),
  parameter integer TAP_COUNT      = KERNEL_WIDTH * KERNEL_HEIGHT,
  parameter integer USE_STATE_MACRO = 0,
  parameter logic signed [TAP_COUNT*WEIGHT_WIDTH-1:0] KERNEL_WEIGHTS = '0
) (
  input  logic clk,
  input  logic reset,
  input  logic presynaptic_valid,
  output logic presynaptic_ready,
  input  logic [COORD_WIDTH-1:0] presynaptic_x,
  input  logic [COORD_WIDTH-1:0] presynaptic_y,
  input  logic epoch_end_valid,
  output logic epoch_end_ready,
  input  logic [23:0] epoch_tag_i,
  input  logic [15:0] beta_i,
  input  logic signed [15:0] threshold_i,
  output logic spike_valid,
  input  logic spike_ready,
  output logic [ADDRESS_WIDTH-1:0] spike_destination_o,
  output logic epoch_done_valid,
  input  logic epoch_done_ready,
  output logic [23:0] epoch_tag_o,
  output logic initialization_done_o
);
  logic [TAP_COUNT-1:0] tap_valid;
  logic [TAP_COUNT*COORD_WIDTH-1:0] tap_x;
  logic [TAP_COUNT*COORD_WIDTH-1:0] tap_y;
  logic [TAP_COUNT*WEIGHT_WIDTH-1:0] tap_weight;
  logic [TAP_COUNT-1:0] pending_valid_reg;
  logic [TAP_COUNT*COORD_WIDTH-1:0] pending_x_reg;
  logic [TAP_COUNT*COORD_WIDTH-1:0] pending_y_reg;
  logic [TAP_COUNT*WEIGHT_WIDTH-1:0] pending_weight_reg;
  logic actor_contribution_valid;
  logic actor_contribution_ready;
  logic [ADDRESS_WIDTH-1:0] actor_destination;
  logic signed [WEIGHT_WIDTH-1:0] actor_weight;
  logic actor_epoch_end_valid;
  logic actor_epoch_end_ready;
  logic actor_address_error;
  integer selected_tap;
  integer tap;
  integer linear_destination;

  presynaptic_tap_array #(
    .COORD_WIDTH(COORD_WIDTH), .WEIGHT_WIDTH(WEIGHT_WIDTH),
    .KERNEL_WIDTH(KERNEL_WIDTH), .KERNEL_HEIGHT(KERNEL_HEIGHT),
    .STRIDE_X(STRIDE_X), .STRIDE_Y(STRIDE_Y), .DILATION_X(DILATION_X),
    .DILATION_Y(DILATION_Y), .PAD_X(PAD_X), .PAD_Y(PAD_Y),
    .OUTPUT_WIDTH(OUTPUT_WIDTH), .OUTPUT_HEIGHT(OUTPUT_HEIGHT)
  ) taps (
    .input_valid(presynaptic_valid && presynaptic_ready),
    .input_x(presynaptic_x), .input_y(presynaptic_y),
    .weights_i(KERNEL_WEIGHTS), .tap_valid_o(tap_valid), .tap_x_o(tap_x),
    .tap_y_o(tap_y), .tap_weight_o(tap_weight)
  );

  always_comb begin
    selected_tap = 0;
    for (tap = TAP_COUNT - 1; tap >= 0; tap = tap - 1)
      if (pending_valid_reg[tap]) selected_tap = tap;
    linear_destination =
      $unsigned(pending_y_reg[selected_tap*COORD_WIDTH +: COORD_WIDTH]) * OUTPUT_WIDTH +
      $unsigned(pending_x_reg[selected_tap*COORD_WIDTH +: COORD_WIDTH]);
    actor_destination = linear_destination[ADDRESS_WIDTH-1:0];
    actor_weight = pending_weight_reg[selected_tap*WEIGHT_WIDTH +: WEIGHT_WIDTH];
  end

  assign presynaptic_ready = (pending_valid_reg == 0) && actor_contribution_ready &&
                             !epoch_end_valid;
  assign actor_contribution_valid = (pending_valid_reg != 0);
  assign actor_epoch_end_valid = epoch_end_valid && (pending_valid_reg == 0);
  assign epoch_end_ready = actor_epoch_end_ready && (pending_valid_reg == 0);

  always_ff @(posedge clk) begin
    if (reset) begin
      pending_valid_reg <= '0;
      pending_x_reg <= '0;
      pending_y_reg <= '0;
      pending_weight_reg <= '0;
    end else begin
      if (presynaptic_valid && presynaptic_ready) begin
        pending_valid_reg <= tap_valid;
        pending_x_reg <= tap_x;
        pending_y_reg <= tap_y;
        pending_weight_reg <= tap_weight;
      end else if (actor_contribution_valid && actor_contribution_ready) begin
        pending_valid_reg[selected_tap] <= 1'b0;
      end
    end
  end

  asynchronous_plif_actor #(
    .ADDRESS_WIDTH(ADDRESS_WIDTH), .DEST_COUNT(DEST_COUNT),
    .WEIGHT_WIDTH(WEIGHT_WIDTH), .USE_STATE_MACRO(USE_STATE_MACRO)
  ) neuron_array (
    .clk, .reset, .contribution_valid(actor_contribution_valid),
    .contribution_ready(actor_contribution_ready), .destination_i(actor_destination),
    .weight_i(actor_weight), .epoch_end_valid(actor_epoch_end_valid),
    .epoch_end_ready(actor_epoch_end_ready), .epoch_tag_i, .beta_i, .threshold_i,
    .spike_valid, .spike_ready, .spike_destination_o, .epoch_done_valid,
    .epoch_done_ready, .epoch_tag_o, .address_error_o(actor_address_error),
    .initialization_done_o(initialization_done_o)
  );
endmodule
