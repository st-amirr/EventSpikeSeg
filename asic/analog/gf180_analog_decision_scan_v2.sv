`timescale 1ns/1ps
// Categorical address/result control only; no numerical state or ADC.
// Start ONLY after accumulation and required population RMS/threshold phases.
// Service owns restore/evaluate/reset/writeback and must hold its sampled SPIKE
// stable through result_valid/result_ready. Its done requires a fresh low/high.
// Bank0=local64, bank1..2=local two-bank service, bank3..18=local1024 page;
// LOCAL_BANKS gives physical local-slot order; forest rank excludes exactly
// those banks. Low-resolution actors have a real gap at bank9.
module gf180_analog_decision_scan_v2 #(
  parameter integer CHANNELS=8, HEIGHT=440, WIDTH=640,
  parameter [379:0] LOCAL_BANKS=380'h0001200011000100000f0000e0000d0000c0000b0000a00009000080000700006000050000400003000020000100000,
  parameter integer BANKS_X=(WIDTH+7)/8, BANKS_Y=(HEIGHT+7)/8
) (
  input wire clk, reset,
  input wire start_i,
  output wire start_ready_o,
  input wire [23:0] bin_tag_i,
  output wire service_valid_o,
  input wire service_ready_i,
  input wire service_done_i,
  output wire [6:0] channel_o,
  output wire [8:0] y_o,
  output wire [9:0] x_o,
  output wire [19:0] linear_bank_o,
  output wire [1:0] service_kind_o,
  output wire [21:0] forest_address_o,
  output wire [21:0] auxiliary_forest_address_o,
  output wire [6:0] local_page_address_o,
  output wire local_bank_select_o,
  output wire [2:0] local_row_o,
  output wire [7:0] column_select_o,
  output wire result_valid_o,
  input wire result_ready_i,
  output wire [25:0] result_address_o,
  output wire [23:0] result_bin_tag_o,
  output wire result_last_o,
  output wire result_hold_o,
  output wire busy_o,
  output wire done_o,
  input wire done_ready_i
);
  localparam [2:0] IDLE=0, REQUEST=1, WAIT_SERVICE=2, PUBLISH=3,
                   WAIT_COMPLETION=4, DONE=5;
  reg [2:0] state;
  reg [6:0] channel;
  reg [8:0] y;
  reg [9:0] x;
  reg [23:0] tag;
  reg ack_armed;
  wire last=(channel==CHANNELS-1 && y==HEIGHT-1 && x==WIDTH-1);
  wire [31:0] bank=(channel*BANKS_Y+(y>>3))*BANKS_X+(x>>3);
  integer local_index, excluded_before, hole;
  reg [19:0] excluded_bank;
  always @* begin
    local_index=-1;excluded_before=0;excluded_bank=0;
    for(hole=0;hole<19;hole=hole+1) begin
      excluded_bank=LOCAL_BANKS[hole*20 +: 20];
      if(bank==excluded_bank) local_index=hole;
      if(bank>=excluded_bank) excluded_before=excluded_before+1;
    end
  end
  wire [31:0] rank=bank-excluded_before;
  assign start_ready_o=(state==IDLE);
  assign service_valid_o=(state==REQUEST);
  assign busy_o=(state!=IDLE && state!=DONE);
  assign done_o=(state==DONE);
  assign channel_o=channel;
  assign y_o=y;
  assign x_o=x;
  assign linear_bank_o=bank[19:0];
  assign service_kind_o=(local_index==0) ? 2'd0 : (local_index>0 && local_index<3) ? 2'd1 : (local_index>=3) ? 2'd2 : 2'd3;
  assign forest_address_o=(local_index<0) ? {rank[18:0],y[2:0]} : 22'b0;
  // AGE/AMP planes have no local resident-identity exceptions in the map.
  assign auxiliary_forest_address_o={bank[18:0],y[2:0]};
  assign local_page_address_o=(local_index>=3) ? ((local_index-3)*8+y[2:0]) : 7'b0;
  assign local_bank_select_o=(local_index==2);
  assign local_row_o=y[2:0];
  assign column_select_o=8'b1<<x[2:0];
  assign result_valid_o=(state==PUBLISH);
  assign result_address_o={channel,y,x};
  assign result_bin_tag_o=tag;
  assign result_last_o=last;
  assign result_hold_o=(state==PUBLISH);
  always @(posedge clk) begin
    if (reset) begin
      state<=IDLE;channel<=0;y<=0;x<=0;tag<=0;ack_armed<=0;
    end else case(state)
      IDLE: if(start_i) begin
        channel<=0;y<=0;x<=0;tag<=bin_tag_i;ack_armed<=0;state<=REQUEST;
      end
      REQUEST: if(service_ready_i) begin
        ack_armed<=!service_done_i;state<=WAIT_SERVICE;
      end
      WAIT_SERVICE: begin
        if(!service_done_i) ack_armed<=1;
        if(service_done_i && ack_armed) begin ack_armed<=0;state<=PUBLISH;end
      end
      PUBLISH: if(result_ready_i) begin
        if(last) state<=WAIT_COMPLETION;
        else begin
          if(x==WIDTH-1) begin
            x<=0;
            if(y==HEIGHT-1) begin y<=0;channel<=channel+1'b1;end
            else y<=y+1'b1;
          end else x<=x+1'b1;
          state<=REQUEST;
        end
      end
      // The existing scalar packet adapter deasserts ready while the last spike
      // and then completion are pending. Do not start a new bin until drained.
      WAIT_COMPLETION: if(result_ready_i) state<=DONE;
      DONE: if(done_ready_i) state<=IDLE;
      default: state<=IDLE;
    endcase
  end
  initial begin
    if(CHANNELS<1 || CHANNELS>128 || HEIGHT<1 || HEIGHT>512 || WIDTH<1 || WIDTH>1024)
      $error("Canonical channel/y/x fields cannot represent this population");
    if(CHANNELS*BANKS_X*BANKS_Y > (1<<19))
      $error("Forest row/bank selector width exceeded");
  end
endmodule
