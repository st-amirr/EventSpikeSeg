`timescale 1ns/1ps
module triangular_threshold_adaptation #(
  parameter integer VALUE_WIDTH = 16,
  parameter integer AGE_WIDTH = 16,
  parameter integer FRAC_BITS = 10
) (
  input  logic clk,
  input  logic reset,
  input  logic update_valid,
  input  logic [AGE_WIDTH-1:0] elapsed_bins_i,
  input  logic spike_i,
  input  logic [VALUE_WIDTH-1:0] membrane_energy_i,
  input  logic [VALUE_WIDTH-1:0] strength_i,
  input  logic [AGE_WIDTH-1:0] duration_i,
  output logic [VALUE_WIDTH-1:0] penalty_o,
  output logic active_o
);
  localparam [AGE_WIDTH-1:0] INACTIVE = {AGE_WIDTH{1'b1}};
  localparam integer MAX_VALUE = (1 << VALUE_WIDTH) - 1;

  logic [AGE_WIDTH-1:0] age_reg;
  logic [VALUE_WIDTH-1:0] amplitude_reg;
  longint unsigned effective_age;
  longint unsigned phase_numerator;
  longint unsigned penalty_value;
  longint unsigned amplitude_value;

  always_comb begin
    active_o = (age_reg != INACTIVE);
    effective_age = age_reg;
    if (update_valid && active_o)
      effective_age = $unsigned(age_reg) + $unsigned(elapsed_bins_i);

    phase_numerator = 0;
    if (active_o && duration_i != 0) begin
      if (effective_age <= $unsigned(duration_i))
        phase_numerator = effective_age;
      else if (effective_age < (2 * $unsigned(duration_i)))
        phase_numerator = 2 * $unsigned(duration_i) - effective_age;
    end
    if (duration_i == 0)
      penalty_value = 0;
    else
      penalty_value = ($unsigned(amplitude_reg) * phase_numerator) /
                      $unsigned(duration_i);
    if (penalty_value > MAX_VALUE)
      penalty_o = {VALUE_WIDTH{1'b1}};
    else
      penalty_o = penalty_value[VALUE_WIDTH-1:0];
  end

  always_ff @(posedge clk) begin
    if (reset) begin
      age_reg <= INACTIVE;
      amplitude_reg <= '0;
    end else if (update_valid) begin
      if (spike_i) begin
        age_reg <= '0;
        amplitude_value = ($unsigned(membrane_energy_i) * $unsigned(strength_i) +
                           (1 << (FRAC_BITS - 1))) >> FRAC_BITS;
        if (amplitude_value > MAX_VALUE)
          amplitude_reg <= {VALUE_WIDTH{1'b1}};
        else
          amplitude_reg <= amplitude_value[VALUE_WIDTH-1:0];
      end else if (active_o) begin
        if (effective_age >= (2 * $unsigned(duration_i))) begin
          age_reg <= INACTIVE;
          amplitude_reg <= '0;
        end else begin
          age_reg <= effective_age[AGE_WIDTH-1:0];
        end
      end
    end
  end
endmodule
