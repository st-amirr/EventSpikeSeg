`timescale 1ns/1ps
module peer_membrane_inhibition #(
  parameter integer CHANNELS = 4,
  parameter integer MEM_WIDTH = 16,
  parameter integer STRENGTH_WIDTH = 16,
  parameter integer FRAC_BITS = 10
) (
  input  logic signed [CHANNELS*MEM_WIDTH-1:0] adjusted_candidates_i,
  input  logic [CHANNELS-1:0] spikes_i,
  input  logic [STRENGTH_WIDTH-1:0] strength_i,
  output logic signed [CHANNELS*MEM_WIDTH-1:0] inhibited_membranes_o
);
  localparam integer MAX_MEM = (1 << (MEM_WIDTH - 1)) - 1;
  localparam integer MIN_MEM = -(1 << (MEM_WIDTH - 1));
  integer channel;
  integer signed candidate;
  integer signed inhibited;
  longint unsigned square_sum;
  longint unsigned mean_square;
  longint unsigned rms;
  longint unsigned decrement;
  longint unsigned root_trial;
  longint unsigned magnitude;
  integer root_bit;

  always_comb begin
    square_sum = 0;
    for (channel = 0; channel < CHANNELS; channel = channel + 1) begin
      candidate = $signed(adjusted_candidates_i[channel*MEM_WIDTH +: MEM_WIDTH]);
      magnitude = (candidate < 0) ? -candidate : candidate;
      square_sum = square_sum + magnitude * magnitude;
    end
    mean_square = square_sum / CHANNELS;
    rms = 0;
    for (root_bit = MEM_WIDTH - 1; root_bit >= 0; root_bit = root_bit - 1) begin
      root_trial = rms | (1 << root_bit);
      if (root_trial * root_trial <= mean_square)
        rms = root_trial;
    end
    decrement = (rms * $unsigned(strength_i) + (1 << (FRAC_BITS - 1))) >> FRAC_BITS;

    inhibited_membranes_o = adjusted_candidates_i;
    if (|spikes_i) begin
      for (channel = 0; channel < CHANNELS; channel = channel + 1) begin
        if (!spikes_i[channel]) begin
          candidate = $signed(adjusted_candidates_i[channel*MEM_WIDTH +: MEM_WIDTH]);
          inhibited = candidate - decrement;
          if (inhibited > MAX_MEM) inhibited = MAX_MEM;
          if (inhibited < MIN_MEM) inhibited = MIN_MEM;
          inhibited_membranes_o[channel*MEM_WIDTH +: MEM_WIDTH] =
            inhibited[MEM_WIDTH-1:0];
        end
      end
    end
  end
endmodule
