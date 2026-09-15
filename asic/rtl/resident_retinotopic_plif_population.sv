`timescale 1ns/1ps
// Fully resident mechanism-enabled PLIF population. Every channel/spatial
// neuron owns one combined accumulator/state plus compact adaptation age and
// amplitude state. At completion all spatial peer groups commit in parallel; no addressed
// state memory, touched bitmap, touched queue, or last-bin tag is required.
module resident_retinotopic_plif_population #(
  parameter integer DEST_COUNT = 8,
  parameter integer ADDRESS_WIDTH = (DEST_COUNT <= 1) ? 1 : $clog2(DEST_COUNT),
  parameter integer CHANNEL_COUNT = 2,
  parameter integer SPATIAL_DEST_COUNT = DEST_COUNT/CHANNEL_COUNT,
  parameter integer CONTRIBUTION_LANES = 1,
  parameter integer WEIGHT_WIDTH = 24,
  parameter integer CURRENT_WIDTH = 32,
  parameter integer MEM_WIDTH = 24,
  parameter integer BETA_WIDTH = 24,
  parameter integer BETA_FRAC_BITS = 23,
  parameter integer TAG_WIDTH = 24,
  parameter integer AGE_WIDTH = 6,
  parameter integer AMPLITUDE_WIDTH = 19,
  parameter integer DURATION_WIDTH = 21,
  parameter integer ENABLE_INHIBITION = 0,
  parameter integer ENABLE_ADAPTATION = 0,
  parameter logic [CHANNEL_COUNT*BETA_WIDTH-1:0] CHANNEL_BETAS = '0,
  parameter logic signed [CHANNEL_COUNT*MEM_WIDTH-1:0] CHANNEL_THRESHOLDS = '0,
  parameter logic [MEM_WIDTH-1:0] INHIBITION_STRENGTH = '0,
  parameter logic [AMPLITUDE_WIDTH-1:0] ADAPTATION_STRENGTH = '0,
  parameter logic [DURATION_WIDTH-1:0] ADAPTATION_DURATION = '0
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
  localparam integer MAX_MEM = (1 << (MEM_WIDTH-1))-1;
  localparam integer MIN_MEM = -(1 << (MEM_WIDTH-1));
  localparam logic [AGE_WIDTH-1:0] INACTIVE_AGE = {AGE_WIDTH{1'b1}};

  // These are physical resident registers, not addressed memories. Packing
  // them prevents synthesis from constructing a large inferred-memory
  // write-priority network before eventually lowering it back to registers.
  logic signed [DEST_COUNT*CURRENT_WIDTH-1:0] accumulator_reg;
  logic [DEST_COUNT*AGE_WIDTH-1:0] age_reg;
  logic [DEST_COUNT*AMPLITUDE_WIDTH-1:0] amplitude_reg;
  logic signed [DEST_COUNT*MEM_WIDTH-1:0] candidates;
  logic signed [DEST_COUNT*MEM_WIDTH-1:0] mechanism_membranes;
  logic [DEST_COUNT-1:0] mechanism_spikes;
  logic [DEST_COUNT*AGE_WIDTH-1:0] mechanism_ages;
  logic [DEST_COUNT*AMPLITUDE_WIDTH-1:0] mechanism_amplitudes;
  logic [DEST_COUNT*AGE_WIDTH-1:0] resident_ages;
  logic [DEST_COUNT*AMPLITUDE_WIDTH-1:0] resident_amplitudes;
  logic [DEST_COUNT*TAG_WIDTH-1:0] one_elapsed_bin;
  logic holding_result_reg;
  integer error_lane;

  initial begin
    if (DEST_COUNT != CHANNEL_COUNT*SPATIAL_DEST_COUNT)
      $error("resident retinotopic dimensions are inconsistent");
  end

  assign contribution_ready_o = !holding_result_reg && !completion_valid_i;
  assign dense_current_ready_o = !holding_result_reg && !completion_valid_i;
  assign completion_ready_o = !holding_result_reg;
  assign spike_valid_o = holding_result_reg;

  // Constant indices keep each physical neuron independent during lowering.
  genvar neuron;
  generate for (neuron = 0; neuron < DEST_COUNT; neuron = neuron+1) begin : neurons
    localparam integer CHANNEL = neuron/SPATIAL_DEST_COUNT;
    localparam integer PEER = (neuron%SPATIAL_DEST_COUNT)*CHANNEL_COUNT+CHANNEL;
    integer lane;
    integer signed candidate;
    integer signed accumulated;
    // Q15.16 membrane times Q0.23 beta needs 48 signed bits.  Keep the full
    // product until the rounded right shift.
    longint signed product;
    integer signed leaked;

    always @* begin
      candidate = $signed(accumulator_reg[neuron*CURRENT_WIDTH +: CURRENT_WIDTH]);
      if (candidate > MAX_MEM) candidate = MAX_MEM;
      else if (candidate < MIN_MEM) candidate = MIN_MEM;
      candidates[PEER*MEM_WIDTH +: MEM_WIDTH] = candidate[MEM_WIDTH-1:0];
    end
    assign resident_ages[PEER*AGE_WIDTH +: AGE_WIDTH] =
      age_reg[neuron*AGE_WIDTH +: AGE_WIDTH];
    assign resident_amplitudes[PEER*AMPLITUDE_WIDTH +: AMPLITUDE_WIDTH] =
      amplitude_reg[neuron*AMPLITUDE_WIDTH +: AMPLITUDE_WIDTH];
    assign one_elapsed_bin[PEER*TAG_WIDTH +: TAG_WIDTH] =
      {{(TAG_WIDTH-1){1'b0}}, 1'b1};

    always_ff @(posedge clk) begin
      if (reset) begin
        accumulator_reg[neuron*CURRENT_WIDTH +: CURRENT_WIDTH] <= '0;
        age_reg[neuron*AGE_WIDTH +: AGE_WIDTH] <= INACTIVE_AGE;
        amplitude_reg[neuron*AMPLITUDE_WIDTH +: AMPLITUDE_WIDTH] <= '0;
        spike_vector_o[neuron] <= 1'b0;
      end else if (holding_result_reg) begin
        if (spike_ready_i) spike_vector_o[neuron] <= 1'b0;
      end else if (completion_valid_i && completion_ready_o) begin
        spike_vector_o[neuron] <= mechanism_spikes[PEER];
        product = $signed(mechanism_membranes[PEER*MEM_WIDTH +: MEM_WIDTH]) *
                  $signed({1'b0, CHANNEL_BETAS[CHANNEL*BETA_WIDTH +: BETA_WIDTH]});
        if (product >= 0)
          leaked = (product + (1 << (BETA_FRAC_BITS-1))) >>> BETA_FRAC_BITS;
        else
          leaked = -(((-product) + (1 << (BETA_FRAC_BITS-1))) >>> BETA_FRAC_BITS);
        accumulator_reg[neuron*CURRENT_WIDTH +: CURRENT_WIDTH] <= leaked[CURRENT_WIDTH-1:0];
        age_reg[neuron*AGE_WIDTH +: AGE_WIDTH] <= mechanism_ages[PEER*AGE_WIDTH +: AGE_WIDTH];
        amplitude_reg[neuron*AMPLITUDE_WIDTH +: AMPLITUDE_WIDTH] <=
          mechanism_amplitudes[PEER*AMPLITUDE_WIDTH +: AMPLITUDE_WIDTH];
      end else begin
        accumulated = $signed(accumulator_reg[neuron*CURRENT_WIDTH +: CURRENT_WIDTH]);
        if (dense_current_valid_i)
          accumulated = accumulated + $signed(dense_current_delta_i[neuron*CURRENT_WIDTH +: CURRENT_WIDTH]);
        for (lane = 0; lane < CONTRIBUTION_LANES; lane = lane+1)
          if (contribution_valid_i[lane] &&
              $unsigned(destination_i[lane*ADDRESS_WIDTH +: ADDRESS_WIDTH]) == neuron)
            accumulated = accumulated + $signed(weight_i[lane*WEIGHT_WIDTH +: WEIGHT_WIDTH]);
        if (accumulated > MAX_CURRENT)
          accumulator_reg[neuron*CURRENT_WIDTH +: CURRENT_WIDTH] <= MAX_CURRENT;
        else if (accumulated < MIN_CURRENT)
          accumulator_reg[neuron*CURRENT_WIDTH +: CURRENT_WIDTH] <= MIN_CURRENT;
        else
          accumulator_reg[neuron*CURRENT_WIDTH +: CURRENT_WIDTH] <= accumulated[CURRENT_WIDTH-1:0];
      end
    end
  end endgenerate

  genvar generated_spatial;
  generate for (generated_spatial = 0;
                generated_spatial < SPATIAL_DEST_COUNT;
                generated_spatial = generated_spatial+1) begin : peer_groups
    retinotopic_mechanism_update #(
      .CHANNELS(CHANNEL_COUNT), .MEM_WIDTH(MEM_WIDTH), .AGE_WIDTH(AGE_WIDTH),
      .AMPLITUDE_WIDTH(AMPLITUDE_WIDTH), .DURATION_WIDTH(DURATION_WIDTH),
      .FRAC_BITS(16), .AGE_FRAC_BITS(0), .ELAPSED_WIDTH(TAG_WIDTH)
    ) mechanism (
      .candidates_i(candidates[
        generated_spatial*CHANNEL_COUNT*MEM_WIDTH +: CHANNEL_COUNT*MEM_WIDTH]),
      .base_thresholds_i(CHANNEL_THRESHOLDS),
      .update_mask_i({CHANNEL_COUNT{1'b1}}),
      .ages_i(resident_ages[
        generated_spatial*CHANNEL_COUNT*AGE_WIDTH +: CHANNEL_COUNT*AGE_WIDTH]),
      .amplitudes_i(resident_amplitudes[
        generated_spatial*CHANNEL_COUNT*AMPLITUDE_WIDTH +:
        CHANNEL_COUNT*AMPLITUDE_WIDTH]),
      .elapsed_bins_i(one_elapsed_bin[
        generated_spatial*CHANNEL_COUNT*TAG_WIDTH +: CHANNEL_COUNT*TAG_WIDTH]),
      .inhibition_enabled_i(ENABLE_INHIBITION != 0),
      .adaptation_enabled_i(ENABLE_ADAPTATION != 0),
      .inhibition_strength_i(INHIBITION_STRENGTH),
      .adaptation_strength_i(ADAPTATION_STRENGTH),
      .adaptation_duration_i(ADAPTATION_DURATION),
      .membranes_o(mechanism_membranes[
        generated_spatial*CHANNEL_COUNT*MEM_WIDTH +: CHANNEL_COUNT*MEM_WIDTH]),
      .spikes_o(mechanism_spikes[
        generated_spatial*CHANNEL_COUNT +: CHANNEL_COUNT]),
      .ages_o(mechanism_ages[
        generated_spatial*CHANNEL_COUNT*AGE_WIDTH +: CHANNEL_COUNT*AGE_WIDTH]),
      .amplitudes_o(mechanism_amplitudes[
        generated_spatial*CHANNEL_COUNT*AMPLITUDE_WIDTH +:
        CHANNEL_COUNT*AMPLITUDE_WIDTH]),
      .shared_penalty_o(), .membrane_energy_o()
    );
  end endgenerate

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
      for (error_lane = 0; error_lane < CONTRIBUTION_LANES; error_lane = error_lane+1)
        if (contribution_valid_i[error_lane] &&
            $unsigned(destination_i[error_lane*ADDRESS_WIDTH +: ADDRESS_WIDTH]) >= DEST_COUNT)
          address_error_o <= 1'b1;
    end
  end
endmodule
