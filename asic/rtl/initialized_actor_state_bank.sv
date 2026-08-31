`timescale 1ns/1ps
// Direct-indexed actor state split into bounded 1RW SRAM macros. All banks
// scrub to zero in parallel at sequence start; runtime requests retain one
// logical ready/valid port and may not read and write in the same cycle.
module initialized_actor_state_bank #(
  parameter integer DATA_WIDTH = 65,
  parameter integer DEPTH = 256,
  parameter integer ADDRESS_WIDTH = (DEPTH <= 1) ? 1 : $clog2(DEPTH),
  parameter integer MAXIMUM_BANK_DEPTH = 65_536,
  parameter integer BANK_COUNT =
    (DEPTH + MAXIMUM_BANK_DEPTH - 1) / MAXIMUM_BANK_DEPTH,
  parameter integer BANK_ADDRESS_WIDTH =
    (MAXIMUM_BANK_DEPTH <= 1) ? 1 : $clog2(MAXIMUM_BANK_DEPTH),
  parameter integer USE_MACRO = 0
) (
  input logic clk,
  input logic reset,
  output logic initialization_done_o,
  input logic read_valid_i,
  output logic read_ready_o,
  input logic [ADDRESS_WIDTH-1:0] read_address_i,
  output logic read_response_valid_o,
  output logic [DATA_WIDTH-1:0] read_data_o,
  input logic write_valid_i,
  output logic write_ready_o,
  input logic [ADDRESS_WIDTH-1:0] write_address_i,
  input logic [DATA_WIDTH-1:0] write_data_i,
  output logic request_conflict_o
);
  logic [BANK_COUNT-1:0] bank_done;
  logic [BANK_COUNT-1:0] bank_read_enable;
  logic [BANK_COUNT-1:0] bank_read_valid;
  logic [BANK_COUNT-1:0] bank_write_enable;
  logic [BANK_ADDRESS_WIDTH-1:0] bank_scrub_address [0:BANK_COUNT-1];
  logic [BANK_COUNT*DATA_WIDTH-1:0] bank_read_data;
  integer read_bank_index;
  integer write_bank_index;
  integer bank_index;

  initial begin
    if (DEPTH <= 0) $error("initialized state depth must be positive");
    if (MAXIMUM_BANK_DEPTH <= 0)
      $error("maximum SRAM bank depth must be positive");
  end

  assign initialization_done_o = &bank_done;
  assign read_ready_o = initialization_done_o && !write_valid_i;
  assign write_ready_o = initialization_done_o;

  always_comb begin
    read_bank_index = $unsigned(read_address_i) / MAXIMUM_BANK_DEPTH;
    write_bank_index = $unsigned(write_address_i) / MAXIMUM_BANK_DEPTH;
    bank_read_enable = '0;
    bank_write_enable = '0;
    read_response_valid_o = 1'b0;
    read_data_o = '0;
    for (bank_index = 0; bank_index < BANK_COUNT; bank_index = bank_index + 1) begin
      if (!bank_done[bank_index])
        bank_write_enable[bank_index] = 1'b1;
      else if (initialization_done_o && write_valid_i && write_ready_o &&
               write_bank_index == bank_index)
        bank_write_enable[bank_index] = 1'b1;
      if (initialization_done_o && read_valid_i && read_ready_o &&
          read_bank_index == bank_index)
        bank_read_enable[bank_index] = 1'b1;
      if (bank_read_valid[bank_index]) begin
        read_response_valid_o = 1'b1;
        read_data_o = bank_read_data[bank_index*DATA_WIDTH +: DATA_WIDTH];
      end
    end
  end

  genvar generated_bank;
  generate for (generated_bank = 0; generated_bank < BANK_COUNT;
                generated_bank = generated_bank + 1) begin : banks
    localparam integer BANK_BASE = generated_bank * MAXIMUM_BANK_DEPTH;
    localparam integer REMAINING_DEPTH = DEPTH - BANK_BASE;
    localparam integer THIS_DEPTH =
      (REMAINING_DEPTH > MAXIMUM_BANK_DEPTH) ? MAXIMUM_BANK_DEPTH : REMAINING_DEPTH;
    logic [BANK_ADDRESS_WIDTH-1:0] runtime_read_row;
    logic [BANK_ADDRESS_WIDTH-1:0] runtime_write_row;
    logic [BANK_ADDRESS_WIDTH-1:0] selected_write_row;
    logic [DATA_WIDTH-1:0] selected_write_data;

    assign runtime_read_row = $unsigned(read_address_i) % MAXIMUM_BANK_DEPTH;
    assign runtime_write_row = $unsigned(write_address_i) % MAXIMUM_BANK_DEPTH;
    assign selected_write_row = bank_done[generated_bank] ?
                                runtime_write_row :
                                bank_scrub_address[generated_bank];
    assign selected_write_data = bank_done[generated_bank] ? write_data_i : '0;

    actor_local_state_sram #(
      .DATA_WIDTH(DATA_WIDTH), .DEPTH(THIS_DEPTH),
      .ADDRESS_WIDTH(BANK_ADDRESS_WIDTH), .USE_MACRO(USE_MACRO)
    ) state_memory (
      .clk, .read_enable_i(bank_read_enable[generated_bank]),
      .read_address_i(runtime_read_row),
      .read_valid_o(bank_read_valid[generated_bank]),
      .read_data_o(bank_read_data[generated_bank*DATA_WIDTH +: DATA_WIDTH]),
      .write_enable_i(bank_write_enable[generated_bank]),
      .write_address_i(selected_write_row), .write_data_i(selected_write_data)
    );

    always_ff @(posedge clk) begin
      if (reset) begin
        bank_done[generated_bank] <= 1'b0;
        bank_scrub_address[generated_bank] <= '0;
      end else if (!bank_done[generated_bank]) begin
        if ($unsigned(bank_scrub_address[generated_bank]) + 1 >= THIS_DEPTH) begin
          bank_done[generated_bank] <= 1'b1;
          bank_scrub_address[generated_bank] <= '0;
        end else begin
          bank_scrub_address[generated_bank] <=
            bank_scrub_address[generated_bank] + 1'b1;
        end
      end
    end
  end endgenerate

  always_ff @(posedge clk) begin
    if (reset)
      request_conflict_o <= 1'b0;
    else if (initialization_done_o && read_valid_i && write_valid_i)
      request_conflict_o <= 1'b1;
  end
endmodule
