`timescale 1ns/1ps
// Fully resident ordinary PLIF population. Every logical neuron owns one
// combined accumulator/state element. Between completions it contains the
// already-leaked membrane for the current 5 ms bin plus all accepted synaptic
// contributions. Completion performs clamp/threshold/reset, then pre-applies
// beta so the same element is ready to accumulate the next bin.
module resident_plif_population #(
  parameter integer DEST_COUNT = 16,
  parameter integer ADDRESS_WIDTH = (DEST_COUNT <= 1) ? 1 : $clog2(DEST_COUNT),
  parameter integer CHANNEL_COUNT = 1,
  parameter integer SPATIAL_DEST_COUNT = DEST_COUNT/CHANNEL_COUNT,
  parameter integer CONTRIBUTION_LANES = 1,
  parameter integer WEIGHT_WIDTH = 24,
  parameter integer CURRENT_WIDTH = 32,
  parameter integer MEM_WIDTH = 24,
  parameter integer BETA_WIDTH = 24,
  parameter integer BETA_FRAC_BITS = 23,
  parameter integer TAG_WIDTH = 24,
  parameter logic [CHANNEL_COUNT*BETA_WIDTH-1:0] CHANNEL_BETAS = '0,
  parameter logic signed [CHANNEL_COUNT*MEM_WIDTH-1:0] CHANNEL_THRESHOLDS = '0
) (
  input logic clk, input logic reset,
  input logic [CONTRIBUTION_LANES-1:0] contribution_valid_i,
  output logic contribution_ready_o,
  input logic [CONTRIBUTION_LANES*ADDRESS_WIDTH-1:0] destination_i,
  input logic signed [CONTRIBUTION_LANES*WEIGHT_WIDTH-1:0] weight_i,
  input logic dense_current_valid_i, output logic dense_current_ready_o,
  input logic signed [DEST_COUNT*CURRENT_WIDTH-1:0] dense_current_delta_i,
  input logic completion_valid_i, output logic completion_ready_o,
  input logic [TAG_WIDTH-1:0] completion_tag_i,
  output logic spike_valid_o, input logic spike_ready_i,
  output logic [DEST_COUNT-1:0] spike_vector_o,
  output logic [TAG_WIDTH-1:0] completion_tag_o,
  output logic address_error_o
);
  localparam logic signed [CURRENT_WIDTH-1:0] MAX_CURRENT =
    {1'b0, {(CURRENT_WIDTH-1){1'b1}}};
  localparam logic signed [CURRENT_WIDTH-1:0] MIN_CURRENT =
    {1'b1, {(CURRENT_WIDTH-1){1'b0}}};
  // Keep the resident state explicitly packed.  An unpacked array makes
  // Yosys infer a multi-write memory and spend excessive time constructing
  // write-priority logic even though every element is a physical register.
  logic signed [DEST_COUNT*CURRENT_WIDTH-1:0] accumulator_reg;
  logic holding_result_reg;
  integer address_lane;

  assign contribution_ready_o = !holding_result_reg && !completion_valid_i;
  assign dense_current_ready_o = !holding_result_reg && !completion_valid_i;
  assign completion_ready_o = !holding_result_reg;
  assign spike_valid_o = holding_result_reg;

  // Shared handshake/tag/error registers have a single owner. Each generated
  // neuron below owns a fixed state word and spike bit, with identical timing.
  always_ff @(posedge clk) begin
    if (reset) begin
      holding_result_reg <= 1'b0;
      completion_tag_o <= '0;
      address_error_o <= 1'b0;
    end else if (holding_result_reg) begin
      if (spike_ready_i) holding_result_reg <= 1'b0;
    end else if (completion_valid_i && completion_ready_o) begin
      completion_tag_o <= completion_tag_i;
      holding_result_reg <= 1'b1;
    end else begin
      for (address_lane = 0; address_lane < CONTRIBUTION_LANES; address_lane = address_lane+1)
        if (contribution_valid_i[address_lane] &&
            $unsigned(destination_i[address_lane*ADDRESS_WIDTH +: ADDRESS_WIDTH]) >= DEST_COUNT)
          address_error_o <= 1'b1;
    end
  end

  generate
    for (genvar destination = 0; destination < DEST_COUNT; destination = destination+1) begin : neurons
      localparam integer CHANNEL = destination/SPATIAL_DEST_COUNT;
      integer lane;
      integer signed accumulated;
      // Q15.16 membrane times Q0.23 beta needs 48 signed bits.  A SystemVerilog
      // integer is only 32 bits and silently discarded the retained membrane
      // for realistic checkpoint values near 1.0.
      longint signed product;
      integer signed leaked;
      integer signed candidate;
      integer signed committed_membrane;
      integer signed threshold;
      always_ff @(posedge clk) begin
        if (reset) begin
          spike_vector_o[destination] <= 1'b0;
          accumulator_reg[destination*CURRENT_WIDTH +: CURRENT_WIDTH] <= '0;
        end else if (holding_result_reg) begin
          if (spike_ready_i) spike_vector_o[destination] <= 1'b0;
        end else if (completion_valid_i && completion_ready_o) begin
          candidate = $signed(accumulator_reg[destination*CURRENT_WIDTH +: CURRENT_WIDTH]);
          if (candidate > ((1 << (MEM_WIDTH-1))-1)) candidate = (1 << (MEM_WIDTH-1))-1;
          else if (candidate < -(1 << (MEM_WIDTH-1))) candidate = -(1 << (MEM_WIDTH-1));
          threshold = $signed(CHANNEL_THRESHOLDS[CHANNEL*MEM_WIDTH +: MEM_WIDTH]);
          if (candidate >= threshold) begin
            spike_vector_o[destination] <= 1'b1;
            committed_membrane = candidate-threshold;
          end else begin
            spike_vector_o[destination] <= 1'b0;
            committed_membrane = candidate;
          end
          product = committed_membrane *
                    $signed({1'b0, CHANNEL_BETAS[CHANNEL*BETA_WIDTH +: BETA_WIDTH]});
          if (product >= 0)
            leaked = (product + (1 << (BETA_FRAC_BITS-1))) >>> BETA_FRAC_BITS;
          else
            leaked = -(((-product) + (1 << (BETA_FRAC_BITS-1))) >>> BETA_FRAC_BITS);
          accumulator_reg[destination*CURRENT_WIDTH +: CURRENT_WIDTH] <= leaked[CURRENT_WIDTH-1:0];
        end else begin
          accumulated = $signed(accumulator_reg[destination*CURRENT_WIDTH +: CURRENT_WIDTH]);
          if (dense_current_valid_i)
            accumulated = accumulated + $signed(dense_current_delta_i[destination*CURRENT_WIDTH +: CURRENT_WIDTH]);
          for (lane = 0; lane < CONTRIBUTION_LANES; lane = lane+1)
            if (contribution_valid_i[lane] &&
                $unsigned(destination_i[lane*ADDRESS_WIDTH +: ADDRESS_WIDTH]) == destination)
              accumulated = accumulated + $signed(weight_i[lane*WEIGHT_WIDTH +: WEIGHT_WIDTH]);
          if (accumulated > MAX_CURRENT)
            accumulator_reg[destination*CURRENT_WIDTH +: CURRENT_WIDTH] <= MAX_CURRENT;
          else if (accumulated < MIN_CURRENT)
            accumulator_reg[destination*CURRENT_WIDTH +: CURRENT_WIDTH] <= MIN_CURRENT;
          else
            accumulator_reg[destination*CURRENT_WIDTH +: CURRENT_WIDTH] <= accumulated[CURRENT_WIDTH-1:0];
        end
      end
    end
  endgenerate
endmodule
