`timescale 1ns/1ps
// Exact combinational building blocks for retinotopic threshold adaptation.
// A CHANNELS-wide update is composed as follows:
//   CHANNELS penalty lanes -> one penalty reducer -> CHANNELS square lanes
//   -> one energy reducer -> CHANNELS commit lanes.
// The shared penalty and RMS energy therefore remain cross-channel values; the
// decomposition changes only the physical characterization boundary.

module retinotopic_adaptation_penalty_lane #(
  parameter integer MEM_WIDTH = 24,
  parameter integer AGE_WIDTH = 6,
  parameter integer AMPLITUDE_WIDTH = 19,
  parameter integer DURATION_WIDTH = 21,
  parameter integer ELAPSED_WIDTH = 24,
  parameter integer FRAC_BITS = 16,
  parameter integer AGE_FRAC_BITS = 0
) (
  input logic update_i,
  input logic [AGE_WIDTH-1:0] age_i,
  input logic [AMPLITUDE_WIDTH-1:0] amplitude_i,
  input logic [ELAPSED_WIDTH-1:0] elapsed_bins_i,
  input logic [DURATION_WIDTH-1:0] adaptation_duration_i,
  output logic [MEM_WIDTH-1:0] penalty_o
);
  localparam [AGE_WIDTH-1:0] INACTIVE = {AGE_WIDTH{1'b1}};
  localparam longint unsigned MAX_VALUE = (64'd1 << MEM_WIDTH) - 1;
  longint unsigned effective_age_value;
  longint unsigned effective_age_q;
  longint unsigned phase;
  longint unsigned penalty;

  always @* begin
    effective_age_value = $unsigned(age_i);
    if (age_i != INACTIVE && update_i)
      effective_age_value = effective_age_value +
        ($unsigned(elapsed_bins_i) << AGE_FRAC_BITS);
    effective_age_q = effective_age_value << (FRAC_BITS-AGE_FRAC_BITS);
    phase = 0;
    if (age_i != INACTIVE && adaptation_duration_i != 0) begin
      if (effective_age_q <= $unsigned(adaptation_duration_i))
        phase = effective_age_q;
      else if (effective_age_q < 2*$unsigned(adaptation_duration_i))
        phase = 2*$unsigned(adaptation_duration_i) - effective_age_q;
    end
    penalty = (adaptation_duration_i == 0) ? 0 :
      ($unsigned(amplitude_i) * phase) / $unsigned(adaptation_duration_i);
    if (penalty > MAX_VALUE) penalty_o = {MEM_WIDTH{1'b1}};
    else penalty_o = penalty[MEM_WIDTH-1:0];
  end
endmodule

module retinotopic_adaptation_penalty_reduce #(
  parameter integer CHANNELS = 64,
  parameter integer MEM_WIDTH = 24
) (
  input logic [CHANNELS*MEM_WIDTH-1:0] penalties_i,
  output logic [MEM_WIDTH-1:0] shared_penalty_o
);
  localparam longint unsigned MAX_VALUE = (64'd1 << MEM_WIDTH) - 1;
  integer channel;
  longint unsigned penalty_sum;

  always @* begin
    penalty_sum = 0;
    for (channel = 0; channel < CHANNELS; channel = channel + 1)
      penalty_sum = penalty_sum +
        $unsigned(penalties_i[channel*MEM_WIDTH +: MEM_WIDTH]);
    if (penalty_sum > MAX_VALUE) shared_penalty_o = {MEM_WIDTH{1'b1}};
    else shared_penalty_o = penalty_sum[MEM_WIDTH-1:0];
  end
endmodule

module retinotopic_adaptation_square_lane #(
  parameter integer MEM_WIDTH = 24,
  parameter integer SQUARE_WIDTH = 2*MEM_WIDTH
) (
  input logic signed [MEM_WIDTH-1:0] candidate_i,
  input logic [MEM_WIDTH-1:0] shared_penalty_i,
  output logic [SQUARE_WIDTH-1:0] square_o
);
  integer signed adjusted;
  longint unsigned magnitude;
  longint unsigned square;

  always @* begin
    adjusted = $signed(candidate_i) -
      $signed({1'b0, shared_penalty_i[MEM_WIDTH-2:0]});
    magnitude = (adjusted < 0) ? -adjusted : adjusted;
    square = magnitude*magnitude;
    square_o = square[SQUARE_WIDTH-1:0];
  end
endmodule

module retinotopic_adaptation_energy_reduce #(
  parameter integer CHANNELS = 64,
  parameter integer MEM_WIDTH = 24,
  parameter integer SQUARE_WIDTH = 2*MEM_WIDTH
) (
  input logic [CHANNELS*SQUARE_WIDTH-1:0] squares_i,
  output logic [MEM_WIDTH-1:0] membrane_energy_o
);
  localparam longint unsigned MAX_VALUE = (64'd1 << MEM_WIDTH) - 1;
  integer channel;
  integer root_bit;
  longint unsigned square_sum;
  longint unsigned mean_square;
  longint unsigned rms;
  longint unsigned trial;

  always @* begin
    square_sum = 0;
    for (channel = 0; channel < CHANNELS; channel = channel + 1)
      square_sum = square_sum +
        $unsigned(squares_i[channel*SQUARE_WIDTH +: SQUARE_WIDTH]);
    mean_square = square_sum / CHANNELS;
    rms = 0;
    for (root_bit = MEM_WIDTH-1; root_bit >= 0; root_bit = root_bit-1) begin
      trial = rms | (64'd1 << root_bit);
      if (trial*trial <= mean_square) rms = trial;
    end
    if (rms > MAX_VALUE) membrane_energy_o = {MEM_WIDTH{1'b1}};
    else membrane_energy_o = rms[MEM_WIDTH-1:0];
  end
endmodule

module retinotopic_adaptation_commit_lane #(
  parameter integer MEM_WIDTH = 24,
  parameter integer AGE_WIDTH = 6,
  parameter integer AMPLITUDE_WIDTH = 19,
  parameter integer DURATION_WIDTH = 21,
  parameter integer ELAPSED_WIDTH = 24,
  parameter integer FRAC_BITS = 16,
  parameter integer AGE_FRAC_BITS = 0
) (
  input logic signed [MEM_WIDTH-1:0] candidate_i,
  input logic signed [MEM_WIDTH-1:0] base_threshold_i,
  input logic update_i,
  input logic [AGE_WIDTH-1:0] age_i,
  input logic [AMPLITUDE_WIDTH-1:0] amplitude_i,
  input logic [ELAPSED_WIDTH-1:0] elapsed_bins_i,
  input logic [MEM_WIDTH-1:0] shared_penalty_i,
  input logic [MEM_WIDTH-1:0] membrane_energy_i,
  input logic [AMPLITUDE_WIDTH-1:0] adaptation_strength_i,
  input logic [DURATION_WIDTH-1:0] adaptation_duration_i,
  output logic signed [MEM_WIDTH-1:0] membrane_o,
  output logic spike_o,
  output logic [AGE_WIDTH-1:0] age_o,
  output logic [AMPLITUDE_WIDTH-1:0] amplitude_o
);
  localparam integer MAX_MEM = (1 << (MEM_WIDTH - 1)) - 1;
  localparam integer MIN_MEM = -(1 << (MEM_WIDTH - 1));
  localparam integer MAX_AMPLITUDE = (1 << AMPLITUDE_WIDTH) - 1;
  localparam [AGE_WIDTH-1:0] INACTIVE = {AGE_WIDTH{1'b1}};
  integer signed candidate;
  integer signed threshold;
  integer signed membrane;
  longint unsigned effective_age_value;
  longint unsigned effective_age_q;
  longint unsigned amplitude_value;

  always @* begin
    candidate = $signed(candidate_i);
    threshold = $signed(base_threshold_i) +
      $signed({1'b0, shared_penalty_i[MEM_WIDTH-2:0]});
    if (threshold > MAX_MEM) threshold = MAX_MEM;
    spike_o = update_i && candidate >= threshold;
    if (spike_o) membrane = candidate - threshold;
    else membrane = candidate;
    if (membrane > MAX_MEM) membrane = MAX_MEM;
    if (membrane < MIN_MEM) membrane = MIN_MEM;
    membrane_o = membrane[MEM_WIDTH-1:0];

    age_o = age_i;
    amplitude_o = amplitude_i;
    effective_age_value = $unsigned(age_i) +
      ($unsigned(elapsed_bins_i) << AGE_FRAC_BITS);
    effective_age_q = effective_age_value << (FRAC_BITS-AGE_FRAC_BITS);
    amplitude_value = 0;
    if (update_i) begin
      if (spike_o) begin
        age_o = '0;
        amplitude_value =
          ($unsigned(membrane_energy_i)*$unsigned(adaptation_strength_i) +
           (64'd1 << (FRAC_BITS-1))) >> FRAC_BITS;
        if (amplitude_value > MAX_AMPLITUDE)
          amplitude_o = {AMPLITUDE_WIDTH{1'b1}};
        else amplitude_o = amplitude_value[AMPLITUDE_WIDTH-1:0];
      end else if (age_i != INACTIVE) begin
        if (effective_age_q >= 2*$unsigned(adaptation_duration_i)) begin
          age_o = INACTIVE;
          amplitude_o = '0;
        end else age_o = effective_age_value[AGE_WIDTH-1:0];
      end
    end
  end
endmodule
