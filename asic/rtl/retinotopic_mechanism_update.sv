`timescale 1ns/1ps
// One retinotopic all-channel threshold/reset/mechanism commit. Triangular
// processes are summed across feature channels before thresholding. Peer
// inhibition subtracts shared RMS membrane energy from non-spiking channels.
module retinotopic_mechanism_update #(
  parameter integer CHANNELS = 4,
  parameter integer MEM_WIDTH = 16,
  parameter integer AGE_WIDTH = 16,
  parameter integer ELAPSED_WIDTH = 24,
  parameter integer FRAC_BITS = 10
) (
  input logic signed [CHANNELS*MEM_WIDTH-1:0] candidates_i,
  input logic signed [CHANNELS*MEM_WIDTH-1:0] base_thresholds_i,
  input logic [CHANNELS-1:0] update_mask_i,
  input logic [CHANNELS*AGE_WIDTH-1:0] ages_i,
  input logic [CHANNELS*MEM_WIDTH-1:0] amplitudes_i,
  input logic [CHANNELS*ELAPSED_WIDTH-1:0] elapsed_bins_i,
  input logic inhibition_enabled_i,
  input logic adaptation_enabled_i,
  input logic [MEM_WIDTH-1:0] inhibition_strength_i,
  input logic [MEM_WIDTH-1:0] adaptation_strength_i,
  input logic [AGE_WIDTH-1:0] adaptation_duration_i,
  output logic signed [CHANNELS*MEM_WIDTH-1:0] membranes_o,
  output logic [CHANNELS-1:0] spikes_o,
  output logic [CHANNELS*AGE_WIDTH-1:0] ages_o,
  output logic [CHANNELS*MEM_WIDTH-1:0] amplitudes_o,
  output logic [MEM_WIDTH-1:0] shared_penalty_o,
  output logic [MEM_WIDTH-1:0] membrane_energy_o
);
  localparam integer MAX_MEM = (1 << (MEM_WIDTH - 1)) - 1;
  localparam integer MIN_MEM = -(1 << (MEM_WIDTH - 1));
  localparam integer MAX_VALUE = (1 << MEM_WIDTH) - 1;
  localparam [AGE_WIDTH-1:0] INACTIVE = {AGE_WIDTH{1'b1}};
  integer channel;
  integer signed candidate;
  integer signed threshold;
  integer signed membrane;
  integer signed adjusted;
  integer signed inhibited;
  longint unsigned effective_age_value;
  longint unsigned phase;
  longint unsigned penalty;
  longint unsigned penalty_sum;
  longint unsigned square_sum;
  longint unsigned mean_square;
  longint unsigned rms;
  longint unsigned magnitude;
  longint unsigned trial;
  longint unsigned decrement;
  longint unsigned amplitude_value;
  integer root_bit;
  logic any_spike;

  // Use an explicit combinational process instead of always_comb here. Icarus
  // 11 incorrectly adds this block's temporary variables to its any-edge
  // sensitivity set and can enter a zero-time assertion loop.
  always @* begin
    candidate = 0;
    threshold = 0;
    membrane = 0;
    adjusted = 0;
    inhibited = 0;
    effective_age_value = 0;
    phase = 0;
    penalty = 0;
    penalty_sum = 0;
    square_sum = 0;
    mean_square = 0;
    rms = 0;
    magnitude = 0;
    trial = 0;
    decrement = 0;
    amplitude_value = 0;
    any_spike = 1'b0;
    for (channel = 0; channel < CHANNELS; channel = channel + 1) begin
      effective_age_value = $unsigned(ages_i[channel*AGE_WIDTH +: AGE_WIDTH]);
      if (ages_i[channel*AGE_WIDTH +: AGE_WIDTH] != INACTIVE && update_mask_i[channel])
        effective_age_value = effective_age_value +
          ($unsigned(elapsed_bins_i[channel*ELAPSED_WIDTH +: ELAPSED_WIDTH]) <<
           FRAC_BITS);
      phase = 0;
      if (adaptation_enabled_i &&
          ages_i[channel*AGE_WIDTH +: AGE_WIDTH] != INACTIVE &&
          adaptation_duration_i != 0) begin
        if (effective_age_value <= $unsigned(adaptation_duration_i))
          phase = effective_age_value;
        else if (effective_age_value < 2*$unsigned(adaptation_duration_i))
          phase = 2*$unsigned(adaptation_duration_i) - effective_age_value;
      end
      penalty = (adaptation_duration_i == 0) ? 0 :
        ($unsigned(amplitudes_i[channel*MEM_WIDTH +: MEM_WIDTH]) * phase) /
        $unsigned(adaptation_duration_i);
      penalty_sum = penalty_sum + penalty;
    end
    if (penalty_sum > MAX_VALUE) shared_penalty_o = {MEM_WIDTH{1'b1}};
    else shared_penalty_o = penalty_sum[MEM_WIDTH-1:0];

    square_sum = 0;
    for (channel = 0; channel < CHANNELS; channel = channel + 1) begin
      candidate = $signed(candidates_i[channel*MEM_WIDTH +: MEM_WIDTH]);
      adjusted = candidate - $signed({1'b0, shared_penalty_o[MEM_WIDTH-2:0]});
      magnitude = (adjusted < 0) ? -adjusted : adjusted;
      square_sum = square_sum + magnitude*magnitude;
    end
    mean_square = square_sum / CHANNELS;
    rms = 0;
    for (root_bit = MEM_WIDTH-1; root_bit >= 0; root_bit = root_bit-1) begin
      trial = rms | (1 << root_bit);
      if (trial*trial <= mean_square) rms = trial;
    end
    if (rms > MAX_VALUE) membrane_energy_o = {MEM_WIDTH{1'b1}};
    else membrane_energy_o = rms[MEM_WIDTH-1:0];

    membranes_o = candidates_i;
    spikes_o = '0;
    ages_o = ages_i;
    amplitudes_o = amplitudes_i;
    for (channel = 0; channel < CHANNELS; channel = channel + 1) begin
      candidate = $signed(candidates_i[channel*MEM_WIDTH +: MEM_WIDTH]);
      threshold = $signed(base_thresholds_i[channel*MEM_WIDTH +: MEM_WIDTH]) +
                  $signed({1'b0, shared_penalty_o[MEM_WIDTH-2:0]});
      if (threshold > MAX_MEM) threshold = MAX_MEM;
      if (update_mask_i[channel] && candidate >= threshold) begin
        spikes_o[channel] = 1'b1;
        membrane = candidate - threshold;
      end else membrane = candidate;
      if (membrane > MAX_MEM) membrane = MAX_MEM;
      if (membrane < MIN_MEM) membrane = MIN_MEM;
      membranes_o[channel*MEM_WIDTH +: MEM_WIDTH] = membrane[MEM_WIDTH-1:0];

      if (adaptation_enabled_i && update_mask_i[channel]) begin
        effective_age_value = $unsigned(ages_i[channel*AGE_WIDTH +: AGE_WIDTH]) +
          ($unsigned(elapsed_bins_i[channel*ELAPSED_WIDTH +: ELAPSED_WIDTH]) <<
           FRAC_BITS);
        if (spikes_o[channel]) begin
          ages_o[channel*AGE_WIDTH +: AGE_WIDTH] = '0;
          amplitude_value =
            ($unsigned(membrane_energy_o)*$unsigned(adaptation_strength_i) +
             (1 << (FRAC_BITS-1))) >> FRAC_BITS;
          if (amplitude_value > MAX_VALUE)
            amplitudes_o[channel*MEM_WIDTH +: MEM_WIDTH] = {MEM_WIDTH{1'b1}};
          else amplitudes_o[channel*MEM_WIDTH +: MEM_WIDTH] =
            amplitude_value[MEM_WIDTH-1:0];
        end else if (ages_i[channel*AGE_WIDTH +: AGE_WIDTH] != INACTIVE) begin
          if (effective_age_value >= 2*$unsigned(adaptation_duration_i)) begin
            ages_o[channel*AGE_WIDTH +: AGE_WIDTH] = INACTIVE;
            amplitudes_o[channel*MEM_WIDTH +: MEM_WIDTH] = '0;
          end else ages_o[channel*AGE_WIDTH +: AGE_WIDTH] =
            effective_age_value[AGE_WIDTH-1:0];
        end
      end
    end

    any_spike = |spikes_o;
    decrement =
      ($unsigned(membrane_energy_o)*$unsigned(inhibition_strength_i) +
       (1 << (FRAC_BITS-1))) >> FRAC_BITS;
    if (inhibition_enabled_i && any_spike) begin
      for (channel = 0; channel < CHANNELS; channel = channel + 1) begin
        if (!spikes_o[channel]) begin
          membrane = $signed(membranes_o[channel*MEM_WIDTH +: MEM_WIDTH]);
          inhibited = membrane - decrement;
          if (inhibited > MAX_MEM) inhibited = MAX_MEM;
          if (inhibited < MIN_MEM) inhibited = MIN_MEM;
          membranes_o[channel*MEM_WIDTH +: MEM_WIDTH] = inhibited[MEM_WIDTH-1:0];
        end
      end
    end
  end
endmodule
