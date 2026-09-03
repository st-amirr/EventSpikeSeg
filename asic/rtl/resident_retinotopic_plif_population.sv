`timescale 1ns/1ps
// Fully resident mechanism-enabled PLIF population. Every channel/spatial
// neuron owns its current, membrane, adaptation age, and adaptation amplitude
// state. At completion all spatial peer groups commit in parallel; no addressed
// state memory, touched bitmap, touched queue, or last-bin tag is required.
module resident_retinotopic_plif_population #(
  parameter integer DEST_COUNT = 8,
  parameter integer ADDRESS_WIDTH = (DEST_COUNT <= 1) ? 1 : $clog2(DEST_COUNT),
  parameter integer CHANNEL_COUNT = 2,
  parameter integer SPATIAL_DEST_COUNT = DEST_COUNT/CHANNEL_COUNT,
  parameter integer CONTRIBUTION_LANES = 1,
  parameter integer WEIGHT_WIDTH = 8,
  parameter integer CURRENT_WIDTH = 24,
  parameter integer MEM_WIDTH = 16,
  parameter integer BETA_WIDTH = 16,
  parameter integer BETA_FRAC_BITS = 15,
  parameter integer TAG_WIDTH = 24,
  parameter integer AGE_WIDTH = 16,
  parameter integer ENABLE_INHIBITION = 0,
  parameter integer ENABLE_ADAPTATION = 0,
  parameter logic [CHANNEL_COUNT*BETA_WIDTH-1:0] CHANNEL_BETAS = '0,
  parameter logic signed [CHANNEL_COUNT*MEM_WIDTH-1:0] CHANNEL_THRESHOLDS = '0,
  parameter logic [MEM_WIDTH-1:0] INHIBITION_STRENGTH = '0,
  parameter logic [MEM_WIDTH-1:0] ADAPTATION_STRENGTH = '0,
  parameter logic [AGE_WIDTH-1:0] ADAPTATION_DURATION = '0
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
  localparam integer MAX_CURRENT = (1 << (CURRENT_WIDTH-1))-1;
  localparam integer MIN_CURRENT = -(1 << (CURRENT_WIDTH-1));
  localparam integer MAX_MEM = (1 << (MEM_WIDTH-1))-1;
  localparam integer MIN_MEM = -(1 << (MEM_WIDTH-1));
  localparam logic [AGE_WIDTH-1:0] INACTIVE_AGE = {AGE_WIDTH{1'b1}};

  logic signed [CURRENT_WIDTH-1:0] current_reg [0:DEST_COUNT-1];
  logic signed [MEM_WIDTH-1:0] membrane_reg [0:DEST_COUNT-1];
  logic [AGE_WIDTH-1:0] age_reg [0:DEST_COUNT-1];
  logic [MEM_WIDTH-1:0] amplitude_reg [0:DEST_COUNT-1];
  logic signed [CHANNEL_COUNT*MEM_WIDTH-1:0] candidates [0:SPATIAL_DEST_COUNT-1];
  logic signed [CHANNEL_COUNT*MEM_WIDTH-1:0] mechanism_membranes [0:SPATIAL_DEST_COUNT-1];
  logic [CHANNEL_COUNT-1:0] mechanism_spikes [0:SPATIAL_DEST_COUNT-1];
  logic [CHANNEL_COUNT*AGE_WIDTH-1:0] mechanism_ages [0:SPATIAL_DEST_COUNT-1];
  logic [CHANNEL_COUNT*MEM_WIDTH-1:0] mechanism_amplitudes [0:SPATIAL_DEST_COUNT-1];
  logic [CHANNEL_COUNT*AGE_WIDTH-1:0] resident_ages [0:SPATIAL_DEST_COUNT-1];
  logic [CHANNEL_COUNT*MEM_WIDTH-1:0] resident_amplitudes [0:SPATIAL_DEST_COUNT-1];
  logic [CHANNEL_COUNT*TAG_WIDTH-1:0] one_elapsed_bin [0:SPATIAL_DEST_COUNT-1];
  logic holding_result_reg;
  integer destination;
  integer lane;
  integer channel;
  integer spatial;
  integer signed accumulated;
  integer signed product;
  integer signed leaked;
  integer signed candidate;

  initial begin
    if (DEST_COUNT != CHANNEL_COUNT*SPATIAL_DEST_COUNT)
      $error("resident retinotopic dimensions are inconsistent");
  end

  assign contribution_ready_o = !holding_result_reg && !completion_valid_i;
  assign dense_current_ready_o = !holding_result_reg && !completion_valid_i;
  assign completion_ready_o = !holding_result_reg;
  assign spike_valid_o = holding_result_reg;

  // Repack channel-major resident state into one all-channel vector per pixel.
  always_comb begin
    for (spatial = 0; spatial < SPATIAL_DEST_COUNT; spatial = spatial+1) begin
      candidates[spatial] = '0;
      resident_ages[spatial] = '0;
      resident_amplitudes[spatial] = '0;
      one_elapsed_bin[spatial] = '0;
      for (channel = 0; channel < CHANNEL_COUNT; channel = channel+1) begin
        destination = channel*SPATIAL_DEST_COUNT+spatial;
        product = $signed(membrane_reg[destination]) *
                  $signed({1'b0, CHANNEL_BETAS[channel*BETA_WIDTH +: BETA_WIDTH]});
        if (product >= 0)
          leaked = (product + (1 << (BETA_FRAC_BITS-1))) >>> BETA_FRAC_BITS;
        else
          leaked = -(((-product) + (1 << (BETA_FRAC_BITS-1))) >>> BETA_FRAC_BITS);
        candidate = leaked + $signed(current_reg[destination]);
        if (candidate > MAX_MEM) candidate = MAX_MEM;
        else if (candidate < MIN_MEM) candidate = MIN_MEM;
        candidates[spatial][channel*MEM_WIDTH +: MEM_WIDTH] =
          candidate[MEM_WIDTH-1:0];
        resident_ages[spatial][channel*AGE_WIDTH +: AGE_WIDTH] =
          age_reg[destination];
        resident_amplitudes[spatial][channel*MEM_WIDTH +: MEM_WIDTH] =
          amplitude_reg[destination];
        one_elapsed_bin[spatial][channel*TAG_WIDTH +: TAG_WIDTH] =
          {{(TAG_WIDTH-1){1'b0}}, 1'b1};
      end
    end
  end

  genvar generated_spatial;
  generate for (generated_spatial = 0;
                generated_spatial < SPATIAL_DEST_COUNT;
                generated_spatial = generated_spatial+1) begin : peer_groups
    retinotopic_mechanism_update #(
      .CHANNELS(CHANNEL_COUNT), .MEM_WIDTH(MEM_WIDTH), .AGE_WIDTH(AGE_WIDTH),
      .ELAPSED_WIDTH(TAG_WIDTH)
    ) mechanism (
      .candidates_i(candidates[generated_spatial]),
      .base_thresholds_i(CHANNEL_THRESHOLDS),
      .update_mask_i({CHANNEL_COUNT{1'b1}}),
      .ages_i(resident_ages[generated_spatial]),
      .amplitudes_i(resident_amplitudes[generated_spatial]),
      .elapsed_bins_i(one_elapsed_bin[generated_spatial]),
      .inhibition_enabled_i(ENABLE_INHIBITION != 0),
      .adaptation_enabled_i(ENABLE_ADAPTATION != 0),
      .inhibition_strength_i(INHIBITION_STRENGTH),
      .adaptation_strength_i(ADAPTATION_STRENGTH),
      .adaptation_duration_i(ADAPTATION_DURATION),
      .membranes_o(mechanism_membranes[generated_spatial]),
      .spikes_o(mechanism_spikes[generated_spatial]),
      .ages_o(mechanism_ages[generated_spatial]),
      .amplitudes_o(mechanism_amplitudes[generated_spatial]),
      .shared_penalty_o(), .membrane_energy_o()
    );
  end endgenerate

  always_ff @(posedge clk) begin
    if (reset) begin
      holding_result_reg <= 1'b0;
      spike_vector_o <= '0;
      completion_tag_o <= '0;
      address_error_o <= 1'b0;
      for (destination = 0; destination < DEST_COUNT; destination = destination+1) begin
        current_reg[destination] <= '0;
        membrane_reg[destination] <= '0;
        age_reg[destination] <= INACTIVE_AGE;
        amplitude_reg[destination] <= '0;
      end
    end else if (holding_result_reg) begin
      if (spike_ready_i) begin
        holding_result_reg <= 1'b0;
        spike_vector_o <= '0;
      end
    end else if (completion_valid_i && completion_ready_o) begin
      completion_tag_o <= completion_tag_i;
      holding_result_reg <= 1'b1;
      for (spatial = 0; spatial < SPATIAL_DEST_COUNT; spatial = spatial+1)
        for (channel = 0; channel < CHANNEL_COUNT; channel = channel+1) begin
          destination = channel*SPATIAL_DEST_COUNT+spatial;
          spike_vector_o[destination] <= mechanism_spikes[spatial][channel];
          membrane_reg[destination] <= mechanism_membranes[spatial][
            channel*MEM_WIDTH +: MEM_WIDTH];
          age_reg[destination] <= mechanism_ages[spatial][
            channel*AGE_WIDTH +: AGE_WIDTH];
          amplitude_reg[destination] <= mechanism_amplitudes[spatial][
            channel*MEM_WIDTH +: MEM_WIDTH];
          current_reg[destination] <= '0;
        end
    end else begin
      for (destination = 0; destination < DEST_COUNT; destination = destination+1) begin
        accumulated = $signed(current_reg[destination]);
        if (dense_current_valid_i)
          accumulated = accumulated + $signed(dense_current_delta_i[
            destination*CURRENT_WIDTH +: CURRENT_WIDTH]);
        for (lane = 0; lane < CONTRIBUTION_LANES; lane = lane+1)
          if (contribution_valid_i[lane]) begin
            if ($unsigned(destination_i[lane*ADDRESS_WIDTH +: ADDRESS_WIDTH]) >=
                DEST_COUNT)
              address_error_o <= 1'b1;
            else if ($unsigned(destination_i[
                     lane*ADDRESS_WIDTH +: ADDRESS_WIDTH]) == destination)
              accumulated = accumulated + $signed(weight_i[
                lane*WEIGHT_WIDTH +: WEIGHT_WIDTH]);
          end
        if (accumulated > MAX_CURRENT) current_reg[destination] <= MAX_CURRENT;
        else if (accumulated < MIN_CURRENT) current_reg[destination] <= MIN_CURRENT;
        else current_reg[destination] <= accumulated[CURRENT_WIDTH-1:0];
      end
    end
  end
endmodule
